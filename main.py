import traceback
import json
from flask import Flask, request, jsonify, render_template

# Initialize the Flask application
app = Flask(__name__)

# --- HARDCODED API KEY ---
# This is loaded at the start, as it's very lightweight.
GEMINI_API_KEY = ""  # <--- PASTE YOUR GEMINI API KEY HERE

# Create a global variable to hold our ML pipeline components.
pipeline_components = None


def initialize_pipeline():
    """
    This function contains all the slow imports and model loading.
    It will only be called ONCE.
    """
    global pipeline_components
    print("🚀 Initializing ML pipeline for the first time... (This may take a few minutes)")

    # Import all the necessary functions
    from WebScraper import scrape_flipkart_reviews
    from AspectExtraction import summarize_product_reviews
    from SentimentPrediction import analyze_product
    from OpinionSummarization import summarize_opinions
    # Corrected import from our previous discussion
    from ContextualizedWriting import generate_human_report_text

    # Store the loaded functions in our global dictionary
    pipeline_components = {
        "scrape": scrape_flipkart_reviews,
        "extract_aspects": summarize_product_reviews,
        "analyze_sentiment": analyze_product,
        "summarize_opinions": summarize_opinions,
        "generate_report": generate_human_report_text,
    }
    print("✅ Pipeline initialized and models are now loaded in memory.")


@app.route('/')
def index():
    """Renders the main HTML page instantly."""
    return render_template('index.html')


@app.route('/summarize', methods=['POST'])
def summarize():
    """
    The main API endpoint. It checks if the pipeline is loaded
    and initializes it only if necessary.
    """
    # This is the crucial check.
    if pipeline_components is None:
        initialize_pipeline()

    # Get the URL from the incoming JSON request
    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({'error': 'URL is required.'}), 400
    if not GEMINI_API_KEY:
        # This check is now crucial. Make sure your key is in the variable above.
        return jsonify({'error': 'API key is not set in the Flask app.'}), 500

    try:
        # --- Start of the ML Pipeline ---
        print("Step 1: Scraping reviews...")
        reviews = pipeline_components["scrape"](url)
        if not reviews:
            return jsonify({'error': 'Could not scrape any reviews from the URL.'}), 404
        if len(reviews) > 50:
            reviews = reviews[:50]
        print(f"-> Found {len(reviews)} reviews.")

        print("Step 2: Extracting aspects...")
        product_id = "product_summary"
        aspect_results = pipeline_components["extract_aspects"](product_id, reviews)
        print("-> Aspect extraction complete.")

        print("Step 3: Analyzing sentiment...")
        _, sentiment_path = pipeline_components["analyze_sentiment"](aspect_results)
        print("-> Sentiment analysis complete.")

        print("Step 4: Running BART summary...")
        # This function returns the path, so we'll capture it to read the summary
        _, summary_path = pipeline_components["summarize_opinions"](sentiment_path)
        print("-> BART summary complete.")

        # Read the simple summary from the file
        try:
            with open(summary_path, 'r', encoding='utf-8') as f:
                simple_summary_text = f.read()
        except Exception:
            simple_summary_text = "Could not load simple summary."

        print("Step 5: Generating Contextual report...")
        with open(sentiment_path, 'r', encoding='utf-8') as f:
            sentiment_data = json.load(f)

        contextual_report_text = pipeline_components["generate_report"](sentiment_data, GEMINI_API_KEY)
        print("-> Contextual report generated.")

        # --- THIS IS THE FIX ---
        # This version correctly returns the JSON that script.js expects.
        return jsonify({
            'simple_summary': simple_summary_text,
            'contextual_report': contextual_report_text,
        })

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({'error': f'An unexpected error occurred: {traceback.format_exc()}'}), 500


if __name__ == '__main__':
    # The server will start instantly.
    # use_reloader=False prevents the server from restarting during model download.
    app.run(debug=True, use_reloader=False)

