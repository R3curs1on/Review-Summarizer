# ====================================================================
# STEP 1: SILENCE WARNINGS & IMPORT LIBRARIES
# ====================================================================
import os
import streamlit as st
import traceback
import json

# Import the main functions from your project files
from WebScrapper import scrape_flipkart_reviews
from AspectExtraction import summarize_product_reviews
from SentimentPrediction import analyze_product
from OpinionSummarization import summarize_opinions
from HumanReadableSummary import generate_human_report_text

def run_full_pipeline(url, api_key):
    """
    Executes the entire review summarization pipeline from scraping to final report generation.
    """
    # Step 1: Scraping
    st.info("🔎 Scraping reviews... This may take a moment.")
    reviews = scrape_flipkart_reviews(url)
    if not reviews:
        st.error("Could not scrape any reviews. Please check the URL or try another product.")
        return None

    # Limit reviews for faster processing
    if len(reviews) > 50:
        reviews = reviews[:50]
    st.write(f"✅ Found {len(reviews)} reviews.")

    # Step 2: Aspect Extraction
    st.info("🧠 Extracting key aspects from reviews...")
    product_id = "product_summary"
    aspect_results = summarize_product_reviews(product_id, reviews)
    st.write("✅ Aspect extraction complete.")

    # Step 3: Sentiment Prediction
    st.info("❤️ Analyzing sentiment for each aspect...")
    _, sentiment_path = analyze_product(aspect_results)
    st.write("✅ Sentiment analysis complete.")

    # Step 4: Opinion Summarization (BART) - Kept for potential future use
    st.info("✍️ Generating abstractive summary with BART...")
    summarize_opinions(sentiment_path)
    st.write("✅ Abstractive summary generated.")

    # Step 5: Generate Human-Readable Report (Gemini)
    st.info("🤖 Calling Gemini to generate a high-quality, human-readable summary...")
    try:
        with open(sentiment_path, 'r', encoding='utf-8') as f:
            sentiment_data = json.load(f)
    except Exception as e:
        st.error(f"Failed to read the sentiment data file: {e}")
        st.code(traceback.format_exc())
        return None

    human_report = generate_human_report_text(sentiment_data, api_key)
    st.write("✅ Human-readable report generated.")

    return human_report

 
# Set the page title, icon, and layout
st.set_page_config(page_title="Review Summarizer", page_icon="🛍️", layout="wide")

# Title and subtitle
st.title("🛍️ AI-Powered Review Summarizer")
st.markdown("Enter a product URL to get a high-quality summary of user reviews, powered by Gemini.")

# --- User Input for URL ---
url = st.text_input(
    "Enter Product URL",
    placeholder="https://www.flipkart.com/..."
)

# --- HARDCODED API KEY ---
# WARNING: It is not secure to hardcode API keys and share the file.
# This is for local testing only. Do not push this to a public repository.
gemini_api_key = ""  # <--- PASTE YOUR GEMINI API KEY HERE

# "Generate" button logic
if st.button("✨ Generate Summary", type="primary"):
    if url and gemini_api_key:
        # Create a container to show the progress and results
        with st.container(border=True):
            try:
                # Run the entire pipeline and pass the API key
                final_report = run_full_pipeline(url, gemini_api_key)

                if final_report:
                    st.success("🎉 Summary Generation Complete!")
                    st.markdown("---")
                    # The final report from Gemini is already in Markdown format
                    st.markdown(final_report)

            except Exception as e:
                st.error("An unexpected error occurred during the process.")
                st.code(traceback.format_exc())
    elif not url:
        st.warning("Please enter a product URL to begin.")
    else:
        # This warning shows if the URL is present but the API key is not
        st.warning("⚠️ Please paste your Gemini API Key into the `gemini_api_key` variable in the script.")
