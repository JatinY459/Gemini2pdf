# First, ensure you have the library installed:
# pip install xhtml2pdf

from xhtml2pdf import pisa

def convert_html_to_pdf(source_html_path, output_pdf_path):
    """
    Converts a local HTML file to a PDF file.

    :param source_html_path: The full path to the source HTML file.
    :param output_pdf_path: The full path for the output PDF file.
    :return: True if conversion was successful, False otherwise.
    """
    # Open the source HTML file in read mode
    with open(source_html_path, "r", encoding="UTF-8") as source_file:
        source_html = source_file.read()

    # Open the destination PDF file in write-binary mode
    with open(output_pdf_path, "w+b") as result_file:
        # Convert HTML to PDF
        pisa_status = pisa.CreatePDF(
            source_html,                # the HTML to convert
            dest=result_file            # file handle to receive result
        )

    # Return the success status
    if pisa_status.err:
        print(f"Error converting HTML to PDF: {pisa_status.err}")
        return False
    else:
        print(f"Successfully converted {source_html_path} to {output_pdf_path}")
        return True

# --- --- --- USAGE EXAMPLE --- --- ---
if __name__ == "__main__":
    # Define the input and output file paths
    # Ensure 'input.html' exists in the same directory as this script.
    html_file = "debug_output.html"
    pdf_file = "output.pdf"

    # Call the conversion function
    convert_html_to_pdf(html_file, pdf_file)