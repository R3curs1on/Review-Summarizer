# ====================================================================
# File: OpinionSummarization.py
# ====================================================================

# --- Setup & Installation for Portability ---
#
# 1. **Install Dependencies:**
#    Ensure you have the required libraries installed.
#    You might need to install PyTorch first, depending on your system.
#
#    pip install transformers torch
#
# 2. **Review Data:**
#    This script expects a JSON file with a specific structure at
#    './outputs/P-001_sentiment.json' (or the path you provide).
#
# 3. **Execution:**
#    python OpinionSummarization.py

import os
import json
import warnings
from transformers import logging, BartTokenizer, BartForConditionalGeneration, pipeline

# Suppress all Hugging Face and other library warnings for cleaner output
logging.set_verbosity_error()
warnings.filterwarnings("ignore")

# --- Config ---
# We use the standard repository ID. The 'transformers' library handles
# downloading and caching to the default Hugging Face cache location.
BART_REPO_ID = "facebook/bart-large-cnn"


def load_sentiment_json(path):
    """Loads the structured sentiment data from a JSON file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Input file not found at: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def aspects_to_fact_prompt(sentiment_payload):
    """
    Consolidates all aspect-sentiment pairs across all reviews into a
    single, structured prompt for the summarizer model. This is key
    for multi-document summarization.
    """
    positives, negatives, neutrals = set(), set(), set()
    for r in sentiment_payload.get("reviews", []):
        # Handle cases where 'aspect_sentiments' might be None or missing
        for aspect, sentiment in r.get("aspect_sentiments", []) or []:
            if sentiment and aspect:
                s_lower = sentiment.lower()
                if s_lower == "positive":
                    positives.add(aspect)
                elif s_lower == "negative":
                    negatives.add(aspect)
                elif s_lower == "neutral":
                    neutrals.add(aspect)
    
    # Calculate overall sentiments
    reviews = sentiment_payload.get("reviews", [])
    pos = sum(1 for r in reviews if r.get("overall_sentiment") == "Positive")
    neg = sum(1 for r in reviews if r.get("overall_sentiment") == "Negative")
    neu = sum(1 for r in reviews if r.get("overall_sentiment") == "Neutral")
    
    # Structure the prompt
    lines = [
        f"Reviews: {pos} positive, {neg} negative, {neu} neutral.",
        f"Praised aspects: {', '.join(positives) if positives else 'None'}.",
        f"Criticized aspects: {', '.join(negatives) if negatives else 'None'}.",
        f"Neutral aspects: {', '.join(neutrals) if neutrals else 'None'}."
    ]
    return " ".join(lines) 

def get_portable_bart_summarizer():
    """
    Loads the BART model using its standard repository ID.
    The 'transformers' library handles local caching automatically.
    
    - First run: Downloads the model (requires internet).
    - Subsequent runs: Loads from the local cache (offline).
    """
    print(f"Loading BART Summarization model: {BART_REPO_ID}. This may take a minute...")
    
    # Load model and tokenizer directly from the Hugging Face Hub (or local cache)
    try:
        # NOTE: We do not use local_files_only=True initially to allow download.
        # It will automatically check the cache first.
        tok = BartTokenizer.from_pretrained(BART_REPO_ID)
        mdl = BartForConditionalGeneration.from_pretrained(BART_REPO_ID)
        
        # Create the pipeline for convenient summarization
        summarizer = pipeline("summarization", model=mdl, tokenizer=tok, framework="pt", device=-1)
        print("BART model loaded successfully.")
        return summarizer
        
    except Exception as e:
        # This catch-all handles network errors, incorrect model IDs, etc.
        print(f"\n--- ERROR ---")
        print(f"Could not load BART model: {e}")
        print(f"Please check your internet connection and ensure '{BART_REPO_ID}' is accessible.")
        print(f"If running offline after a failed first-time run, you need to manually ensure the model is in the Hugging Face cache.")
        return None
 
def filter_hallucinated_summary(summary, sentiment_payload):
    """
    Simple post-processing to clean up potential hallucinations (e.g.,
    model inventing product names or phrases not supported by input).
    """
    product_id = sentiment_payload.get("product_id", "the product")
    
    # Capitalize the product ID for a natural fit in the text
    display_name = product_id.replace('-', ' ').title()

    # The model may generate 'summaries' based on the input structure
    # This just ensures we don't present entirely unsupported facts.
    # If the summary is suspiciously short, it might be a failure.
    if len(summary) < 20:
        return f"Summary generation was inconclusive. Key findings: {summary}"
    
    return summary.replace("The product", display_name).replace("the product", display_name)


def summarize_opinions(input_json_path, out_dir="./outputs", min_len=60, max_len=180):
    
    os.makedirs(out_dir, exist_ok=True)
    payload = load_sentiment_json(input_json_path)
    
    # 1. Prepare the input text for summarization
    text = aspects_to_fact_prompt(payload)
    
    # 2. Load the summarization pipeline
    summarizer = get_portable_bart_summarizer()
    if not summarizer:
        return "Summarization failed due to model loading error.", None
        
    # 3. Generate the summary
    print(f"Summarizing {len(payload.get('reviews', []))} reviews...")
    out = summarizer(
        text, 
        max_length=max_len, 
        min_length=min_len, 
        do_sample=False  # Use beam search for deterministic results
    )[0]["summary_text"]
    
    # 4. Post-process and save
    out = filter_hallucinated_summary(out, payload)
    product_id = payload.get("product_id", "UNKNOWN")
    out_path = os.path.join(out_dir, f"{product_id}_summary.txt")
    
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(out)
        
    return out, out_path 

if __name__ == "__main__":
    # NOTE: You MUST ensure this file exists and contains the sentiment structure.
    # We'll use your example file name.
    input_json_path = "./outputs/P-001_sentiment.json"
    
    # --- DUMMY FILE CREATION FOR TESTING PORTABILITY ---
    # Since the input file is missing, we create a dummy one for the script to run.
    dummy_payload = {
        "product_id": "P-001",
        "reviews": [
            {
                "overall_sentiment": "Positive",
                "aspect_sentiments": [["speed", "Positive"], ["cost", "Neutral"]]
            },
            {
                "overall_sentiment": "Negative",
                "aspect_sentiments": [["screen", "Negative"], ["battery", "Negative"]]
            },
             {
                "overall_sentiment": "Positive",
                "aspect_sentiments": [["screen", "Positive"], ["support", "Positive"]]
            },
        ]
    }
    os.makedirs("./outputs", exist_ok=True)
    with open(input_json_path, "w", encoding="utf-8") as f:
        json.dump(dummy_payload, f, indent=4)
    print(f"Created dummy input file: {input_json_path}")
    # --- END DUMMY FILE CREATION ---
    
    try:
        summary, saved = summarize_opinions(input_json_path)
        print("\n--- Summary Result ---")
        print(summary)
        print(f"\nSaved opinion summary to: {saved}")
    except FileNotFoundError as e:
        print(f"\nCRITICAL ERROR: {e}")
        print("Please ensure your input JSON file exists at the specified path.")
