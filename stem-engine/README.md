# Stem Engine MVP

Stem Engine is a community-first, AI-powered tool designed to generate high-quality, royalty-free musical stems from natural language prompts. This project aims to build the Minimum Viable Product (MVP) for this tool.

## Overview

The primary interface for Stem Engine will be a Discord bot. Users will interact with the bot using commands to generate and refine musical stems. The backend will consist of an "AI Sandwich" architecture:

1.  **LLM (Language Model):** To interpret natural language prompts.
2.  **Orchestration Engine:** Proprietary logic to translate creative requests into technical parameters for music generation models.
3.  **Generators:** Specialized music generation models.

## Project Structure

-   `discord_bot/`: Contains the Python code for the Discord bot.
-   `backend/`: Contains the Python code for the backend Flask service, which will host the AI Sandwich.
-   `assets/`: Contains static assets, such as placeholder audio files for initial development.
    - `assets/audio_placeholders/`: Stores sample .wav files for testing the pipeline.
-   `README.md`: This file.

## MVP Features (High-Level)

-   `/generate` command: Users provide a text prompt and optional parameters (genre, BPM, key, bars) to generate a musical stem.
-   `/refine` command: Users can request iterative changes to a previously generated stem.
-   `#gallery` channel: A Discord channel where users can share their favorite creations.

## Getting Started

To run the Stem Engine MVP, you'll need to set up and run the backend service and the Discord bot separately.

### Environment Variables

Ensure you have the following environment variables set. You can use a `.env` file (loaded by a library like `python-dotenv` in your local environment, not committed to git) or set them directly in your shell.

**For the Backend (`stem-engine/backend/app.py`):**

-   `FLASK_HOST`: The host address for the Flask app (e.g., `127.0.0.1`). Defaults to `127.0.0.1`.
-   `FLASK_PORT`: The port for the Flask app (e.g., `5000`). Defaults to `5000`.
-   `FLASK_DEBUG`: Set to `True` for development mode, `False` for production. Defaults to `True`.

**For the Discord Bot (`stem-engine/discord_bot/bot.py`):**

-   `DISCORD_BOT_TOKEN` (Required): Your Discord bot token.
-   `BACKEND_URL`: The full URL for the backend's `/generate_stem` endpoint (e.g., `http://127.0.0.1:5000/generate_stem`). Defaults to `http://127.0.0.1:5000/generate_stem`.

### Running the Services

1.  **Backend Service:**
    -   Navigate to the `stem-engine/backend` directory.
    -   Install dependencies: `pip install -r requirements.txt`
    -   Run the Flask app: `python app.py`
    -   You should see output indicating the Flask server is running (e.g., `* Running on http://127.0.0.1:5000/`).

2.  **Discord Bot:**
    -   Navigate to the `stem-engine/discord_bot` directory.
    -   Install dependencies: `pip install -r requirements.txt`
    -   Ensure your `DISCORD_BOT_TOKEN` (and `BACKEND_URL` if not default) environment variable is set.
    -   Run the bot: `python bot.py`
    -   You should see output indicating the bot has logged in (e.g., `Bot logged in as YourBotName`).

### End-to-End Test Procedure

1.  Ensure both the backend service and the Discord bot are running as described above.
2.  Invite your Discord bot to a server where you have permissions to use slash commands.
3.  In any channel the bot can access, type the `/generate` command. For example:
    -   `/generate prompt:a funky drum beat`
    -   `/generate prompt:a sad synth melody genre:ambient bpm:120 key:Cm bars:8`
4.  **Expected Outcome:**
    -   The bot should initially respond with an ephemeral message like "Processing your request...".
    -   After a moment, the bot should send a follow-up message containing:
        -   Text similar to "Here's your generated stem for..."
        -   An attached audio file (e.g., `placeholder_drums.wav` if your prompt contained "drum").
    -   Check the console logs for both the backend and the bot for any errors and to see the flow of information.
    -   The backend console should show the JSON request it received.
    -   The bot console should show the JSON response it received from the backend and messages about file paths.
