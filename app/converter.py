# app/converter.py

import logging
from time import sleep

from bs4 import BeautifulSoup
import pdfkit  # <-- CHANGED: Replaced xhtml2pdf with pdfkit

# --- SELENIUM IMPORTS ---
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Set up basic logging to see the progress
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# --- HELPER FUNCTION TO CLEAN HTML (NO CHANGES) ---
def process_and_clean_model_response(block_soup: BeautifulSoup) -> str:
    """
    Cleans and simplifies the HTML from a model response block before PDF conversion.
    (This function remains unchanged.)
    """
    # Remove empty paragraphs which cause large vertical gaps
    for p_tag in block_soup.find_all('p'):
        if not p_tag.get_text(strip=True):
            p_tag.decompose()

    # Simplify list items by removing nested <p> tags but keeping their content
    for li_tag in block_soup.find_all('li'):
        for p_tag in li_tag.find_all('p'):
            p_tag.unwrap()

    # Find complex Katex (LaTeX) spans, extract their text, and replace them
    for katex_span in block_soup.find_all('span', class_='katex'):
        formula_text = katex_span.get_text()
        simple_formula_tag = BeautifulSoup(f'<span class="formula">{formula_text}</span>', 'html.parser').span
        katex_span.replace_with(simple_formula_tag)

    return block_soup.decode_contents()


# --- MAIN SCRAPING AND HTML GENERATION FUNCTION (NO CHANGES) ---
def scrape_gemini_chat(url: str) -> str:
    """
    Fetches a Gemini share link using Selenium, waits for dynamic content,
    and extracts the chat into a clean HTML string for PDF conversion.
    (This function remains unchanged.)
    """
    options = ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=options)
    
    html_parts = []
    try:
        logging.info(f"Fetching URL: {url}")
        driver.get(url)

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "message-content"))
        )
        
        sleep(1)

        logging.info("Page content loaded. Parsing with BeautifulSoup.")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        message_blocks = soup.find_all(class_=["horizontal-container", "message-content"])

        if not message_blocks:
            raise ValueError("Could not find any chat content. Class names 'horizontal-container' or 'message-content' may be incorrect.")

        html_parts.append(f"""
    <html>
    <head>
    <meta charset="UTF-8" />
    <title>Gemini Chat Export (Improved Dark Theme)</title>
    <style>
      /* A modern, refined dark theme color palette */
      @page {{
        size: A4;
        margin: 1cm;
        background-color: #0d1117;
      }}

      body {{
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI",
          Roboto, Oxygen, Ubuntu, Cantarell, "Open Sans", "Helvetica Neue",
          sans-serif;
        line-height: 1.6;
        background-color: #0d1117; /* Deep charcoal background */
        color: #c9d1d9; /* Soft, light gray text */
      }}

      h1 {{
        text-align: center;
        color: #58a6ff; /* Bright, clear blue for heading */
        border-bottom: 2px solid #30363d; /* Muted gray border */
        padding-bottom: 10px;
        margin-bottom: 20px;
      }}

      .user-prompt {{
        background-color: #1c2128; /* Slightly lighter gray for user prompt */
        border-left: 5px solid #3fb950; /* A vibrant green for accent */
        padding: 15px 20px;
        margin-bottom: 0.75rem;
        border-radius: 0 8px 8px 0;
      }}

      .model-response {{
        background-color: #161b22; /* Darker gray for model response */
        padding: 15px 20px;
        margin-bottom: 0.75rem;
        border-radius: 8px;
        word-wrap: break-word;
        page-break-inside: avoid;
        display: inline-block;
        width: 100%;
        box-sizing: border-box;
      }}

      p.role {{
        font-weight: bold;
        color: #8b949e; /* Muted gray for the role text (You/Gemini) */
        margin: 0 0 8px 0;
      }}

      .source-link a {{
        color: #58a6ff; /* Same bright blue as the heading for links */
        text-decoration: none;
      }}
      .source-link a:hover {{
        text-decoration: underline;
      }}

      hr {{
        border: none;
        border-top: 1px solid #30363d; /* Consistent muted gray for horizontal rule */
        margin-bottom: 25px;
      }}

      b,
      strong {{
        color: #adbac7; /* Slightly brighter text for bolded elements */
      }}
    </style>
  </head>
  <body>
    <h1>Gemini Chat Export</h1>
    <p class="source-link"><strong>Source:</strong><a href="{url}">{url}</a></p><hr />
        """)

        for block in message_blocks:
            block_classes = block.get('class', [])
            
            if 'horizontal-container' in block_classes:
                html_parts.append('<div class="user-prompt">')
                html_parts.append('<p class="role">You</p>')
                prompt_text = block.get_text(separator='\n').strip()
                prompt_html = prompt_text.replace('\n', '<br>')
                html_parts.append(f"<div>{prompt_html}</div>")
                html_parts.append('</div>')
            
            elif 'message-content' in block_classes:
                html_parts.append('<div class="model-response">')
                html_parts.append('<p class="role">Gemini</p>')
                cleaned_html = process_and_clean_model_response(block)
                html_parts.append(cleaned_html)
                html_parts.append('</div>')
        
        html_parts.append("</body></html>")
        
        final_html = "".join(html_parts)
        
        with open("debug_output.html", "w", encoding="utf-8") as f:
            f.write(final_html)
        logging.info("Saved final, cleaned HTML to debug_output.html")

        return final_html

    except TimeoutException:
        logging.error(f"Timeout: The page at {url} took too long to load.")
        raise
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        raise
    finally:
        if 'driver' in locals():
            logging.info("Closing Selenium browser.")
            driver.quit()


# --- THIS IS THE CONVERTED PDF CREATION FUNCTION ---
def create_pdf_from_html(html_string: str) -> bytes:
    """
    Converts a string of HTML into PDF bytes using pdfkit.
    """
    if not html_string:
        raise ValueError("Cannot create PDF from empty HTML string.")
    
    # Options for the PDF output. These mirror the @page CSS rule.
    options = {
        'page-size': 'A4',
        'margin-top': '1.5cm',
        'margin-right': '1.5cm',
        'margin-bottom': '1.5cm',
        'margin-left': '1.5cm',
        'encoding': "UTF-8",  # for handling special characters
        'enable-local-file-access': None # Allows loading of local files if needed (safer)
    }
    
    try:
        logging.info("Starting PDF conversion with pdfkit.")
        # The 'False' argument tells pdfkit to return the PDF as a variable (bytes)
        # instead of writing it to a file on disk.
        pdf_bytes = pdfkit.from_string(html_string, False, options=options)
        logging.info("PDF conversion successful.")
        return pdf_bytes
        
    except OSError as e:
        # This error is commonly raised if wkhtmltopdf is not installed or not in the PATH.
        logging.error(f"pdfkit error: {e}")
        logging.error("Ensure 'wkhtmltopdf' is installed and in your system's PATH.")
        raise Exception("PDF generation failed. The 'wkhtmltopdf' tool may be missing.")

