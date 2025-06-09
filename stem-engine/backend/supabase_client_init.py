# -----------------------------------------------------------------------------
# SUPABASE 'generations' TABLE SCHEMA (for manual setup in Supabase Studio)
# -----------------------------------------------------------------------------
# Table name: generations
#
# Columns:
#   id uuid (Primary Key, Default: uuid_generate_v4())
#   created_at timestamptz (Default: now())
#   user_id text (Indexed)                     -- Discord User ID
#   guild_id text (Nullable, Indexed)          -- Discord Guild ID
#   channel_id text (Nullable)                 -- Discord Channel ID
#   prompt_text text                           -- The user's original full prompt string
#   claude_interpretation_json jsonb (Nullable) -- The full JSON output from Claude LLM
#   orchestrator_output_json jsonb (Nullable)   -- The JSON output from the orchestration layer
#   output_wav_url text (Nullable)             -- Public URL to the .wav file in Supabase Storage
#   output_midi_url text (Nullable)            -- Public URL to the .midi file in Supabase Storage
#   status text (Default: 'pending', Indexed)  -- e.g., 'pending', 'success', 'failed_upload', 'failed_logging', 'failed_generation'
#   error_message text (Nullable)              -- Any error message if status is a failure type
#   duration_ms integer (Nullable)             -- If known, duration of the generated audio
#   model_version_claude text (Nullable)       -- Version/name of the Claude model used
#   model_version_orchestrator text (Nullable) -- Version of the orchestrator logic used
#   model_version_generator text (Nullable)    -- Version of the audio generator used (future)
#
# Suggested Row Level Security (RLS) - for future consideration (not MVP sprint):
# - Enable RLS on the table.
# - Allow public read-only access if needed for a public gallery.
# - Allow individual users to read their own generations.
# - Backend service role key will bypass RLS for inserts/updates.
#
# Example SQL for table creation (adapt types if Supabase UI differs slightly):
#
# CREATE TABLE public.generations (
#     id uuid DEFAULT uuid_generate_v4() NOT NULL,
#     created_at timestamp with time zone DEFAULT now() NOT NULL,
#     user_id text NOT NULL,
#     guild_id text,
#     channel_id text,
#     prompt_text text NOT NULL,
#     claude_interpretation_json jsonb,
#     orchestrator_output_json jsonb,
#     output_wav_url text,
#     output_midi_url text,
#     status text DEFAULT 'pending'::text NOT NULL,
#     error_message text,
#     duration_ms integer,
#     model_version_claude text,
#     model_version_orchestrator text,
#     model_version_generator text
# );
# ALTER TABLE public.generations ADD CONSTRAINT generations_pkey PRIMARY KEY (id);
# CREATE INDEX generations_user_id_idx ON public.generations (user_id);
# CREATE INDEX generations_guild_id_idx ON public.generations (guild_id);
# CREATE INDEX generations_status_idx ON public.generations (status);
# -- To enable uuid_generate_v4() if not enabled: CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
# -----------------------------------------------------------------------------

import os
import logging
from supabase import create_client, Client
from typing import Optional # Added for type hinting

# Get Supabase credentials from environment variables
SUPABASE_URL: str = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY", "") # This should be the service_role key for backend operations

supabase_client: Optional[Client] = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        logging.info(f"Initializing Supabase client with URL: {SUPABASE_URL[:20]}...") # Log only part of URL
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logging.info("Supabase client initialized successfully.")
    except Exception as e:
        logging.error(f"Failed to initialize Supabase client: {e}", exc_info=True)
        supabase_client = None # Ensure client is None if initialization fails
else:
    logging.warning("SUPABASE_URL and/or SUPABASE_KEY environment variables are not set. Supabase client not initialized.")

def get_supabase_client() -> Optional[Client]:
    '''Returns the initialized Supabase client. Returns None if not initialized.'''
    return supabase_client
