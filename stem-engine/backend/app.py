from flask import Flask, request, jsonify
import logging
import os
import anthropic
import json
import uuid # For generating unique filenames
from datetime import datetime, timezone # For timestamps

# Project-specific imports
from orchestration import orchestrate_generation, select_placeholder_audio
from supabase_client_init import get_supabase_client # For DB operations
from storage_handler import upload_file_to_supabase # For file uploads

# Basic logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
app = Flask(__name__)

# Initialize Supabase client (available via get_supabase_client())
supabase = get_supabase_client()

# Claude client initialization
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL_NAME = os.getenv("CLAUDE_MODEL_NAME", "claude-3-opus-20240229")
claude_client = None
if ANTHROPIC_API_KEY:
    try:
        claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    except Exception as e:
        logging.error(f"Failed to initialize Anthropic client: {e}", exc_info=True)
else:
    logging.warning("ANTHROPIC_API_KEY not set. Claude API calls will fail.")

# Base directory for resolving asset paths
APP_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ASSETS_AUDIO_DIR = os.path.join(APP_BASE_DIR, 'assets', 'audio_placeholders')

# Claude System Prompts (Generation and Refinement)
CLAUDE_SYSTEM_PROMPT = '''You are an AI assistant for music producers. Your task is to interpret a user's natural language request for a musical stem (a short audio loop) and transform it into a structured JSON object. This JSON object will be used by downstream music generation tools.
The user will provide a main 'prompt' and optionally 'genre', 'bpm' (beats per minute), 'key' (musical key), and 'bars' (length of the loop).
Your JSON output MUST strictly follow this format:
{
  "user_request": {
    "original_prompt": "The user's original main prompt string",
    "genre_specified": "User specified genre or null",
    "bpm_specified": "User specified BPM or null",
    "key_specified": "User specified key or null",
    "bars_specified": "User specified bars or null"
  },
  "interpretation": {
    "primary_instrument_description": "Describe the core instrument or sound the user wants (e.g., 'a deep sub bass', 'a gritty acoustic drum kit', 'ethereal synth pads'). Infer this from the prompt.",
    "genre_tags": ["An array of relevant genre tags, e.g., 'hip-hop', 'lo-fi', 'ambient', 'techno'. Consider both specified genre and inferred from prompt."],
    "mood_descriptors": ["An array of adjectives describing the mood/vibe, e.g., 'melancholic', 'energetic', 'dreamy', 'aggressive'. Infer from prompt."],
    "tempo_bpm": "Integer BPM. If specified by user, use that. If not, infer a suitable BPM based on prompt/genre, or leave as null if highly ambiguous.",
    "musical_key": "Musical key (e.g., 'C minor', 'F# major', 'Am'). If specified by user, use that. If not, infer if possible, or leave as null.",
    "loop_length_bars": "Integer number of bars. If specified by user, use that. If not, infer a common loop length (e.g., 2, 4, 8) or leave as null.",
    "rhythmic_elements": ["Describe rhythmic characteristics, e.g., 'shuffle groove', 'straight 16th-note hi-hats', 'syncopated kick drum', 'lazy snare'. Null if not applicable."],
    "melodic_harmonic_elements": ["Describe melodic/harmonic aspects, e.g., 'simple pentatonic melody', 'minor chord progression', 'sustained drone'. Null if not applicable."],
    "sound_design_details": ["Specific sound characteristics mentioned or implied, e.g., 'heavy distortion', 'vinyl crackle', 'spacious reverb', 'filter sweeps'. Null if not applicable."],
    "energy_level": "A string describing overall energy: 'low', 'medium', 'high'. Infer from prompt and genre.",
    "additional_notes": "Any other important details or nuances you picked up from the user's request that don't fit elsewhere."
  }
}
Adhere to JSON format strictly. If a field is not applicable or cannot be inferred, use null or an empty array as appropriate for the field type.
Do not add any conversational text or explanations outside of the JSON structure itself. Your entire response should be the JSON object.
'''

