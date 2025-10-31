# AI-Powered Review Summarizer

This project scrapes reviews for a given product URL from Flipkart, analyzes them to extract key aspects and sentiment, and generates a human-readable summary using the Gemini API. This version is a web application built with Flask.

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

3.  **Set up Environment Variables**
    Create a `.env` file in the root directory and add your Google Gemini API key:
    Also paste same API key in ContextualWriting.py and main.py
    ```
    GEMINI_API_KEY="YOUR_API_KEY"
    ```

5.  **Run the App**
    ```bash
    flask run
    ```
    Or
    ```bash
    python app.py
    ```

Open your browser to `http://127.0.0.1:5000/`, paste a Flipkart product URL, and generate your summary.

**Note**: For First time it will be quit slow due to all models are being downloaded. If you are running this on a CPU, it may take some time to run the heavy ML models . Please be patient. I have added enough debug statements so if anything goes wrong, check the console where you ran the application.
