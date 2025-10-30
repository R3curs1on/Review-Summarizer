# AI-Powered Review Summarizer

This project scrapes reviews for a given product URL from Flipkart, analyzes them to extract key aspects and sentiment, and generates a human-readable summary using the Gemini API.

## How to Run

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/R3curs1on/Review-Summarizer.git
    cd Review-Summarizer
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Add API Key**
    Open `app.py` and paste your Google Gemini API key into the `gemini_api_key` variable.

4.  **Run the App**
    ```bash
    streamlit run app.py
    ```

Open your browser to the local URL provided by Streamlit, paste a Flipkart product URL, and generate your summary.

**Note** : If you are using on cpu then it will take time to run those heavy ml models so please be patient . I have added enough debug statements if anything goes wrong check console ( where you run app.py )  .
