#!/bin/bash
# Submits our Flan-T5 large based approach for task A

TEST_FP="../datasets/medqa_d2n/task_prefix/medqa_d2n_test2.json"  # Provided to the script by the submission system

OUTPUT_DIR="./output"
# /root/distill-d2n/ckpts/task_prefix/flan-t5-large_dstl_xl/checkpoint-250/pytorch_model.bin
CKPT_DIR="../ckpts/adapter/flan-t5-small_distill_adpt/checkpoint-2/"
# /root/distill-d2n/ckpts/adapter/flan-t5-small_distill_adpt/checkpoint-2/pytorch_model.bin

# Notes:
# - The model will be downloaded from the HuggingFace model hub
# - The script expects a summary column in the test file, but we don't have one, so use the dialogue column
# - Set the batch size to one to avoid OOM errors
# - Turn off mixed precision to avoid errors on CPUs and some GPUs
# - Set evaluation_strategy="'no'" and load_best_model_at_end=false to avoid evaluation
# - Set bertscore_model_type=null and bleurt_checkpoint=null to avoid loading them
# - Use the run=1 argument to ensure that the output file is named correctly
# 
python3 ./run_summarization.py "./conf/base.yml" "./conf/taskA.yml" output_dir="$OUTPUT_DIR" \
    model_name_or_path="google/flan-t5-large" \
    summary_column="dialogue" \
    checkpoint_dir="$CKPT_DIR" \
    train_file=null \
    validation_file=null \
    test_file="$TEST_FP" \
    per_device_eval_batch_size=1 \
    fp16=false \
    bf16=false \
    do_train=false \
    do_eval=false \
    do_predict=true \
    evaluation_strategy="'no'" \
    load_best_model_at_end=false \
    bertscore_model_type=null \
    bleurt_checkpoint=null \
    model_type=adapter \
    
    
   