CLAUDE_REFINE_SYSTEM_PROMPT = '''You are an AI assistant for music producers, specializing in refining existing musical ideas.
You will be given an 'original_llm_interpretation' which is a JSON object representing a previously generated musical stem. This JSON object was created by an AI based on a user's request and has a specific structure.
You will also be given a 'user_refinement_request' which is a natural language instruction from the user on how they want to change or modify the original stem.

Your task is to produce a NEW JSON object that incorporates the user's refinement request into the original interpretation.
The output JSON MUST strictly follow the exact same format as the 'original_llm_interpretation' provided. Do not add, remove, or rename keys in the JSON structure unless the refinement explicitly implies a structural change that fits the schema (e.g. adding a new genre tag if specified).

Carefully consider the user's refinement request and how it applies to the various fields in the original JSON.
- If the refinement contradicts a field in the original, update that field in the new JSON.
- If the refinement adds new information relevant to a field, incorporate it.
- If the refinement asks to remove or lessen something, reflect that (e.g., change mood_descriptors, lower energy_level, set a field to null if appropriate).
- If a field from the original interpretation is not affected by the refinement request, carry it over as-is to the new JSON.
- Ensure that all fields in the new JSON are consistent with each other after applying the refinement. For example, if the user asks for "more energetic", also update `energy_level` and potentially `tempo_bpm` or `rhythmic_elements`.

The 'user_request' block within the JSON should also be updated:
- 'original_prompt' in the 'user_request' block of the NEW JSON should be the 'user_refinement_request' text.
- 'genre_specified', 'bpm_specified', 'key_specified', 'bars_specified' in the 'user_request' block should reflect any such parameters *explicitly mentioned in the user_refinement_request*. If not mentioned, they can be null or based on the refined interpretation from the original JSON if not contradicted.

Your entire response MUST be only the new, complete JSON object. Do not include any conversational text, explanations, or markdown formatting outside of the JSON structure itself.
'''

