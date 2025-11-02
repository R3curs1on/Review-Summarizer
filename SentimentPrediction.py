# ====================================================================
# File: SentimentPrediction.py
# ====================================================================

# --- Setup & Installation for Portability ---
#
# 1. **Install Dependencies:**
#    Ensure you have the required libraries installed.
#    You might need to install PyTorch first, depending on your system.
#
#    pip install transformers torch numpy
#
# 2. **Review Data:**
#    This script expects an input JSON file from your AspectExtraction step.
#    (A dummy file is created in the '__main__' block for testing).
#
# 3. **Execution:**
#    python SentimentPrediction.py

import os
import json
import numpy as np
import torch
import warnings
from transformers import logging, BertTokenizer, BertModel

# Suppress all Hugging Face and other library warnings
logging.set_verbosity_error()
warnings.filterwarnings("ignore")

# --- Config ---
# We are replacing your local './BERT_MODEL' with a standard, portable
# model from the Hugging Face Hub. 'bert-base-uncased' is the
# most common choice for general-purpose embeddings.
BERT_REPO_ID = "bert-base-uncased"

# ====================================================================
# A. Model Loading (The Portable Change)
# ====================================================================

def load_bert_model_and_tokenizer():
    """
    Loads the BERT model and tokenizer using its standard repository ID.
    Handles automatic download/caching and moves the model to GPU if available.
    """
    print(f"Loading BERT model for embeddings: {BERT_REPO_ID}...")
    # Check for GPU availability
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    try:
        # Load tokenizer and model from Hub (or cache if already downloaded)
        tokenizer = BertTokenizer.from_pretrained(BERT_REPO_ID)
        model = BertModel.from_pretrained(BERT_REPO_ID) 
        # Move model to the selected device (GPU/CPU)
        model.to(device)
        # Set model to evaluation mode (disables dropout, etc.)
        model.eval()
        print("BERT model loaded successfully.")
        return model, tokenizer, device
        
    except Exception as e:
        print(f"\n--- ERROR ---")
        print(f"Could not load BERT model: {e}")
        print(f"Please check your internet connection and ensure '{BERT_REPO_ID}' is accessible.")
        return None, None, None

# ====================================================================
# B. Sentiment Logic (Unchanged)
# ====================================================================

def compute_overall_sentiment(aspects):
    """
    aspects: list of {term, sentiment, confidence}
    Returns one of: 'Positive', 'Negative', 'Neutral'
    """
    if not aspects:
        return "Neutral"
    scores = {"Positive": 0.0, "Negative": 0.0, "Neutral": 0.0}
    for asp in aspects:
        s = str(asp.get("sentiment", "")).strip().capitalize()
        if s not in scores:
            continue
        try:
            w = float(asp.get("confidence", 1.0))
        except Exception:
            w = 1.0
        scores[s] += max(0.0, w)

    # Tie-safe decision
    best = max(scores.items(), key=lambda x: x[1])
    if scores["Positive"] == scores["Negative"] and scores["Positive"] > 0:
        return "Neutral"
    return best[0]

def extract_review_items(product_summary):
    """
    Converts AspectExtraction output into a list of review items.
    """
    items = []
    for entry in product_summary.get("reviews", []):
        aspects = entry.get("aspects", []) or []
        pairs = []
        for asp in aspects:
            a = asp.get("term")
            s = asp.get("sentiment")
            if a and s:
                pairs.append((a, s))
        overall = compute_overall_sentiment(aspects)
        items.append({
            "review": entry.get("review", ""),
            "aspects": aspects,
            "aspect_sentiments": pairs,
            "overall_sentiment": overall
        })
    return items

def bert_encode_prompt(pairs, tokenizer, model, device):
    """
    pairs: list of (aspect, sentiment)
    Returns np.array CLS embedding for the prompt 'aspect: sentiment; ...'
    """
    prompt = "; ".join([f"{a}: {s}" for a, s in pairs]) if pairs else "no salient aspect found"
    # Tokenize the prompt
    inputs = tokenizer(prompt, return_tensors='pt', truncation=True, max_length=128)
    # Move inputs to the same device as the model (GPU/CPU)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    # Run the model
    with torch.no_grad():
        outputs = model(**inputs)
    # Get the [CLS] token embedding and move it back to CPU for numpy
    cls_vec = outputs.last_hidden_state[:, 0, :].squeeze().cpu().numpy()
    return cls_vec

