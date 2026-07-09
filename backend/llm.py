from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

# Load Model (loads once when server starts)

MODEL_NAME = "google/flan-t5-base"

print("Loading Flan-T5 model...")

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

device = "cuda" if torch.cuda.is_available() else "cpu"

model.to(device)

print(f"Flan-T5 loaded successfully on {device}.")



# Prompt Builder
def build_prompt(question, context):

    return f"""
You are a helpful assistant that answers questions
based on the provided context. Follow these rules strictly:

1. Only answer based on the provided context
2. If the context does not contain enough information, say "I couldn't find that information in the uploaded document."
3. Cite your sources using [Source N] notation
4. Be concise but thorough
5. If asked about something outside the context, explain that
   your knowledge is limited to the provided documents

Context:
{context}

Question:
{question}

Answer:
"""


# Generate Answer

def generate_answer(question, chunks):

    # Combine retrieved chunks
    all_chunks = get_all_chunks(document_id)

    context = all_chunks[0]

    for chunk in chunks:

        if chunk not in context:
            context += "\n\n" + chunk

    prompt = build_prompt(question, context)

    # tokenizes the prompt
    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=512
    )

    inputs = {k: v.to(device) for k, v in inputs.items()}

    # model generates text
    outputs = model.generate(
        **inputs,
        max_new_tokens=150,
        do_sample=False,
        temperature=0.3,
        num_beams=4
    )

    # convert the output tokens back into text
    answer = tokenizer.decode(
        outputs[0],
        skip_special_tokens=True
    )

    return answer