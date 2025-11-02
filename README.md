# AI-Powered Review Summarizer

This project is a full-stack web application that uses a sophisticated AI pipeline to scrape, analyze, and summarize product reviews from Flipkart. Users can paste a product URL, and the application generates two types of summaries: a concise, abstractive summary and a detailed, human-readable report crafted by a Large Language Model (LLM).

The frontend is a modern, responsive single-page application built with vanilla HTML, CSS, and JavaScript, featuring a clean, "claymorphism" design. The backend is a Flask server that orchestrates a multi-stage machine learning pipeline.

![Project Demo](https://github.com/R3curs1on/Review-Summarizer/blob/main/assets/demo.gif?raw=true)

## Features

-   **Dynamic Web Scraping**: Uses Selenium to robustly scrape reviews from Flipkart product pages.
-   **Multi-Stage AI Pipeline**:
    1.  **Aspect Extraction**: Identifies key product features being discussed (e.g., "battery," "screen quality") using `pyabsa`.
    2.  **Sentiment Analysis**: Determines the sentiment (Positive, Negative, Neutral) for each aspect.
    3.  **Abstractive Summarization**: Generates a short, concise summary using a BART model.
    4.  **Contextual Report Generation**: Uses the Google Gemini API to produce a high-quality, human-readable report that synthesizes all findings.
-   **Lazy-Loaded Models**: The ML models are loaded only on the first API call to ensure the web server starts instantly.
-   **Responsive Frontend**: A clean and modern UI that works on all device sizes.
-   **Real-time Progress Updates**: The frontend shows the user which stage of the analysis pipeline is currently running.

## Tech Stack

-   **Backend**: Flask, Gunicorn
-   **Machine Learning**: PyTorch, Transformers (Hugging Face), PyABSA
-   **Web Scraping**: Selenium, WebDriver-Manager
-   **LLM Integration**: Google Gemini API
-   **Frontend**: HTML5, CSS3, JavaScript
-   **Deployment**: Python, Gunicorn

## How It Works

The application follows a 5-step pipeline to process reviews:

1.  **Scrape Reviews**: When a user submits a Flipkart URL, the Flask backend uses **Selenium** to navigate to the page and scrape the raw text of user reviews.
2.  **Extract Aspects**: The collected reviews are passed to **PyABSA**, which identifies the specific product aspects mentioned (e.g., "sound," "design," "battery life").
3.  **Predict Sentiment**: A **BERT-based model** then analyzes the sentiment associated with each extracted aspect.
4.  **Generate Simple Summary**: The aspect-sentiment pairs are fed into a **BART model** to generate a short, abstractive summary.
5.  **Generate Contextual Report**: A structured JSON object containing all the extracted aspects, sentiments, and review snippets is sent to the **Google Gemini API**. A carefully crafted system prompt instructs the LLM to write a flowing, human-readable report in Markdown format.
6.  **Display Results**: The final simple summary and the LLM-generated report are sent back to the frontend and displayed dynamically.

## Setup and Installation

Follow these steps to run the project locally.

### Prerequisites

-   Python 3.8+
-   Google Chrome browser installed
-   A Google Gemini API Key

### 1. Clone the Repository

```bash
git clone https://github.com/R3curs1on/Review-Summarizer.git
cd Review-Summarizer
```

### 2. Install Dependencies

It is highly recommended to use a virtual environment.

```bash
# Create and activate a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

# Install the required packages
pip install -r requirements.txt
```

### 3. Configure API Key

You need to add your Google Gemini API key to the project.

-   Open the `main.py` file.
-   Find the line `GEMINI_API_KEY = ""` near the top of the file.
-   Paste your API key inside the quotes.

```python
# In main.py
GEMINI_API_KEY = "YOUR_API_KEY_HERE"
```

### 4. Run the Application

You can run the application using the Flask development server.

```bash
python main.py
```

The server will start on `http://127.0.0.1:5000`. Open this URL in your browser.

**Note on First Run**: The first time you analyze a product, the application will download several large machine learning models (`BERT`, `BART`, `ATEPC`). This process can take several minutes and requires a stable internet connection. Subsequent analyses will be much faster as the models will be loaded from the local cache.

## Project Structure

```
.
├── AspectExtraction.py      # Extracts aspects from reviews using PyABSA
├── ContextualizedWriting.py # Generates human-readable reports with Gemini API
├── OpinionSummarization.py  # Creates simple summaries with BART
├── SentimentPrediction.py   # Analyzes sentiment with a BERT model
├── WebScraper.py            # Scrapes reviews from Flipkart with Selenium
├── main.py                  # Main Flask application and pipeline orchestrator
├── requirements.txt         # Project dependencies
├── static/                  # Frontend assets
│   ├── script.js            # Handles API calls and dynamic content
│   └── style.css            # Styling for the web page
└── templates/
    └── index.html           # Main HTML file for the UI
```
