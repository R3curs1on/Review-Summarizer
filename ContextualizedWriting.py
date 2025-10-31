# ====================================================================
# File: HumanReadableSummary.py
# ====================================================================

# --- Setup & Installation ---
#
# 1. **Install Dependencies:**
#    This script requires the 'requests' library to call the Gemini API.
#
#    pip install requests
#
# 2. **SET YOUR API KEY (CRITICAL!):**
#    Find the `if __name__ == "__main__":` block at the bottom of this
#    file and paste your API key directly into the `apiKey` variable.
#
# 3. **Input Data:**
#    This script looks for 'sentiment_example.json'. A dummy file
#    is created below in the main() block for testing.
#
# 4. **Execution:**
#    python HumanReadableSummary.py

import json
import os
import re
import time
import requests
import warnings

# --- Gemini API Configuration ---
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent"

# System prompt to guide the AI
GEMINI_SYSTEM_PROMPT = """
You are an expert product review summarizer. Your task is to transform a structured JSON object
containing positive and negative aspects of a product, along with raw user review snippets,
into a single, high-quality, human-readable report.

Your response MUST be in this format:
1.  A "Final Report" header.
2.  An "Overall Summary" paragraph. This should be a synthesized, flowing paragraph (NOT a list) that
    naturally integrates the main themes, both good and bad.
3.  A "What Users Liked" section. This should be 1-2 paragraphs that group similar positive
    concepts.
4.  A "What Users Disliked" section. This should be 1-2 paragraphs that group similar
    negative concepts.

RULES:
-   **Be Natural:** Write in clear, engaging, and fluent language.
-   **Synthesize, Don't List:** Do not just list every aspect. Group them.
-   **Use Quotes Sparingly:** Do not include a quote for every single aspect.
-   **Be Contextual:** Use the provided snippets to understand *why* users liked or
    disliked something.
-   **Use Markdown:** Use Markdown for formatting (e.g., ## Headers, **bold**).
-   **NEW RULE: BE CONCISE. The entire report (from "Final Report" to the end)
    MUST be a maximum of 300 words.**
"""

# ====================================================================
#   Original Report Functions (Kept for Future Use)
# ====================================================================

def find_best_review_for_aspect(aspect_term, desired_sentiment, sentiment_data):
    """
    Searches through all reviews to find a good example snippet for a given aspect.
    """
    best_review = "No specific example found."
    for review_info in sentiment_data.get("reviews", []):
        for aspect, sentiment in review_info.get("aspect_sentiments", []):
            if aspect.lower() == aspect_term.lower() and sentiment.lower() == desired_sentiment.lower():
                return f'"{review_info["review"]}"'  # Found a match
    return best_review


def sanitize_example(example):
    """
    Cleans up review snippets for display.
    """
    if not example:
        return example
    default_msg = "No specific example found."
    if example == default_msg:
        return example

    # Remove surrounding quotes, clean, add back
    quote_char = ""
    if example.startswith(('"', "'")):
        quote_char = example[0]
        example = example[1:-1] if example.endswith(quote_char) else example[1:]

    example = example.replace("\n", " ").strip()
    
    # Remove leading star rating (e.g., "5 The product is great")
    if example and example[0] in "12345" and (len(example) == 1 or example[1] in (" ", "\t", "*")):
        example = "*" + example[1:].lstrip()
    
    return f"{quote_char}{example}{quote_char}"


