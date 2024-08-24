// script.js
document.getElementById('queryForm').addEventListener('submit', function(event) {
    event.preventDefault();

    // Show "Please wait..." in the response area
    document.getElementById('response').innerHTML = `
        <p>Just a sec ⏱️</p>
    `;

    const video_id = document.getElementById('video_id').value;
    const user_question = document.getElementById('user_question').value;

    fetch('https://youtube-rag-k3w6.onrender.com/process', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ video_id, user_question })
    })
    .then(response => response.json())
    .then(data => {
        // Clear the "Please wait..." placeholder
        document.getElementById('response').innerHTML = '';

        if (data.youtube_link && data.answer) {
            document.getElementById('response').innerHTML = `
                <p><strong>RAG Answer 🧠</strong></p>
                <p>${data.answer}</p>
                <p><strong>View on YouTube ↗️</strong> <a href="${data.youtube_link}" target="_blank">${data.youtube_link}</a></p>
            `;

            // Update the iframe source URL with the start parameter
            const iframeSrc = `https://www.youtube.com/embed/${video_id}?start=${data.start}`;

            // Log the iframe source URL to the console
            console.log('Iframe Source URL:', iframeSrc);

            document.getElementById('videoContainer').innerHTML = `
                <iframe src="${iframeSrc}" allowfullscreen></iframe>
            `;
        } else {
            document.getElementById('response').innerHTML = `
                <p><strong>Error:</strong> ${data.error}</p>
            `;
        }
    })
    .catch(error => {
        // Clear the "Please wait..." placeholder
        document.getElementById('response').innerHTML = '';

        document.getElementById('response').innerHTML = `
            <p><strong>Error:</strong> ${error.message}</p>
        `;
    });
});
