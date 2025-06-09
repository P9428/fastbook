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

### Additional Backend Environment Variables for Claude LLM

-   `ANTHROPIC_API_KEY` (Required for LLM): Your API key for the Anthropic Claude LLM.
-   `CLAUDE_MODEL_NAME`: The specific Claude model you want to use (e.g., `claude-3-opus-20240229`). Defaults to `claude-3-opus-20240229` if not set.

### Additional Backend Environment Variables for Supabase

-   `SUPABASE_URL` (Required for Supabase integration): The URL of your Supabase project.
-   `SUPABASE_KEY` (Required for Supabase integration): The `service_role` key for your Supabase project. This key has elevated privileges and should be kept secret, used only on the backend.

**For the Discord Bot (`stem-engine/discord_bot/bot.py`):**

-   `DISCORD_BOT_TOKEN` (Required): Your Discord bot token.
-   `BACKEND_URL`: The full URL for the backend's `/generate_stem` endpoint (e.g., `http://127.0.0.1:5000/generate_stem`). Defaults to `http://127.0.0.1:5000/generate_stem`.
-   `BACKEND_URL_GENERATE`: (Alternative to `BACKEND_URL` if more specific) URL for the `/generate_stem` endpoint. Defaults to `http://127.0.0.1:5000/generate_stem`.
-   `BACKEND_URL_REFINE`: URL for the `/refine_stem` endpoint. Defaults to `http://127.0.0.1:5000/refine_stem`.


### Manual Supabase Project Setup (Required for full functionality)

Before running the backend with Supabase features enabled, you need to:

1.  **Create a Supabase Project:** Go to [supabase.com](https://supabase.com/) and create a new project.
2.  **Create 'generations' Table:** In the Supabase SQL Editor or Table Editor, create a table named `generations`. The specific schema expected by the application will be defined in backend code comments (e.g., in `supabase_client_init.py` or near its usage in `app.py`). Refer to these comments for column names and types.
3.  **Create 'stems' Storage Bucket:** In the Supabase Storage section, create a new bucket.
    *   **Name:** `stems` (or ensure this matches the bucket name used in backend code, e.g., in `storage_handler.py`).
    *   **Public Access:** For this MVP, it's simplest to make this bucket public so that the URLs returned by Supabase for uploaded files are directly accessible. You can configure more granular access policies later if needed. Ensure "Public access" is enabled for the bucket, or set up appropriate read access policies for the files.

### Running the Services

1.  **Backend Service:**
    -   Navigate to the `stem-engine/backend` directory.
    -   Install dependencies: `pip install -r requirements.txt`
    -   Run the Flask app: `python app.py`
    -   You should see output indicating the Flask server is running (e.g., `* Running on http://127.0.0.1:5000/`).

2.  **Discord Bot:**
    -   Navigate to the `stem-engine/discord_bot` directory.
    -   Install dependencies: `pip install -r requirements.txt`
    -   Ensure your `DISCORD_BOT_TOKEN` (and relevant `BACKEND_URL`s) environment variable is set.
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

## Phase 3: LLM Integration Testing and Prompt Refinement

After setting up and running the services with the new LLM integration (Phase 3), the primary goal is to test how well the Claude LLM interprets user prompts and to refine the system prompt in `backend/app.py` for better structured output.

### Testing Focus:

1.  **JSON Structure Adherence:**
    *   Verify that Claude's output (displayed by the bot) strictly adheres to the JSON format defined in `CLAUDE_SYSTEM_PROMPT` in `backend/app.py`.
    *   Check for any extraneous text outside the main JSON object.
    *   Ensure correct use of `null` for empty scalar fields (like `bpm_specified` if not provided) and empty arrays `[]` for list-type fields (like `genre_tags` if none are applicable).

2.  **Accuracy of Interpretation:**
    *   **`user_request` block:** Does this accurately reflect the parameters sent by the user?
    *   **`interpretation` block:**
        *   `primary_instrument_description`: Is it a sensible description of the main sound/instrument?
        *   `genre_tags`: Are the tags relevant? Does it correctly pick up user-specified genre and infer others?
        *   `mood_descriptors`: Do these capture the vibe of the prompt?
        *   `tempo_bpm`, `musical_key`, `loop_length_bars`: Are user-specified values correctly copied? If not specified, is the inference reasonable, or is it correctly `null`?
        *   `rhythmic_elements`, `melodic_harmonic_elements`, `sound_design_details`: Is relevant information from the prompt correctly categorized here?
        *   `energy_level`: Is the inference appropriate?
        *   `additional_notes`: What kind of information lands here? Is it useful?

3.  **Handling of Diverse Prompts:**
    *   Test with simple prompts (e.g., "kicking drum machine").
    *   Test with complex prompts specifying multiple attributes (e.g., "a melancholic, ambient synth pad in C minor at 60 bpm for 8 bars with lots of reverb").
    *   Test with vague or ambiguous prompts to see how the LLM handles them.
    *   Test prompts that *don't* specify genre, BPM, key, or bars to check inference capabilities.
    *   Test with prompts that might try to "break" the JSON format (though the system prompt strongly discourages this).

### Prompt Refinement Process:

1.  **Run a Test:** Use the Discord bot's `/generate` command with a test prompt.
2.  **Observe Output:** Carefully examine the JSON output displayed by the bot.
3.  **Identify Issues:** Note any deviations from the desired structure, inaccuracies in interpretation, or areas where the LLM seems confused.
4.  **Modify System Prompt:**
    *   Open `stem-engine/backend/app.py`.
    *   Edit the `CLAUDE_SYSTEM_PROMPT` string. You might:
        *   Add more specific instructions.
        *   Provide examples within the field descriptions if Claude is struggling with a particular field.
        *   Clarify expected types or formats.
        *   Re-phrase instructions for better clarity.
5.  **Restart Backend:** After saving changes to `app.py`, restart the Flask backend service to apply the new system prompt. The bot usually doesn't need a restart unless its own code changes.
6.  **Retest:** Run the same test prompt (and variations) again to see if the changes improved the output.
7.  **Iterate:** Repeat steps 2-6. Prompt engineering is an iterative process.

### Example Test Prompts:

**Simple & Direct:**
*   `/generate prompt:a simple house drum loop`
*   `/generate prompt:deep sub bass line`
*   `/generate prompt:energetic trap hi-hats with rolls`

**With Parameters:**
*   `/generate prompt:lo-fi hip hop beat genre:hip-hop bpm:85 key:Am bars:4`
*   `/generate prompt:ethereal ambient pads genre:ambient key:Cmaj bars:16 bpm:70`

**Descriptive/Vague:**
*   `/generate prompt:music for a rainy day, make it chill`
*   `/generate prompt:something fast and aggressive for a workout`
*   `/generate prompt:a sound that feels like floating in space`

**Testing Specific Fields:**
*   `/generate prompt:acoustic guitar strumming a G C D progression` (for `melodic_harmonic_elements`)
*   `/generate prompt:kick drum with a heavy sidechain compression effect` (for `sound_design_details`)

By following this iterative process of testing and refining the system prompt, you will improve the quality and reliability of the structured data produced by Claude, which is essential for the subsequent music generation stages.
