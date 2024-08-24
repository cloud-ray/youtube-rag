from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from embed_upload import process_video_transcript
from retrieve_create import generate_youtube_link
import logging

app = Flask(__name__)
CORS(app, resources={r"/process": {"origins": ["http://localhost:8080", "http://127.0.0.1:8080"]}})
# CORS(app, resources={r"/*": {"origins": "*"}})
# CORS(app)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_request():
    data = request.json
    video_id = data.get('video_id')
    user_question = data.get('user_question')

    if not video_id or not user_question:
        return jsonify({"error": "Both 'video_id' and 'user_question' are required."}), 400

    try:
        # Step 1: Download, embed, and upload to ChromaDB
        vector_store = process_video_transcript(video_id)
        if vector_store is None:
            logger.error(f"Failed to process video_id: {video_id}.")
            return jsonify({"error": f"Failed to process video_id: {video_id}."}), 500

        # Step 2: Use the chain to query and generate a timestamped YouTube link
        result = generate_youtube_link(user_question, video_id)

        # Ensure result contains the expected keys
        if 'youtube_link' in result and 'answer' in result:
            return jsonify(result)
        else:
            logger.error("Unable to generate YouTube link or retrieve answer.")
            return jsonify({"error": "Unable to generate YouTube link or retrieve answer."}), 500

    except Exception as e:
        logger.exception("An error occurred while processing the request.")
        return jsonify({"error": "An internal error occurred."}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