# --- /generate_stem endpoint (as implemented in previous sprint) ---
@app.route('/generate_stem', methods=['POST'])
def generate_stem():
    # ... (Full implementation from previous step, unchanged for this task) ...
    if not claude_client:
        logging.error("Anthropic client not initialized. Cannot process /generate_stem.")
        return jsonify({"error": "AI model client not configured properly."}), 503
    if not supabase:
        logging.error("Supabase client not initialized. Cannot process /generate_stem.")
        return jsonify({"error": "Database/Storage client not configured properly."}), 503
    try:
        data = request.get_json()
        if not data: return jsonify({"error": "Invalid request. JSON data expected."}), 400
        user_prompt = data.get('prompt')
        user_id = data.get('user_id')
        guild_id = data.get('guild_id')
        channel_id = data.get('channel_id')
        if not user_prompt: return jsonify({"error": "Missing 'prompt' in request data."}), 400
        if not user_id: return jsonify({"error": "Missing 'user_id' in request data."}), 400
        user_genre = data.get('genre'); user_bpm = data.get('bpm'); user_key = data.get('key'); user_bars = data.get('bars')
        logging.info(f"User {user_id} in Guild {guild_id}/Channel {channel_id} called /generate_stem with prompt: '{user_prompt}'")
    except Exception as e:
        logging.error(f"Error parsing request data for /generate_stem: {e}", exc_info=True)
        return jsonify({"error": "Error parsing request data."}), 400

    claude_structured_output = None; orchestrated_params = None
    generation_status = "pending_llm"; error_message_details = None
    try:
        claude_user_message_content = "User's request details:\n" + f"- Main prompt: \"{user_prompt}\"\n" + (f"- Genre: {user_genre}\n" if user_genre else "") + (f"- BPM: {user_bpm}\n" if user_bpm else "") + (f"- Key: {user_key}\n" if user_key else "") + (f"- Bars: {user_bars}\n" if user_bars else "")
        logging.info(f"Sending request to Claude. Model: {CLAUDE_MODEL_NAME}.")
        claude_api_response = claude_client.messages.create(model=CLAUDE_MODEL_NAME, max_tokens=2048, system=CLAUDE_SYSTEM_PROMPT, messages=[{"role": "user", "content": claude_user_message_content}])
        logging.info(f"Raw response received from Claude. Stop reason: {claude_api_response.stop_reason}.")
        if claude_api_response.content and claude_api_response.content[0].type == "text":
            claude_json_output_str = claude_api_response.content[0].text
            logging.debug(f"Claude text output before parsing: {claude_json_output_str}")
            try:
                if claude_json_output_str.strip().startswith("```json"): claude_json_output_str = claude_json_output_str.strip()[7:-3].strip()
                elif claude_json_output_str.strip().startswith("```"): claude_json_output_str = claude_json_output_str.strip()[3:-3].strip()
                claude_structured_output = json.loads(claude_json_output_str)
                logging.info("Successfully parsed Claude's output as JSON.")
                generation_status = "llm_success"
            except json.JSONDecodeError as e:
                logging.error(f"Failed to parse Claude's output as JSON: {e}"); error_message_details = "Failed to parse LLM response."
                generation_status = "failed_llm_parsing"; return jsonify({"error": error_message_details, "llm_raw_output": claude_json_output_str}), 500
        else:
            logging.error(f"Unexpected response structure from Claude: {claude_api_response}"); error_message_details = "Unexpected response format from LLM."
            generation_status = "failed_llm_response_format"; return jsonify({"error": error_message_details}), 500
    except anthropic.APIError as e:
        logging.error(f"Claude API error: {e}", exc_info=True); error_message_details = f"AI model service error: {type(e).__name__}"
        generation_status = "failed_llm_api_error"; return jsonify({"error": error_message_details}), 503
    except Exception as e:
        logging.error(f"An unexpected error occurred during Claude API call: {e}", exc_info=True); error_message_details = "An unexpected error with AI model service."
        generation_status = "failed_llm_unexpected"; return jsonify({"error": error_message_details}), 500
    try:
        orchestrated_params = orchestrate_generation(claude_structured_output)
        logging.info(f"Orchestration decided: Type='{orchestrated_params.get('target_generator_type')}', BPM={orchestrated_params.get('derived_bpm')}")
        generation_status = "orchestration_success"
    except Exception as e:
        logging.error(f"Error during orchestration: {e}", exc_info=True); error_message_details = "Error in orchestration layer."
        generation_status = "failed_orchestration"
    output_wav_url = None; output_midi_url = None
    if generation_status == "orchestration_success":
        try:
            selected_wav_filename, wav_path_from_root = select_placeholder_audio(orchestrated_params)
            placeholder_midi_filename = "placeholder.midi"; midi_path_from_root = os.path.join('assets', 'audio_placeholders', placeholder_midi_filename)
            local_wav_path = os.path.join(APP_BASE_DIR, wav_path_from_root) if wav_path_from_root else None
            local_midi_path = os.path.join(APP_BASE_DIR, midi_path_from_root)
            unique_id = uuid.uuid4()
            # Ensure selected_wav_filename is a string before trying to use it in f-string or join
            actual_wav_filename_for_path = selected_wav_filename if selected_wav_filename else "audio.wav"
            supabase_wav_filename = f"stems/{user_id}/{unique_id}_{actual_wav_filename_for_path}"
            supabase_midi_filename = f"stems/{user_id}/{unique_id}_{placeholder_midi_filename}"

            if local_wav_path and os.path.exists(local_wav_path):
                output_wav_url = upload_file_to_supabase(local_wav_path, supabase_wav_filename)
                if not output_wav_url: generation_status = "failed_wav_upload"; error_message_details = "Failed to upload WAV."
            else:
                logging.warning(f"Selected WAV placeholder not found or not selected: {local_wav_path}"); generation_status = "failed_wav_missing_local"; error_message_details = "Selected WAV not found locally."

            if os.path.exists(local_midi_path) and generation_status not in ["failed_wav_upload", "failed_wav_missing_local"]:
                output_midi_url = upload_file_to_supabase(local_midi_path, supabase_midi_filename)
                if not output_midi_url: generation_status = "failed_midi_upload"; error_message_details = (error_message_details or "") + " Failed to upload MIDI."
            else: # MIDI placeholder missing
                if generation_status not in ["failed_wav_upload", "failed_wav_missing_local"]: # Don't overwrite more critical WAV error
                    logging.warning(f"Placeholder MIDI file not found: {local_midi_path}"); generation_status = "failed_midi_missing_local"; error_message_details = (error_message_details or "") + " Placeholder MIDI not found."

            if output_wav_url and output_midi_url: generation_status = "success" # Both must be successful for overall success status
            elif output_wav_url and not output_midi_url and generation_status != "failed_midi_missing_local": # WAV good, MIDI failed upload
                 generation_status = "success_wav_only_midi_upload_failed" # Special status
            elif not output_wav_url and output_midi_url and generation_status != "failed_wav_missing_local": # MIDI good, WAV failed upload
                 generation_status = "success_midi_only_wav_upload_failed" # Special status


        except Exception as e:
            logging.error(f"Error during file selection/upload: {e}", exc_info=True); error_message_details = (error_message_details or "") + " Error in file processing/upload."
            if not generation_status.startswith("failed_"): generation_status = "failed_file_processing"

    generation_id = None
    try:
        generation_log_payload = {
            "user_id": user_id, "guild_id": guild_id, "channel_id": channel_id, "prompt_text": user_prompt,
            "claude_interpretation_json": claude_structured_output if isinstance(claude_structured_output, dict) else None,
            "orchestrator_output_json": orchestrated_params if isinstance(orchestrated_params, dict) else None,
            "output_wav_url": output_wav_url, "output_midi_url": output_midi_url, "status": generation_status,
            "error_message": error_message_details, "model_version_claude": CLAUDE_MODEL_NAME,
        }
        insert_response = supabase.table("generations").insert(generation_log_payload).execute()
        if insert_response.data and len(insert_response.data) > 0:
            generation_id = insert_response.data[0].get('id'); logging.info(f"Logged generation ID: {generation_id}")
            if generation_status.startswith("failed_"): logging.info(f"Generation {generation_id} logged with error: {generation_status} - {error_message_details}")
        else:
            logging.error(f"Failed to log to Supabase or no data returned: {insert_response}")
            if not generation_status.startswith("failed_"): generation_status = "failed_db_log_no_data"
            error_message_details = (error_message_details or "") + " Failed to log to DB (no data)."
    except Exception as e:
        logging.error(f"Error during Supabase DB logging: {e}", exc_info=True)
        if not generation_status.startswith("failed_"): generation_status = "failed_db_log_exception"
        error_message_details = (error_message_details or "") + " Error logging to DB."

    final_status_for_response = generation_status == "success" or \
                                generation_status == "success_wav_only_midi_upload_failed" or \
                                generation_status == "success_midi_only_wav_upload_failed"

    if final_status_for_response:
        return jsonify({"message": f"Generation process complete. Status: {generation_status}.", "generation_id": str(generation_id) if generation_id else None, "output_wav_url": output_wav_url, "output_midi_url": output_midi_url, "claude_output": claude_structured_output}), 200
    else:
        error_response_payload = {"error": f"Generation failed: {generation_status}. {error_message_details or 'See logs.'}", "generation_id": str(generation_id) if generation_id else None, "output_wav_url": output_wav_url, "output_midi_url": output_midi_url, "claude_output": claude_structured_output }
        http_status_code = 500;
        if "upload" in generation_status or "file_processing" in generation_status: http_status_code = 502
        return jsonify(error_response_payload), http_status_code

