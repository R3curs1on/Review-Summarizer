# ====================================================================
# File: WebScraper.py
# ====================================================================

# --- Setup & Installation for Portability ---
#
# 1. **Install Dependencies:**
#    This script relies on Selenium and webdriver-manager.
#
#    pip install selenium webdriver-manager
#
# 2. **Google Chrome Required:**
#    The user MUST have the Google Chrome browser installed on their system.
#    'webdriver-manager' will handle finding the driver for it.
#
# 3. **Execution:**
#    python FlipkartScraper.py

import time
import os
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, TimeoutException
 
def setup_driver():
    """Sets up the Selenium WebDriver in headless / quiet mode (no visible browser)."""
    options = webdriver.ChromeOptions()

    # Headless and stability flags
    options.add_argument("--headless=new") 
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Quiet / reduce logging
    options.add_argument("--log-level=3")
    options.add_argument("--silent")
    options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # Custom user agent
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )

    # Reduce webdriver-manager noise
    os.environ["WDM_LOG_LEVEL"] = "0"

    try:
        # Use webdriver-manager to automatically get the correct chromedriver
        # Send chromedriver logs to os.devnull to keep the console clean
        service = Service(ChromeDriverManager().install(), log_path=os.devnull)
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as e:
        print(f"Error: Could not start headless Chrome. {e}")
        print("Please ensure you have Google Chrome installed on this system.")
        return None

    return driver
 
def extract_review_text(container):
    """
    Tries multiple selectors to robustly find the review text.
    This provides fallbacks if class names or structure change.
    """
    review_text = None

    # --- Selector 1: Primary (Direct & Stable Class Name) ---
    try:
        element = container.find_element(By.CSS_SELECTOR, "div.ZmyHeo")
        review_text = element.text
        if review_text: return review_text
    except NoSuchElementException:
        pass # If not found, proceed to the next selector

    # --- Selector 2: Fallback (Structural Position via XPath) ---
    # The review text is consistently inside the second div with class='row'.
    try:
        # The '.' at the start of the XPath is crucial, it means search within this 'container' element.
        element = container.find_element(By.XPATH, ".//div[@class='row'][2]/div/div")
        review_text = element.text
        if review_text: return review_text
    except NoSuchElementException:
        pass # If not found, proceed to the final fallback

    # --- Selector 3: Final Fallback (Content-based) ---
    # Finds the 'READ MORE' span, then gets the text from its parent div.
    try:
        element = container.find_element(By.XPATH, ".//span[contains(text(), 'READ MORE')]/parent::div")
        review_text = element.text
        if review_text: return review_text
    except NoSuchElementException:
        return None # Return None if all selectors failed for this container

    return review_text

def scrape_flipkart_reviews(url: str, max_pages: int = 10):
    """
    Scrapes reviews using a robust, multi-layered selector strategy.
    
    Args:
        url (str): The URL of the *product page*.
        max_pages (int): The maximum number of review pages to scrape (default 10).
    """
    print("🚀 Starting the scraper...")
    driver = setup_driver()
    if driver is None: 
        print("❌ Scraper setup failed. Exiting.")
        return []

    wait = WebDriverWait(driver, 10)

    try:
        # 1. Go to the product page and find the initial reviews page URL
        driver.get(url)
        print(f"✅ Navigated to product page...")
        all_reviews_link_element = wait.until(
            EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/product-reviews/')]"))
        )
        reviews_page_url = all_reviews_link_element.get_attribute('href')
        base_review_url = reviews_page_url.split('&page=')[0]
        print(f"✅ Found base review URL.")

        # 2. Scrape the total page count
        driver.get(f"{base_review_url}&page=1")
        total_pages = 1
        try:
            page_info_span = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div._1G0WLw span")))
            page_text = page_info_span.text
            # Example text: "Page 1 of 1,234"
            total_pages = int(page_text.split(' of ')[-1].replace(',', ''))
            print(f"🎯 Found {total_pages} total pages of reviews.")
        except Exception as e:
            print(f"⚠️ Could not parse page count, defaulting to 1 page. Error: {e}")

        # 3. Main scraping loop
        reviews_scraped = []
        
        # Determine pages to scrape: min of (user_limit, total_pages_found)
        # Ensure we always scrape at least page 1
        pages_to_scrape = max(1, min(total_pages, max_pages))
        print(f"ℹ️ Will scrape a maximum of {pages_to_scrape} pages.")

        for page_count in range(1, pages_to_scrape + 1):
            current_url = f"{base_review_url}&page={page_count}"
            print(f"\n📄 Scraping page {page_count}/{pages_to_scrape}...")
            driver.get(current_url)

            try:
                # Wait for the main review blocks to be present.
                review_containers = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.cPHDOP.col-12-12")))

                page_reviews_count = 0
                for container in review_containers:
                    # Use our robust function to get the text
                    full_text = extract_review_text(container)

                    if full_text:
                        # Clean the "READ MORE" text and add to our list
                        cleaned_text = full_text.replace("READ MORE", "").strip()
                        if cleaned_text:
                            reviews_scraped.append(cleaned_text)
                            page_reviews_count += 1

                print(f"    👍 Scraped {page_reviews_count} reviews from this page. Total so far: {len(reviews_scraped)}")
                time.sleep(1) # Be polite to the server

            except TimeoutException:
                print(f"    ⚠️ Timeout waiting for review containers on page {page_count}. Skipping.")
            except Exception as e:
                print(f"    ⚠️ An unexpected error occurred on page {page_count}: {e}")

        # Remove duplicates while preserving order
        unique_reviews = list(dict.fromkeys(reviews_scraped))
        return unique_reviews

    except Exception as e:
        print(f"❌ An unexpected error occurred in the main process: {e}")
        return []
    finally:
        if driver:
            driver.quit()
        print("\n✅ Browser closed. Scraping finished.")
 

if __name__ == "__main__":
    # --- Configuration ---
    # Paste the URL of the *product page*, not the "all reviews" page.
    product_url = "https://www.flipkart.com/zebronics-pspk9-county-built-in-fm-radio-aux-input-3-w-bluetooth-speaker/p/itm60db34332d5ee?pid=ACCFKTGTVDTHF7GQ"
    
    # Set the maximum number of pages you want to scrape.
    MAX_PAGES_TO_SCRAPE = 10 
    
    # Set the output file name
    OUTPUT_FILE = "scraped_reviews.txt"
    # --- End Configuration ---

    all_reviews = scrape_flipkart_reviews(product_url, max_pages=MAX_PAGES_TO_SCRAPE)

    if all_reviews:
        print(f"\n{'=' * 70}\n🎉 SCRAPING COMPLETE: Found {len(all_reviews)} unique reviews in total\n{'=' * 70}")
        
        # Save to file
        try:
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                for i, review_text in enumerate(all_reviews, 1):
                    # Save each review on its own line
                    f.write(f"{review_text}\n")
            print(f"💾 Successfully saved {len(all_reviews)} reviews to '{OUTPUT_FILE}'")
        except IOError as e:
            print(f"❌ Error saving file: {e}")
            
    else:
        print("\n❌ SCRAPING COMPLETE: No reviews were found.")
