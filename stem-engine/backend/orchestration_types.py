from typing import TypedDict, Optional, List, Dict, Any

class OrchestratorOutput(TypedDict):
    '''
    Defines the structured output from the Orchestration Layer.
    This data structure is used to guide the selection or generation of audio.
    '''
    target_generator_type: str          # e.g., "drum_loop_hip_hop", "synth_pad_ambient", "bassline_trap"
                                        # This will map to specific generator modules or placeholder categories.

    derived_bpm: Optional[int]          # Beats per minute, potentially confirmed or adjusted by the orchestrator.
    derived_key: Optional[str]          # Musical key, potentially confirmed or adjusted.
    derived_bars: Optional[int]         # Length of the loop in bars, potentially confirmed or adjusted.

    # General parameters that many generators might understand
    energy_level: Optional[str]         # e.g., "low", "medium", "high", derived from Claude's output.
    mood_descriptors: Optional[List[str]] # e.g., ["melancholic", "energetic"], from Claude.

    # Placeholder for more specific parameters that future, actual generators might need.
    # The keys and values would be defined by the requirements of those specific generators.
    # For example, a drum generator might look for:
    #   "kick_style": "punchy" | "boomy" | "tight"
    #   "snare_style": "crisp" | "lazy" | "reverberant"
    #   "hi_hat_pattern": "16th_notes" | "8th_notes" | "complex_rolls"
    # A synth generator might look for:
    #   "waveform": "sine" | "square" | "sawtooth"
    #   "filter_cutoff": "low" | "medium" | "high"
    #   "attack_time_ms": 100
    generator_specific_params: Dict[str, Any]

    # Information about the original request, carried through for logging or context
    original_user_prompt: str
    claude_interpretation: Dict[str, Any] # The full 'interpretation' block from Claude for reference