def generate_original_report(summary_text, sentiment_data):
    """
    Generates the original, list-based report. (For future database use)
    """
    product_id = sentiment_data.get("product_id", "UNKNOWN")

    # 1. Identify all unique positive and negative aspects
    positive_aspects, negative_aspects = set(), set()
    for review in sentiment_data.get("reviews", []):
        for aspect, sentiment in review.get("aspect_sentiments", []):
            if sentiment.lower() == 'positive':
                positive_aspects.add(aspect)
            elif sentiment.lower() == 'negative':
                negative_aspects.add(aspect)

    # 2. Build the final report string
    report_lines = []
    report_lines.append("=" * 40)
    report_lines.append(f"✅ FINAL REVIEW SUMMARY FOR PRODUCT: {product_id} (Original Format)")
    report_lines.append("=" * 40)
    report_lines.append(f"\n## 📝 Overall Summary (from BART)\n\n{summary_text}")

    if positive_aspects:
        report_lines.append("\n\n" + "-" * 20 + "\n\n## 👍 What Users Liked\n")
        for aspect in sorted(list(positive_aspects)):
            example = find_best_review_for_aspect(aspect, "positive", sentiment_data)
            report_lines.append(f"- **{aspect.capitalize()}:** {sanitize_example(example)}")

    if negative_aspects:
        report_lines.append("\n\n" + "-" * 20 + "\n\n## 👎 What Users Disliked\n")
        for aspect in sorted(list(negative_aspects)):
            example = find_best_review_for_aspect(aspect, "negative", sentiment_data)
            report_lines.append(f"- **{aspect.capitalize()}:** {sanitize_example(example)}")

    return "\n".join(report_lines)

 
def normalize_aspect(aspect):
    """
    Groups similar aspect terms to avoid repetition for the AI.
    """
    term = aspect.lower().strip()
    if "bass" in term or "buss" in term: return "Bass"
    if "sound" in term: return "Sound Quality"
    if "look" in term or "design" in term: return "Design & Look"
    if "connect" in term or "feature" in term or term in ("sd", "aux", "usb"): return "Connectivity & Features"
    if "woofer" in term: return "Woofer"
    if "size" in term or "length" in term: return "Size & Wire Length"
    return term.capitalize()


def aggregate_aspect_data(sentiment_data):
    """
    Loops through reviews ONCE to build a clean data structure for the AI.
    """
    positive_aspects, negative_aspects = {}, {}
    for review_info in sentiment_data.get("reviews", []):
        review_text = review_info.get("review")
        if not review_text:
            continue

        # Sanitize the *full* review text once
        snippet = sanitize_example(f'"{review_text}"')

        for aspect, sentiment in review_info.get("aspect_sentiments", []):
            normalized_key = normalize_aspect(aspect)
            data_dict = positive_aspects if sentiment.lower() == 'positive' else negative_aspects
            
            if sentiment.lower() not in ('positive', 'negative'):
                continue
                
            if normalized_key not in data_dict:
                data_dict[normalized_key] = []
            data_dict[normalized_key].append(snippet)

    # De-duplicate snippets
    for data_dict in [positive_aspects, negative_aspects]:
        for key in data_dict:
            data_dict[key] = list(set(data_dict[key]))
    return positive_aspects, negative_aspects


def call_gemini_api(api_key, system_prompt, user_prompt, max_retries=5):
    """
    Calls the Gemini API with exponential backoff for retries.
    """
    headers = {"Content-Type": "application/json"}
    params = {"key": api_key}
    payload = {
        "contents": [{"parts": [{"text": user_prompt}]}],
        "systemInstruction": {"parts": [{"text": system_prompt}]}
    }

    retries = 0
    while retries < max_retries:
        try:
            response = requests.post(GEMINI_API_URL, headers=headers, params=params, json=payload, timeout=90)
            response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)
            result = response.json()

            if "candidates" in result and result.get("candidates"):
                text = result["candidates"][0].get("content", {}).get("parts", [{}])[0].get("text")
                if text:
                    return text
            
            warnings.warn(f"Received unexpected/empty response from API: {result}")
            return "--- Error: Could not parse LLM response. ---"

        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err} - {http_err.response.text}")
            if http_err.response.status_code == 429 or http_err.response.status_code >= 500:
                pass # This is a server-side/rate limit error, so we retry
            else:
                return f"--- Error: HTTP {http_err.response.status_code} from API. Check API Key or Model Name. ---"
        except requests.exceptions.RequestException as err:
            print(f"A non-HTTP error occurred: {err}")
            # This could be a connection error, timeout, etc. We retry.

        retries += 1
        wait_time = 2 ** retries
        print(f"Retrying in {wait_time} seconds...")
        time.sleep(wait_time)

    return f"--- Error: API call failed after {max_retries} retries. ---"


