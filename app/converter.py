# app/converter.py
import requests
from bs4 import BeautifulSoup
import logging
from io import BytesIO
from xhtml2pdf import pisa
import time # <-- Import time for potential simple waits

# --- NEW IMPORTS FOR SELENIUM ---
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Set up basic logging
logging.basicConfig(level=logging.INFO)


# --- THIS IS THE UPDATED FUNCTION ---
def scrape_gemini_chat(url: str) -> str:
    """
    Fetches the Gemini share link using a real browser to handle JavaScript,
    and extracts the chat content into a clean HTML string.
    """
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")  # Run browser in the background
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        # Automatically download and manage the correct browser driver
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

        logging.info(f"Fetching URL with Selenium: {url}")
        driver.get(url)

        # --- THIS IS THE CRUCIAL PART ---
        # Wait up to 20 seconds for elements with the class 'message-content' to appear.
        # This is a more stable class name often used for the containers of both user/model text.
        # UPDATE THIS CLASS NAME IF GEMINI CHANGES IT.
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "message-content")))
        
        # Give it an extra moment just in case, for all content to render.
        time.sleep(1)

        # Now get the page source AFTER JavaScript has loaded everything
        html_source = driver.page_source
        driver.quit() # Close the browser

        soup = BeautifulSoup(html_source, 'html.parser')

        # NOTE: Gemini's structure has changed. 'user-query' and 'model-response-text' are the
        # correct classes to look for inside the message containers as of late 2025.
        # chat_elements = soup.find_all(class_=['user-query', 'model-response-text'])
        chat_elements = soup.find_all(class_=['query-text', 'message-content'])

        
        if not chat_elements:
            raise ValueError("Could not find chat content on the page. The website structure may have changed.")

        # The rest of the function remains the same...
        html_content = f"""
        <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    /* Your CSS styles remain here... */
                    @page {{ size: A4; margin: 1.5cm; }}
                    body {{ font-family: sans-serif; line-height: 1.6; color: #333; }}
                    h1 {{ text-align: center; color: #1a237e; border-bottom: 2px solid #e0e0e0; padding-bottom: 10px; }}
                    h3 {{ margin-top: 0; margin-bottom: 10px; color: #0d47a1; }}
                    .user-prompt {{ background-color: #e3f2fd; border-left: 5px solid #2196f3; padding: 10px 15px; margin-bottom: 1.5em; border-radius: 0 5px 5px 0; }}
                    .model-response {{ background-color: #f1f8e9; padding: 10px 15px; margin-bottom: 1.5em; border-radius: 5px; }}
                    pre {{ background-color: #2d2d2d; color: #f2f2f2; padding: 1em; border-radius: 5px; white-space: pre-wrap; word-wrap: break-word; }}
                    code {{ font-family: 'Courier New', Courier, monospace; }}
                </style>
                <title>Gemini Chat Export</title>
            </head>
            <body>
                <h1>Gemini Chat Export</h1>
                <p><strong>Source:</strong> <a href="{url}">{url}</a></p>
                <hr>
        """

        for element in chat_elements:
            # This logic correctly differentiates between the user and the model
            if 'user-query' in element.get('class', []):
                html_content += '<div class="user-prompt">'
                html_content += '<h3>You</h3>'
            else:
                html_content += '<div class="model-response">'
                html_content += '<h3>Gemini</h3>'
            
            html_content += element.decode_contents()
            html_content += '</div>'

        html_content += "</body></html>"
        return html_content

    except Exception as e:
        logging.error(f"An error occurred during scraping: {e}")
        # Clean up the driver if it's still running
        if 'driver' in locals() and driver:
            driver.quit()
        raise

# The create_pdf_from_html function remains EXACTLY THE SAME
def create_pdf_from_html(html_string: str) -> bytes:
    # ... (no changes here) ...
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html_string.encode("UTF-8")), result)
    if pdf.err:
        raise Exception("Error converting HTML to PDF")
    pdf_bytes = result.getvalue()
    result.close()
    return pdf_bytes