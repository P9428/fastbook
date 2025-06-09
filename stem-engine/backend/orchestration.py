import logging
from typing import Dict, Any, Optional, List
import os # Ensure os is imported if not already at the top for path joining

# In a full environment, ensure OrchestratorOutput from orchestration_types.py
# is properly imported and used as the return type hint.
# from .orchestration_types import OrchestratorOutput

DEFAULT_BPM = 120
DEFAULT_BARS = 4
# DEFAULT_KEY = "C major" # Decided to keep key None if not specified.

def orchestrate_generation(claude_output: Dict[str, Any]) -> Dict[str, Any]: # Should be OrchestratorOutput
    '''
    Takes Claude's structured JSON output and translates it into a format
    usable by downstream placeholder/generator selection logic.
    '''
    logging.debug(f"Orchestrator input (Claude output): {claude_output}")

    user_request = claude_output.get("user_request", {})
    interpretation = claude_output.get("interpretation", {})

    # Initialize OrchestratorOutput fields
    target_generator_type = "generic_placeholder" # Default

    # Directly use values from Claude if available, otherwise they remain None or default from Claude
    derived_bpm = interpretation.get("tempo_bpm")
    derived_key = interpretation.get("musical_key")
    derived_bars = interpretation.get("loop_length_bars")

    energy_level = interpretation.get("energy_level")
    mood_descriptors = interpretation.get("mood_descriptors", []) # Default to empty list if not present
    generator_specific_params: Dict[str, Any] = {}

    # --- Basic Rule-Based Logic for target_generator_type ---
    instrument_desc = str(interpretation.get("primary_instrument_description", "")).lower()
    genre_tags = [str(tag).lower() for tag in interpretation.get("genre_tags", []) if tag is not None]


    if "drum" in instrument_desc:
        if "hip-hop" in genre_tags or "lo-fi" in genre_tags:
            target_generator_type = "drum_loop_hip_hop"
        elif "trap" in genre_tags:
            target_generator_type = "drum_loop_trap"
        elif "house" in genre_tags or "techno" in genre_tags or "dance" in genre_tags:
            target_generator_type = "drum_loop_electronic_dance"
        else:
            target_generator_type = "drum_loop_generic"
    elif "bass" in instrument_desc:
        if "hip-hop" in genre_tags:
            target_generator_type = "bassline_hip_hop"
        elif "trap" in genre_tags:
            target_generator_type = "bassline_trap"
        elif "house" in genre_tags or "techno" in genre_tags:
            target_generator_type = "bassline_electronic_dance"
        else:
            target_generator_type = "bassline_generic"
    elif "synth" in instrument_desc or "pad" in instrument_desc or "lead" in instrument_desc or "melody" in instrument_desc:
        if "ambient" in genre_tags:
            target_generator_type = "synth_pad_ambient"
        elif "melodic" in instrument_desc or "lead" in instrument_desc:
            target_generator_type = "synth_melody_generic"
        elif "pad" in instrument_desc:
             target_generator_type = "synth_pad_texture" # More specific than generic texture
        else:
            target_generator_type = "synth_texture_generic"

    # Apply defaults for critical parameters if not provided by Claude or user
    if derived_bpm is None:
        derived_bpm = DEFAULT_BPM
        logging.debug(f"Applied default BPM: {DEFAULT_BPM}")

    if derived_bars is None:
        derived_bars = DEFAULT_BARS
        logging.debug(f"Applied default bars: {DEFAULT_BARS}")

    # derived_key remains None if not specified by user/Claude, to avoid unwanted musical constraints.

    orchestrator_decision: Dict[str, Any] = { # This structure should match OrchestratorOutput
        "target_generator_type": target_generator_type,
        "derived_bpm": derived_bpm,
        "derived_key": derived_key,
        "derived_bars": derived_bars,
        "energy_level": energy_level,
        "mood_descriptors": mood_descriptors,
        "generator_specific_params": generator_specific_params,
        "original_user_prompt": user_request.get("original_prompt", "Prompt not found in Claude output"),
        "claude_interpretation": interpretation
    }

    logging.info(f"Orchestrator decided: Type='{orchestrator_decision['target_generator_type']}', BPM={orchestrator_decision['derived_bpm']}, Bars={orchestrator_decision['derived_bars']}, Key='{orchestrator_decision['derived_key']}'")
    logging.debug(f"Full orchestrator output: {orchestrator_decision}")

    return orchestrator_decision

