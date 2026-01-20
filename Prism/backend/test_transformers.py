import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

model_id = "meta-llama/Llama-3.2-3B-Instruct"
token = os.getenv("HF_TOKEN")

if not token:
    print("WARNING: HF_TOKEN not found. This test might fail for gated models.")

print(f"Loading {model_id}...")
try:
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16
    )
    
    tokenizer = AutoTokenizer.from_pretrained(model_id, token=token)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        quantization_config=bnb_config,
        device_map="auto",
        token=token
    )
    print("Model loaded successfully!")
    
    inputs = tokenizer("Hello, world!", return_tensors="pt").to(model.device)
    outputs = model.generate(**inputs, max_new_tokens=20)
    print("Generation:", tokenizer.decode(outputs[0]))
    
except Exception as e:
    print(f"Failed to load model: {e}")