def encode_reviews_and_save(product_id, items, tokenizer, model, device, emb_dir="./embeddings"):
    """
    Creates an embedding per review and a product-level average embedding.
    Saves to disk and returns file paths.
    """
    os.makedirs(emb_dir, exist_ok=True)
    review_paths = []
    vecs = []

    print(f"Generating {len(items)} review embeddings...")
    for idx, item in enumerate(items):
        # Pass the model, tokenizer, and device to the encoding function
        vec = bert_encode_prompt(item["aspect_sentiments"], tokenizer, model, device)
        vecs.append(vec)
        path = os.path.join(emb_dir, f"{product_id}_r{idx+1}.npy")
        np.save(path, vec)
        review_paths.append(path)

    product_path = None
    if vecs:
        # Stack all review vectors and compute the product-level average
        product_vec = np.mean(np.stack(vecs, axis=0), axis=0)
        product_path = os.path.join(emb_dir, f"{product_id}_product.npy")
        np.save(product_path, product_vec)
        print(f"Saved product average embedding to {product_path}")

    return review_paths, product_path

def analyze_product(product_summary, out_dir="./outputs"):
    """
    Orchestrates classification + embeddings for a single product JSON.
    Returns the summary dict and writes it to ./outputs/{product_id}_sentiment.json
    """

    model, tokenizer, device = load_bert_model_and_tokenizer()
    if not model:
        print("=============Failed to load embedding model for sentiment analysis.===========")
        return None

    os.makedirs(out_dir, exist_ok=True)
    product_id = product_summary.get("product_id", "UNKNOWN")
    # 1. Process review data
    items = extract_review_items(product_summary)
    # 2. Generate and save all embeddings
    per_review_emb_files, product_emb_file = encode_reviews_and_save(
        product_id, items, tokenizer, model, device
    )
    # 3. Compile the final output JSON
    out = {
        "product_id": product_id,
        "num_reviews": len(items),
        "product_embedding_file": product_emb_file,
        "reviews": []
    }
    for idx, item in enumerate(items):
        out["reviews"].append({
            "review": item["review"],
            "overall_sentiment": item["overall_sentiment"],
            "aspect_sentiments": item["aspect_sentiments"],
            "embedding_file": per_review_emb_files[idx] if idx < len(per_review_emb_files) else None
        })

    # 4. Save the final JSON to disk
    out_path = os.path.join(out_dir, f"{product_id}_sentiment.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    return out, out_path
 
if __name__ == "__main__":
    # --- Load Model ---
    # We load the model *once* and pass it to the functions
    model, tokenizer, device = load_bert_model_and_tokenizer()

    if model:
        # --- DUMMY FILE CREATION FOR TESTING PORTABILITY ---
        # This creates a fake input file so the script can run
        input_json_path = "./product_reviews_summary.json"
        dummy_data = {
            "product_id": "P-001",
            "reviews": [
                {"review": "The screen is bright, but the battery is bad.",
                 "aspects": [
                     {"term": "screen", "sentiment": "Positive", "confidence": 0.9},
                     {"term": "battery", "sentiment": "Negative", "confidence": 0.98}
                 ]},
                {"review": "Great speed! Very fast.",
                 "aspects": [
                     {"term": "speed", "sentiment": "Positive", "confidence": 0.95}
                 ]},
                {"review": "It was just okay.",
                 "aspects": []}
            ]
        }
        with open(input_json_path, "w", encoding="utf-8") as f:
            json.dump(dummy_data, f, indent=2)
        print(f"Created dummy input file: {input_json_path}")
        # --- END DUMMY FILE CREATION ---
        
        try:
            # Load the product summary JSON (the dummy file in this case)
            with open(input_json_path, "r", encoding="utf-8") as f:
                product = json.load(f)
            
            # Run the main analysis pipeline
            result, saved_path = analyze_product(product, tokenizer, model, device)
            
            print(f"\n--- Analysis Complete ---")
            print(f"Saved sentiment + embeddings to: {saved_path}")

        except FileNotFoundError:
            print(f"ERROR: Input file not found at {input_json_path}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
    else:
        print("Failed to load BERT model. Exiting.")