# --- /refine_stem endpoint ---
@app.route('/refine_stem', methods=['POST'])
def refine_stem():
    # --- Initial Checks ---
    if not claude_client: return jsonify({"error": "AI model client not configured properly."}), 503
    if not supabase: return jsonify({"error": "Supabase client not configured for /refine_stem."}), 503

    # --- Request Data Parsing & Validation ---
    try:
        data = request.get_json()
        if not data: return jsonify({"error": "Invalid request. JSON data expected."}), 400

        original_claude_json = data.get('original_claude_json')
        refinement_prompt = data.get('refinement_prompt')
        user_id = data.get('user_id')
        guild_id = data.get('guild_id')
        channel_id = data.get('channel_id')

        if not all([original_claude_json, refinement_prompt, user_id]):
            return jsonify({"error": "Missing 'original_claude_json', 'refinement_prompt', or 'user_id'."}), 400

        logging.info(f"User {user_id} in Guild {guild_id}/Channel {channel_id} called /refine_stem with prompt: '{refinement_prompt}'")
        logging.debug(f"Original Claude JSON for refinement: {original_claude_json}")

    except Exception as e:
        logging.error(f"Error parsing request data for /refine_stem: {e}", exc_info=True)
        return jsonify({"error": "Error parsing request data for refinement."}), 400

    # --- LLM Call (Claude for Refinement) ---
    refined_claude_output = None
    refined_orchestrated_params = None
    refinement_status = "pending_llm_refinement"
    ref_error_message_details = None

    try:
        claude_refine_user_message = (
            f"Here is the original JSON interpretation of a musical idea:\n"
            f"```json\n{json.dumps(original_claude_json, indent=2)}\n```\n\n"
            f"Now, please refine this based on the following request: \"{refinement_prompt}\""
        )

        logging.info(f"Sending refinement request to Claude. Model: {CLAUDE_MODEL_NAME}.")
        claude_api_response = claude_client.messages.create(
            model=CLAUDE_MODEL_NAME,
            max_tokens=2048,
            system=CLAUDE_REFINE_SYSTEM_PROMPT, # Using the new system prompt for refinement
            messages=[{"role": "user", "content": claude_refine_user_message}]
        )
        logging.info(f"Refinement response received from Claude. Stop reason: {claude_api_response.stop_reason}.")

        if claude_api_response.content and claude_api_response.content[0].type == "text":
            refined_claude_json_str = claude_api_response.content[0].text
            logging.debug(f"Refined Claude text output before parsing: {refined_claude_json_str}")
            try:
                if refined_claude_json_str.strip().startswith("```json"):
                    refined_claude_json_str = refined_claude_json_str.strip()[7:-3].strip()
                elif refined_claude_json_str.strip().startswith("```"):
                    refined_claude_json_str = refined_claude_json_str.strip()[3:-3].strip()
                refined_claude_output = json.loads(refined_claude_json_str)
                logging.info("Successfully parsed refined Claude output as JSON.")
                refinement_status = "llm_refinement_success"
            except json.JSONDecodeError as e:
                logging.error(f"Failed to parse refined Claude output as JSON: {e}")
                ref_error_message_details = "Failed to parse refined LLM response."
                refinement_status = "failed_llm_refinement_parsing"
                return jsonify({"error": ref_error_message_details, "llm_raw_output": refined_claude_json_str}), 500
        else:
            logging.error(f"Unexpected refinement response structure from Claude: {claude_api_response}")
            ref_error_message_details = "Unexpected response format from refined LLM call."
            refinement_status = "failed_llm_refinement_response_format"
            return jsonify({"error": ref_error_message_details}), 500

    except anthropic.APIError as e:
        logging.error(f"Claude API error during refinement: {e}", exc_info=True)
        ref_error_message_details = f"AI model service error during refinement: {type(e).__name__}"
        refinement_status = "failed_llm_refinement_api_error"
        return jsonify({"error": ref_error_message_details}), 503
    except Exception as e:
        logging.error(f"Unexpected error during Claude API refinement call: {e}", exc_info=True)
        ref_error_message_details = "An unexpected error with AI model service during refinement."
        refinement_status = "failed_llm_refinement_unexpected"
        return jsonify({"error": ref_error_message_details}), 500

    # --- Orchestration for Refined Output ---
    try:
        refined_orchestrated_params = orchestrate_generation(refined_claude_output) # Re-use same orchestrator
        logging.info(f"Refined Orchestration: Type='{refined_orchestrated_params.get('target_generator_type')}', BPM={refined_orchestrated_params.get('derived_bpm')}")
        refinement_status = "orchestration_refinement_success"
    except Exception as e:
        logging.error(f"Error during refined orchestration: {e}", exc_info=True)
        ref_error_message_details = "Error in refined orchestration layer."
        refinement_status = "failed_orchestration_refinement"

    # --- Placeholder Audio Selection & Upload for Refined Output ---
    refined_output_wav_url = None
    refined_output_midi_url = None

    if refinement_status == "orchestration_refinement_success":
        try:
            r_selected_wav_filename, r_wav_path_from_root = select_placeholder_audio(refined_orchestrated_params)
            r_placeholder_midi_filename = "placeholder.midi"
            r_midi_path_from_root = os.path.join('assets', 'audio_placeholders', r_placeholder_midi_filename)
            r_local_wav_path = os.path.join(APP_BASE_DIR, r_wav_path_from_root) if r_wav_path_from_root else None
            r_local_midi_path = os.path.join(APP_BASE_DIR, r_midi_path_from_root)
            r_unique_id = uuid.uuid4()
            r_actual_wav_filename = r_selected_wav_filename if r_selected_wav_filename else "audio_refined.wav"
            r_supabase_wav_filename = f"stems/{user_id}/{r_unique_id}_refined_{r_actual_wav_filename}"
            r_supabase_midi_filename = f"stems/{user_id}/{r_unique_id}_refined_{r_placeholder_midi_filename}"

            if r_local_wav_path and os.path.exists(r_local_wav_path):
                refined_output_wav_url = upload_file_to_supabase(r_local_wav_path, r_supabase_wav_filename)
                if not refined_output_wav_url: refinement_status = "failed_refined_wav_upload"; ref_error_message_details = "Failed to upload refined WAV."
            else:
                logging.warning(f"Refined WAV placeholder not found: {r_local_wav_path}"); refinement_status = "failed_refined_wav_missing_local"; ref_error_message_details = "Refined WAV not found locally."
            if os.path.exists(r_local_midi_path) and refinement_status not in ["failed_refined_wav_upload", "failed_refined_wav_missing_local"]:
                refined_output_midi_url = upload_file_to_supabase(r_local_midi_path, r_supabase_midi_filename)
                if not refined_output_midi_url: refinement_status = "failed_refined_midi_upload"; ref_error_message_details = (ref_error_message_details or "") + " Failed to upload refined MIDI."
            else:
                if refinement_status not in ["failed_refined_wav_upload", "failed_refined_wav_missing_local"]:
                    logging.warning(f"Refined MIDI placeholder not found: {r_local_midi_path}"); refinement_status = "failed_refined_midi_missing_local"; ref_error_message_details = (ref_error_message_details or "") + " Refined MIDI not found."

            if refined_output_wav_url and refined_output_midi_url: refinement_status = "success_refined"
            elif refined_output_wav_url and not refined_output_midi_url and refinement_status != "failed_refined_midi_missing_local": refinement_status = "success_refined_wav_only_midi_upload_failed"
            elif not refined_output_wav_url and refined_output_midi_url and refinement_status != "failed_refined_wav_missing_local": refinement_status = "success_refined_midi_only_wav_upload_failed"
        except Exception as e:
            logging.error(f"Error during refined file selection/upload: {e}", exc_info=True); ref_error_message_details = (ref_error_message_details or "") + " Error in refined file processing/upload."
            if not refinement_status.startswith("failed_"): refinement_status = "failed_refined_file_processing"

    # --- Database Logging for Refinement ---
    refined_generation_id = None
    try:
        log_prompt_text = f"Refinement of previous generation with: '{refinement_prompt}' (Original context user prompt: {original_claude_json.get('user_request',{}).get('original_prompt','N/A')[:100]}...)"
        refinement_log_payload = {
            "user_id": user_id, "guild_id": guild_id, "channel_id": channel_id, "prompt_text": log_prompt_text,
            "claude_interpretation_json": refined_claude_output if isinstance(refined_claude_output, dict) else None,
            "orchestrator_output_json": refined_orchestrated_params if isinstance(refined_orchestrated_params, dict) else None,
            "output_wav_url": refined_output_wav_url, "output_midi_url": refined_output_midi_url, "status": refinement_status,
            "error_message": ref_error_message_details, "model_version_claude": CLAUDE_MODEL_NAME,
        }
        insert_response = supabase.table("generations").insert(refinement_log_payload).execute()
        if insert_response.data and len(insert_response.data) > 0:
            refined_generation_id = insert_response.data[0].get('id'); logging.info(f"Logged refined generation ID: {refined_generation_id}")
            if refinement_status.startswith("failed_"): logging.info(f"Refined generation {refined_generation_id} logged with error: {refinement_status} - {ref_error_message_details}")
        else:
            logging.error(f"Failed to log refined generation to Supabase: {insert_response}")
            if not refinement_status.startswith("failed_"): refinement_status = "failed_refined_db_log_no_data"
            ref_error_message_details = (ref_error_message_details or "") + " Failed to log refined generation to DB (no data)."
    except Exception as e:
        logging.error(f"Error during Supabase DB logging for refinement by {user_id}: {e}", exc_info=True)
        if not refinement_status.startswith("failed_"): refinement_status = "failed_refined_db_log_exception"
        ref_error_message_details = (ref_error_message_details or "") + " Error logging refined generation to DB."

    # --- Final Response to Bot for Refinement ---
    final_refinement_status_for_response = refinement_status == "success_refined" or \
                                           refinement_status == "success_refined_wav_only_midi_upload_failed" or \
                                           refinement_status == "success_refined_midi_only_wav_upload_failed"

    if final_refinement_status_for_response:
        return jsonify({
            "message": f"Refinement process complete. Status: {refinement_status}.",
            "generation_id": str(refined_generation_id) if refined_generation_id else None,
            "output_wav_url": refined_output_wav_url,
            "output_midi_url": refined_output_midi_url,
            "claude_output": refined_claude_output # Send the NEW refined Claude output
        }), 200
    else:
        error_response_payload = {"error": f"Refinement failed: {refinement_status}. {ref_error_message_details or 'See logs.'}", "generation_id": str(refined_generation_id) if refined_generation_id else None, "output_wav_url": refined_output_wav_url, "output_midi_url": refined_output_midi_url, "claude_output": refined_claude_output } # Send new claude output even on error
        http_status_code = 500;
        if "upload" in refinement_status or "file_processing" in refinement_status: http_status_code = 502
        return jsonify(error_response_payload), http_status_code

# --- Health Check (as before) ---
@app.route('/health', methods=['GET'])
def health_check():
    status = {"status": "healthy"}
    if not claude_client: status["claude_client"] = "not_initialized"
    else: status["claude_client"] = "initialized"
    if not supabase: status["supabase_client"] = "not_initialized"
    else: status["supabase_client"] = "initialized"
    return jsonify(status), 200

if __name__ == '__main__':
    host = os.getenv("FLASK_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_PORT", 5000))
    debug_mode = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    if not ANTHROPIC_API_KEY: logging.warning("Reminder: ANTHROPIC_API_KEY is not set.")
    if not (os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_KEY")): logging.warning("Reminder: SUPABASE_URL and/or SUPABASE_KEY are not set.")
    app.run(host=host, port=port, debug=debug_mode)