# Define the base directory of the application (stem-engine) for asset path resolution
# This assumes orchestration.py is in stem-engine/backend/
APP_BASE_DIR_ORCH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ASSETS_AUDIO_DIR = os.path.join(APP_BASE_DIR_ORCH, 'assets', 'audio_placeholders')

PLACEHOLDER_MAP = {
    # Drums
    "drum_loop_hip_hop": "placeholder_drums.wav", # General hip-hop drums
    "drum_loop_trap": "placeholder_drums.wav",    # Using same for now, could be different
    "drum_loop_electronic_dance": "placeholder_drums.wav", # Ditto
    "drum_loop_generic": "placeholder_drums.wav",
    # Basslines
    "bassline_hip_hop": "placeholder_bass.wav",
    "bassline_trap": "placeholder_bass.wav",
    "bassline_electronic_dance": "placeholder_bass.wav",
    "bassline_generic": "placeholder_bass.wav",
    # Synths / Pads / Melodies
    "synth_pad_ambient": "placeholder_synth.wav", # General synth for pads
    "synth_melody_generic": "placeholder_synth.wav", # General synth for melodies
    "synth_pad_texture": "placeholder_synth.wav",
    "synth_texture_generic": "placeholder_synth.wav",
    # Default
    "generic_placeholder": "default_loop.wav" # A very generic default
}

def select_placeholder_audio(orchestrator_output: Dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
    '''
    Selects a placeholder audio file based on the orchestrator's decision.
    Returns (selected_audio_filename, audio_file_path_from_root) or (None, None).
    '''
    target_type = orchestrator_output.get("target_generator_type", "generic_placeholder")
    selected_filename = PLACEHOLDER_MAP.get(target_type)

    if not selected_filename:
        # Fallback if target_type somehow isn't in map (shouldn't happen if orchestrator is robust)
        logging.warning(f"No placeholder directly mapped for target_type: {target_type}. Using generic default.")
        selected_filename = PLACEHOLDER_MAP["generic_placeholder"]

    # Construct the path relative to the project root
    # (e.g., "assets/audio_placeholders/placeholder_drums.wav")
    relative_path_from_root = os.path.join('assets', 'audio_placeholders', selected_filename)

    # Also check if the actual file exists to prevent issues later
    absolute_path_on_server = os.path.join(ASSETS_AUDIO_DIR, selected_filename)
    if not os.path.exists(absolute_path_on_server):
        logging.error(f"Selected placeholder audio file NOT FOUND at: {absolute_path_on_server}")
        # Fallback to a known default if specific one is missing
        # This indicates an issue with asset files or mapping.
        default_filename = PLACEHOLDER_MAP["generic_placeholder"]
        if selected_filename != default_filename and os.path.exists(os.path.join(ASSETS_AUDIO_DIR, default_filename)):
            logging.warning(f"Falling back to default placeholder: {default_filename}")
            selected_filename = default_filename
            relative_path_from_root = os.path.join('assets', 'audio_placeholders', selected_filename)
        else: # Even default is missing
            logging.error(f"Even default placeholder {default_filename} NOT FOUND at: {os.path.join(ASSETS_AUDIO_DIR, default_filename)}")
            return None, None # Critical error, no audio can be provided

    logging.info(f"Placeholder selected: Filename='{selected_filename}', PathFromRoot='{relative_path_from_root}' for TargetType='{target_type}'")
    return selected_filename, relative_path_from_root
