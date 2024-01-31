conda create --name distill python=3.9 -y

conda activate distill
pip install torch==1.12.0+cu116 torchvision==0.13.0+cu116 torchaudio==0.12.0 --extra-index-url https://download.pytorch.org/whl/cu116

pip install git+https://github.com/huggingface/transformers@v4.24.0 datasets sentencepiece protobuf==3.20.* wandb accelerate==0.22.0 deepspeed==0.10.1

wandb login 7386dd9169b97829ec6b24f3587dbaf4967ca91e



export LD_LIBRARY_PATH=/home/$USER/.conda/envs/$ENVNAME/lib:/usr/local/cuda-11.6/lib64



conda create --name distill python=3.10 -y
pip install transformers datasets sentencepiece protobuf wandb accelerate deepspeed
