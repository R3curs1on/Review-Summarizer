import json
import os
from pyabsa import ATEPCCheckpointManager as ATEPC

# Define a valid, downloadable model. 'multilingual' is a robust choice for this task.
model_name = 'multilingual'

print(f"Loading aspect extractor model: '{model_name}'...")
print("This may take a moment on the first run as the model is downloaded.")

# Initialize the aspect extractor.
# This will now successfully download the checkpoint from the web on the first run.
aspect_extractor = ATEPC.get_aspect_extractor(
    checkpoint=model_name,
    auto_device=True,  # Automatically select CUDA if available, else CPU
    cal_perplexity=True
)

print("✅ Model loaded successfully.")


def process_reviews_batch(reviews):
    """Processes a list of reviews to extract aspects and sentiments."""
    return aspect_extractor.predict(
        reviews,
        save_result=False,
        print_result=False
    )

def summarize_product_reviews(product_id, reviews):
    """
    Takes a product ID and a list of review texts, and returns a structured
    JSON object with extracted aspects and their sentiments.
    """
    raw_results = process_reviews_batch(reviews)
    product_summary = {"product_id": product_id, "reviews": []}

    for review_text, res in zip(reviews, raw_results):
        aspects = res.get("aspect", []) or []
        sentiments = res.get("sentiment", []) or []
        confidences = res.get("confidence", []) or []

        paired_aspects = []
        # Pair up each aspect with its corresponding sentiment and confidence
        for aspect, sentiment, confidence in zip(aspects, sentiments, confidences):
            try:
                # Ensure confidence is a float, handle potential errors
                conf_val = float(confidence)
            except (ValueError, TypeError):
                conf_val = None

            paired_aspects.append({
                "term": aspect,
                "sentiment": sentiment,
                "confidence": conf_val
            })

        product_summary["reviews"].append({
            "review": review_text,
            "aspects": paired_aspects
        })

    return product_summary

# Main block for testing the script independently
if __name__ == "__main__":
    sample_reviews = [
        "the food was delicious and the service was excellent.",
        "horrible experience, the room was dirty and the staff were rude.",
        "average quality, nothing special but not bad either."
    ]
    print("\n--- Running Test ---")
    result = summarize_product_reviews(product_id="P-TEST-001", reviews=sample_reviews)

    # Save the test result to a JSON file
    output_filename = "product_reviews_summary.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Test complete. Output saved to '{output_filename}'.")
    print(json.dumps(result, indent=2, ensure_ascii=False))
