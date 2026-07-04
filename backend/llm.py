from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

# --------------------------------------------------
# Load Model (loads once when server starts)
# --------------------------------------------------

MODEL_NAME = "google/flan-t5-base"

print("Loading Flan-T5 model...")

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

device = "cuda" if torch.cuda.is_available() else "cpu"

model.to(device)

print(f"Flan-T5 loaded successfully on {device}.")


# --------------------------------------------------
# Prompt Builder
# --------------------------------------------------

def build_prompt(question, context):

    return f"""
You are an AI research assistant.

Answer ONLY using the information provided in the context.

If the answer is not present in the context, reply:

"I couldn't find that information in the uploaded document."

Context:
{context}

Question:
{question}

Answer:
"""


# --------------------------------------------------
# Generate Answer
# --------------------------------------------------

def generate_answer(question, chunks):

    # Combine retrieved chunks
    context = "\n\n".join(chunks)

    prompt = build_prompt(question, context)

    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=512
    )

    inputs = {k: v.to(device) for k, v in inputs.items()}

    outputs = model.generate(
        **inputs,
        max_new_tokens=150,
        do_sample=False,
        temperature=0.3,
        num_beams=4
    )

    answer = tokenizer.decode(
        outputs[0],
        skip_special_tokens=True
    )

    return answer