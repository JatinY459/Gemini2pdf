# app/routes.py
from flask import render_template, request, jsonify, Response  # Ensure render_template is imported
from app import app
from app.converter import scrape_gemini_chat, create_pdf_from_html

@app.route('/')
def index():
    """Renders the main page."""
    # This line tells Flask to find 'index.html' in your 'templates' folder and show it.
    return render_template('index.html')

# ... the rest of your /convert route stays the same ...
@app.route('/convert', methods=['POST'])
def convert_url_to_pdf():
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({'error': 'URL not provided in request body.'}), 400

    url = data['url']
    if not url.startswith('https://g.co/gemini/share/'):
        return jsonify({'error': 'Invalid Gemini share URL.'}), 400

    try:
        html_content = scrape_gemini_chat(url)
        pdf_bytes = create_pdf_from_html(html_content)
        filename = f"gemini-chat-{url.split('/')[-1]}.pdf"

        return Response(
            pdf_bytes,
            mimetype='application/pdf',
            headers={'Content-Disposition': f'attachment;filename={filename}'}
        )

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'An unexpected error occurred on the server.'}), 500