def generate_human_report_text(sentiment_data, api_key):
    """
    Calls Gemini API to get the human-readable summary text.
    """
    product_id = sentiment_data.get("product_id", "UNKNOWN_PRODUCT")

    print("Aggregating aspect data for LLM...")
    positive_data, negative_data = aggregate_aspect_data(sentiment_data)

    user_prompt_data = {
        "product_id": product_id,
        "what_users_liked": positive_data,
        "what_users_disliked": negative_data
    }

    # Create the final prompt for the AI
    user_prompt = f"""
Here is the structured review data for product '{product_id}'.
Please generate the human-readable report based on these findings.

{json.dumps(user_prompt_data, indent=2)}
"""

    print("Calling LLM to generate human-readable summary...")
    print("(This may take a moment, depending on API response times)")
    summary_text = call_gemini_api(api_key, GEMINI_SYSTEM_PROMPT, user_prompt)

    # Add a final header
    final_report = ""
    final_report += f"\n LLM Based HUMAN-READABLE SUMMARY\n\n"
    final_report += summary_text

    return final_report
 

if __name__ == "__main__":
    # --- 1. CRITICAL: Set your API Key ---
    # PASTE YOUR GEMINI API KEY HERE.
    # IMPORTANT: Do not share this file publicly with your key filled in.
    apiKey = "" # <--- PASTE YOUR KEY INSIDE THE QUOTES

    if not apiKey:
        print("="*80)
        print("❌ WARNING: The 'apiKey' variable is empty.")
        print("Please open the script, find the `if __name__ == '__main__':` block,")
        print("and paste your API key into the `apiKey` variable.")
        print("="*80)
        exit() # Stop the script if no key is found

    # --- 2. Define Paths ---
    input_json = "sentiment_example.json"
    out_dir = "./outputs"

    # --- 3. DUMMY FILE CREATION (for Portability) ---
    # Create a fake input file if it doesn't exist, so the script can run.
    if not os.path.exists(input_json):
        print(f"'{input_json}' not found. Creating a dummy file for testing.")
        dummy_sentiment_data = {
            "product_id": "P-DUMMY-001",
            "reviews": [
                {
                    "review": "5 The sound quality is amazing and the bass is deep!",
                    "aspect_sentiments": [["sound quality", "Positive"], ["bass", "Positive"]]
                },
                {
                    "review": "1 The design is nice but the woofer is very weak and feels cheap.",
                    "aspect_sentiments": [["design", "Positive"], ["woofer", "Negative"], ["woofer", "Negative"]]
                },
                {
                    "review": "4 Good sound, but the wire length is too short.",
                    "aspect_sentiments": [["sound", "Positive"], ["wire length", "Negative"]]
                }
            ]
        }
        try:
            with open(input_json, 'w', encoding='utf-8') as f:
                json.dump(dummy_sentiment_data, f, indent=2)
        except IOError as e:
            print(f"Error creating dummy file: {e}")
            exit()

    # --- 4. Load Data ---
    print(f"Loading sentiment data from '{input_json}'...")
    try:
        with open(input_json, 'r', encoding='utf-8') as f:
            sentiment_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Could not find sentiment file at {input_json}")
        exit()
    except json.JSONDecodeError:
        print(f"Error: Could not parse JSON from {input_json}")
        exit()

    product_id = sentiment_data.get("product_id", "UNKNOWN_PRODUCT")

    # --- 5. Generate Human-Readable Report (Primary Task) ---
    human_report = generate_human_report_text(sentiment_data, apiKey)
    print("✅ Human-readable report generated.")

    # --- 6. Save Final Report ---
    os.makedirs(out_dir, exist_ok=True)
    report_path = os.path.join(out_dir, f"{product_id}_Gemini_Report.md")

    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(human_report)
    except IOError as e:
        print(f"Error writing report to file: {e}")
        exit()

    print("\n" + "=" * 50)
    print("🎉 Success! LLM  report generated.")
    print(f"Saved to: {report_path}")
    print("=" * 50)
    
    # --- 7. Print Preview ---
    print("\n--- REPORT PREVIEW ---")
    print(human_report)
