import argparse
from datasets import DatasetDict, concatenate_datasets
from transformers import AutoTokenizer
from data_utils import MEDQADatasetLoader
from metrics import compute_text_acc, compute_equation_acc, compute_metrics_text, compute_metrics_equation, compute_metrics_text_aux, compute_metrics_equation_aux
from train_utils import train_and_evaluate
 
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(subject, message, to_email):
    from_email = 'rosaliu.567@gmail.com'
    password = 'jdrb ueoq ixik tuoa'
    # jdrb ueoq ixik tuoa

    
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    
    body = MIMEText(message, 'plain')
    msg.attach(body)
    
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(from_email, password)
    text = msg.as_string()
    server.sendmail(from_email, to_email, text)
    server.quit()


def run(args):
    #### Prepare datasets
    
    dataset_loader = MEDQADatasetLoader(args.dataset, args.model_type)

    # 加载数据
    datasets = dataset_loader.load_from_json_rationale()
    
    
    # 整理数据集的label和rationale
    train_llm_rationales, train_llm_labels = dataset_loader.load_rationale_data(split='train')
    test_llm_rationales, test_llm_labels = dataset_loader.load_rationale_data(split='test' )
    valid_llm_rationales, valid_llm_labels = dataset_loader.load_rationale_data(split='valid')

    

    # if args.llm is not None: # 给数据集添加labels,
    datasets['train'] = datasets['train'].add_column('llm_label', train_llm_labels)
    datasets['test'] = datasets['test'].add_column('llm_label', test_llm_labels)
    datasets['train'] = datasets['train'].add_column('llm_rationale', train_llm_rationales)
    datasets['test'] = datasets['test'].add_column('llm_rationale', test_llm_rationales)
    
    datasets['valid'] = datasets['valid'].add_column('llm_label', valid_llm_labels)
    datasets['valid'] = datasets['valid'].add_column('llm_rationale', valid_llm_rationales)
    # breakpoint()

    # 选择不同的计算评估的方式，如果有teacher模型的预测标签，目前数据里没有，gt: Use GT label for training  llm: Use LLM predicted label for training
    # if args.label_type == 'gt': 
    #     pass
    # else:
    #     raise ValueError

    if args.llm is not None: # 重命名rationale
        if 'rationale' in datasets['train'].column_names:
            datasets = datasets.remove_columns('rationale')
        datasets = datasets.rename_column('llm_rationale', 'rationale')
        if 'output' in datasets['train'].column_names:
            datasets = datasets.rename_column('output', 'label')
        # breakpoint()
        

    #### Prepare datasets Prepare data for training
    tokenizer = AutoTokenizer.from_pretrained(args.from_pretrained)

    
    def tokenize_function(examples):
        '''
        tokenizer.decode(model_inputs["input_ids"][0], skip_special_tokens=True) : (input from train set)
        'predict: Doctor: What brings you back into the clinic today, miss? 
        Patient: I came in for a refill of my blood pressure medicine. 
        Doctor: It looks like Doctor Kumar followed up with you last time regarding your hypertension, osteoarthritis, osteoporosis, hypothyroidism, allergic rhinitis and kidney stones. Have you noticed any changes or do you have any concerns regarding these issues? Patient: No. Doctor: Have you had any fever or chills, cough, congestion, nausea, vomiting, chest pain, chest pressure? Patient: No. Doctor: Great. Also, for our records, how old are you and what race do you identify yourself as? Patient: I am seventy six years old and identify as a white female.'
        len(model_inputs["input_ids"]) = 1000

        '''
        
        model_inputs = tokenizer(['predict: ' + text for text in examples['input_1']], max_length=args.max_input_length, truncation=True)
        # breakpoint()
        expl_model_inputs = tokenizer(['explain: ' +  text for text in examples['input_2']], max_length=args.max_input_length, truncation=True)
        model_inputs['expl_input_ids'] = expl_model_inputs['input_ids']
        model_inputs['expl_attention_mask'] = expl_model_inputs['attention_mask']
        # breakpoint()

        with tokenizer.as_target_tokenizer():
            label_output_encodings = tokenizer(examples['label'], max_length=1024, truncation=True)
            rationale_output_encodings = tokenizer(examples['rationale'], max_length=1024, truncation=True)

        model_inputs['labels'] = label_output_encodings['input_ids']
        model_inputs['aux_labels'] = rationale_output_encodings['input_ids']

        # breakpoint()
        return model_inputs


    # 不懂这是啥意思，目前猜测，是因为tokenize_function里，已经把这些都tokenize了，所以就不再保留原来的text了，只把tokenizer 传进去
    # breakpoint()
    
    
    tokenized_datasets = datasets.map(
        tokenize_function,
        remove_columns=['input_1','input_2','rationale', 'label', 'llm_label'],
        batched=True
    )
    # breakpoint()
    compute_metrics = compute_metrics_equation(tokenizer)


    train_and_evaluate(args, args.run, tokenizer, tokenized_datasets, compute_metrics)


if __name__ == '__main__':
    # to_email = "rosaliu.567@gmail.com"
    # send_email('模型训练开始', '您的模型已经开始训练。', to_email)
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', type=str, required=True)
    parser.add_argument('--subsample', type=float, default=1.0)
    parser.add_argument('--alpha', type=float, default=0.5)
    parser.add_argument('--max_steps', type=int, default=100)
    parser.add_argument('--eval_steps', type=int, default=250)
    parser.add_argument('--batch_size', type=int, default=64)
    parser.add_argument('--optimizer_name', type=str, default='AdamW')
    parser.add_argument('--lr', type=float, default=5e-5)
    parser.add_argument('--run', type=int, default=0)
    parser.add_argument('--from_pretrained', type=str, default='google/t5-v1_1-base')
    parser.add_argument('--label_type', type=str, default='gt')
    parser.add_argument('--llm', type=str, default='palm')
    parser.add_argument('--max_input_length', type=int, default=1024)
    parser.add_argument('--grad_steps', type=int, default=1)
    parser.add_argument('--local_rank', type=int, default=-1)
    parser.add_argument('--gen_max_len', type=int, default=64)
    parser.add_argument('--parallelize', action='store_true')
    parser.add_argument('--model_type', type=str, default='task_prefix')
    parser.add_argument('--bf16', action='store_true')
    parser.add_argument('--no_log', action='store_true')
    parser.add_argument('--output_rationale', action='store_true')
    parser.add_argument('--addi_info', type=str, default="")
    parser.add_argument("--deepspeed", type=str, default=None, help="Path to deepspeed config file.")
    parser.add_argument('--weight', type=int, default=1)

    args = parser.parse_args()
    run(args)
    # try:  
    #     run(args)
    #     # to_email = "rosaliu.567@gmail.com"
    #     send_email('模型训练完成', '您的模型已经成功训练完成。', to_email)
    # except Exception as e:
    #     print(e)
    #     # to_email = "rosaliu.567@gmail.com"
    #     send_email('模型训练出错', f'您的模型训练时遇到问题: {e}', to_email)  
       