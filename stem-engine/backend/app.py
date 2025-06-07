from flask import Flask, request, jsonify
import logging
import os

# Basic logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# Define the base directory of the application (stem-engine)
# This assumes app.py is in stem-engine/backend/
APP_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ASSETS_DIR = os.path.join(APP_BASE_DIR, 'assets', 'audio_placeholders')

@app.route('/generate_stem', methods=['POST'])
def generate_stem():
    try:
        data = request.get_json()
        if not data:
            logging.error("No JSON data received or content type not application/json")
            return jsonify({"error": "Invalid request. JSON data expected."}), 400

        logging.info(f"Received /generate_stem request: {data}")

        prompt = data.get('prompt')
        genre = data.get('genre')
        # ... extract other parameters like bpm, key, bars as needed

        if not prompt:
            logging.warning("Missing 'prompt' in request data.")
            return jsonify({"error": "Missing 'prompt' in request data."}), 400

        # --- Mocked AI Sandwich Logic (Phase 1) ---
        selected_filename = "default_loop.wav" # A default
        if "drum" in prompt.lower():
            selected_filename = "placeholder_drums.wav"
        elif "synth" in prompt.lower():
            selected_filename = "placeholder_synth.wav"
        elif "bass" in prompt.lower():
            selected_filename = "placeholder_bass.wav"

        # This path is relative to the stem-engine directory
        relative_path_from_root = os.path.join('assets', 'audio_placeholders', selected_filename)
        # This is the absolute path on the server where the backend can find the file
        absolute_path_on_server = os.path.join(ASSETS_DIR, selected_filename)

        if not os.path.exists(absolute_path_on_server):
            logging.error(f"Placeholder audio file not found: {absolute_path_on_server}")
            return jsonify({
                "error": "Selected audio file not found on server.",
                "selected_audio_filename": selected_filename,
                "tried_path": absolute_path_on_server
            }), 404 # Not found

        logging.info(f"Mocked generation: Selected '{selected_filename}' for prompt '{prompt}'")

        response_data = {
            "message": "Stem generation request processed (mocked response)",
            "prompt_received": prompt,
            "genre_received": genre, # Added for clarity
            "selected_audio_filename": selected_filename,
            # This path should be interpretable by the bot, assuming it knows the project structure.
            # It's relative to the project root.
            "audio_file_path_from_root": relative_path_from_root
        }
        return jsonify(response_data), 200

    except Exception as e:
        logging.error(f"Error processing /generate_stem: {e}", exc_info=True)
        return jsonify({"error": "An internal server error occurred."}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    host = os.getenv("FLASK_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_PORT", 5000))
    # debug=True is for development only, ensure it's False in production
    app.run(host=host, port=port, debug=os.getenv("FLASK_DEBUG", "True").lower() == "true")
