from transformers import MoonshineForConditionalGeneration, AutoProcessor
from datasets import load_dataset, Audio
import torch

device = "cuda:0" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

model = MoonshineForConditionalGeneration.from_pretrained('UsefulSensors/moonshine-tiny-ar').to(device).to(torch_dtype)
processor = AutoProcessor.from_pretrained('UsefulSensors/moonshine-tiny-ar')

dataset = load_dataset('UsefulSensors/multilingual_examples', split='ar')
dataset = dataset.cast_column("audio", Audio(processor.feature_extractor.sampling_rate))
sample = dataset[0]["audio"]

inputs = processor(
    sample["array"], 
    return_tensors="pt",
    sampling_rate=processor.feature_extractor.sampling_rate
)
inputs = inputs.to(device, torch_dtype)

# to avoid hallucination loops, we limit the maximum length of the generated text based expected number of tokens per second
token_limit_factor = 13 / processor.feature_extractor.sampling_rate 
seq_lens = inputs.attention_mask.sum(dim=-1)
max_length = int((seq_lens * token_limit_factor).max().item())

generated_ids = model.generate(**inputs, max_length=max_length)
print(processor.decode(generated_ids[0], skip_special_tokens=True))
