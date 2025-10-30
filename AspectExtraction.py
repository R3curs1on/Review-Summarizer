import json
import os
import warnings
import logging
 
from pyabsa import ATEPCCheckpointManager as ATEPC

# Update this path to your local checkpoint directory
checkpoint_path = os.path.join(
    os.getcwd(),
    "PyABSA_Checkpoints_Local/fast_lcf_atepc_English_cdw_apcacc_82.36_apcf1_81.89_atef1_75.43"
)
 
aspect_extractor = ATEPC.get_aspect_extractor(
    checkpoint=checkpoint_path,
    auto_device=False,
    device='cpu',
    cal_perplexity=True
)

def process_reviews_batch(reviews):
    return aspect_extractor.predict(reviews, save_result=False, print_result=False)

def summarize_product_reviews(product_id, reviews):
    raw_results = process_reviews_batch(reviews)
    product_summary = {"product_id": product_id, "reviews": []}

    for review_text, res in zip(reviews, raw_results):
        aspects = res.get("aspect", []) or []
        sentiments = res.get("sentiment", []) or []
        confidences = res.get("confidence", []) or []

        paired = []
        for a, s, c in zip(aspects, sentiments, confidences):
            try:
                conf_val = float(c)
            except Exception:
                conf_val = None
            paired.append({
                "term": a,
                "sentiment": s,
                "confidence": conf_val
            })

        product_summary["reviews"].append({
            "review": review_text,
            "aspects": paired
        })

    return product_summary

if __name__ == "__main__":
    sample_reviews = [
        "the food was delicious and the service was excellent.",
        "horrible experience, the room was dirty and the staff were rude.",
        "average quality, nothing special but not bad either."
    ]
    result = summarize_product_reviews(product_id="P-001", reviews=sample_reviews)
    with open("product_reviews_summary.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(json.dumps(result, indent=2, ensure_ascii=False))
