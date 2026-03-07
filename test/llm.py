import re

import numpy as np
import onnxruntime as ort
from huggingface_hub import hf_hub_download
from transformers import AutoTokenizer

# Download model (Q4 recommended)
model_id = "LiquidAI/LFM2.5-1.2B-Thinking-ONNX"
model_path = hf_hub_download(model_id, "onnx/model_q4.onnx")
data_path = hf_hub_download(model_id, "onnx/model_q4.onnx_data")

# Load model and tokenizer
session = ort.InferenceSession(model_path)
tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)

# Prepare chat input
messages = [{"role": "user", "content": "What is 25 * 37?"}]
prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
input_ids = np.array([tokenizer.encode(prompt, add_special_tokens=False)], dtype=np.int64)

# Initialize KV cache
ONNX_DTYPE = {"tensor(float)": np.float32, "tensor(float16)": np.float16, "tensor(int64)": np.int64}
cache = {}
for inp in session.get_inputs():
    if inp.name in {"input_ids", "attention_mask", "position_ids"}:
        continue
    shape = [d if isinstance(d, int) else 1 for d in inp.shape]
    for i, d in enumerate(inp.shape):
        if isinstance(d, str) and "sequence" in d.lower():
            shape[i] = 0
    cache[inp.name] = np.zeros(shape, dtype=ONNX_DTYPE.get(inp.type, np.float32))

# Check if model uses position_ids
input_names = {inp.name for inp in session.get_inputs()}
use_position_ids = "position_ids" in input_names

# Generate tokens
seq_len = input_ids.shape[1]
generated_tokens = []

for step in range(512):  # max tokens (reasoning may need more tokens)
    if step == 0:
        ids = input_ids
        pos = np.arange(seq_len, dtype=np.int64).reshape(1, -1)
    else:
        ids = np.array([[generated_tokens[-1]]], dtype=np.int64)
        pos = np.array([[seq_len + len(generated_tokens) - 1]], dtype=np.int64)

    attn_mask = np.ones((1, seq_len + len(generated_tokens)), dtype=np.int64)
    feed = {"input_ids": ids, "attention_mask": attn_mask, **cache}
    if use_position_ids:
        feed["position_ids"] = pos

    outputs = session.run(None, feed)
    next_token = int(np.argmax(outputs[0][0, -1]))
    generated_tokens.append(next_token)

    # Update cache
    for i, out in enumerate(session.get_outputs()[1:], 1):
        name = out.name.replace("present_conv", "past_conv").replace("present.", "past_key_values.")
        if name in cache:
            cache[name] = outputs[i]

    if next_token == tokenizer.eos_token_id:
        break

# Parse thinking and response
full_response = tokenizer.decode(generated_tokens, skip_special_tokens=True)
think_match = re.search(r"<think>(.*?)</think>", full_response, re.DOTALL)
if think_match:
    thinking = think_match.group(1).strip()
    answer = full_response[think_match.end():].strip()
    print(f"Thinking:\n{thinking}\n")
    print(f"Answer:\n{answer}")
else:
    print(full_response)
