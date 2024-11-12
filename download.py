from transformers import T5ForConditionalGeneration, T5Tokenizer

model_name = "t5-large"
model = T5ForConditionalGeneration.from_pretrained(model_name)
tokenizer = T5Tokenizer.from_pretrained(model_name)

# Save locally
model.save_pretrained("./alphabetize_output/alphabetize_sup_scale/t5large_bs32_wd0.01_lr1e-5_beam5_min5_max_20_seed0/model")
tokenizer.save_pretrained("./alphabetize_output/alphabetize_sup_scale/t5large_bs32_wd0.01_lr1e-5_beam5_min5_max_20_seed0/model")
