document.addEventListener('DOMContentLoaded', () => {
    const convertBtn = document.getElementById('convert-btn');
    const urlInput = document.getElementById('gemini-url');
    const messageArea = document.getElementById('message-area');
    const btnText = document.getElementById('btn-text');
    const btnLoader = document.getElementById('btn-loader');

    // Function to handle the conversion process
    const handleConversion = async () => {
        const url = urlInput.value.trim();

        // 1. Basic client-side validation
        if (!url) {
            messageArea.textContent = 'Please paste a URL first.';
            return;
        }
        if (!url.startsWith('https://g.co/gemini/share/')) {
            messageArea.textContent = 'Please enter a valid Gemini share link.';
            return;
        }

        // 2. Update UI to show processing state
        messageArea.textContent = '';
        btnText.classList.add('hidden');
        btnLoader.classList.remove('hidden');
        convertBtn.disabled = true;

        try {
            // 3. Send the URL to the backend API
            const response = await fetch('/convert', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url: url }),
            });

            // 4. Handle the response
            if (response.ok) {
                // If successful, the response is the PDF file
                const blob = await response.blob();
                const downloadUrl = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = downloadUrl;

                // Extract filename from response headers if available, otherwise create one
                const disposition = response.headers.get('Content-Disposition');
                let filename = 'gemini-chat.pdf';
                if (disposition && disposition.indexOf('attachment') !== -1) {
                    const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
                    const matches = filenameRegex.exec(disposition);
                    if (matches != null && matches[1]) {
                        filename = matches[1].replace(/['"]/g, '');
                    }
                }
                
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(downloadUrl);
                a.remove();
                messageArea.textContent = 'Download started successfully!';
                messageArea.classList.remove('text-red-600');
                messageArea.classList.add('text-green-600');

            } else {
                // If the server returned an error (4xx, 5xx)
                const errorData = await response.json();
                messageArea.textContent = `Error: ${errorData.error || 'Something went wrong.'}`;
                messageArea.classList.add('text-red-600');
                messageArea.classList.remove('text-green-600');
            }

        } catch (error) {
            // Handle network errors (e.g., server is down)
            console.error('Fetch error:', error);
            messageArea.textContent = 'A network error occurred. Is the server running?';
        } finally {
            // 5. Reset UI back to normal state
            btnText.classList.remove('hidden');
            btnLoader.classList.add('hidden');
            convertBtn.disabled = false;
        }
    };

    convertBtn.addEventListener('click', handleConversion);
});
