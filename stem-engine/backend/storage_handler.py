import logging
import os
from typing import Optional
# Assuming supabase_client_init.py provides get_supabase_client()
from supabase_client_init import get_supabase_client

# Default bucket name, can be overridden if needed
DEFAULT_STEMS_BUCKET = "stems"

def upload_file_to_supabase(
    local_file_path: str,
    supabase_path_with_filename: str,
    bucket_name: str = DEFAULT_STEMS_BUCKET
) -> Optional[str]:
    '''
    Uploads a local file to the specified Supabase Storage bucket and returns its public URL.

    Args:
        local_file_path: The absolute path to the local file to upload.
        supabase_path_with_filename: The desired path and filename in Supabase Storage
                                     (e.g., "user_123/generated_drum_loop.wav").
        bucket_name: The name of the Supabase Storage bucket.

    Returns:
        The public URL of the uploaded file, or None if the upload fails.
    '''
    supabase = get_supabase_client()
    if not supabase:
        logging.error("Supabase client not initialized. Cannot upload file.")
        return None

    if not os.path.exists(local_file_path):
        logging.error(f"Local file not found for upload: {local_file_path}")
        return None

    try:
        # Read the file content in binary mode
        with open(local_file_path, 'rb') as f:
            file_content = f.read()

        # Upload the file
        # The Supabase Python client's storage API uses `upload` for new files
        # or `update` if you want to overwrite. We'll use `upload`.
        # The path in Supabase is the second argument to `bucket(bucket_name).upload()`.
        response = supabase.storage.from_(bucket_name).upload(
            path=supabase_path_with_filename,
            file=file_content, # Pass the bytes directly
            file_options={"cache-control": "3600", "upsert": "false"} # upsert=false means don't update if exists
                                                                    # Set to true if overwriting is desired for same path
        )

        logging.info(f"File upload response from Supabase for {supabase_path_with_filename}: Status {response.status_code}")

        if response.status_code == 200:
            # If upload is successful, get the public URL
            # The key for the public URL is derived from the path used for upload.
            public_url_response = supabase.storage.from_(bucket_name).get_public_url(supabase_path_with_filename)

            # The actual URL is typically in public_url_response directly if it's a string,
            # or you might need to access a property if it's an object.
            # Based on common patterns, let's assume it's a string.
            # If it's an object, adjust accordingly (e.g. public_url_response.public_url)

            # The get_public_url method in supabase-py returns the URL string directly.
            public_url = public_url_response

            logging.info(f"Successfully uploaded {local_file_path} to Supabase bucket '{bucket_name}' at path '{supabase_path_with_filename}'. Public URL: {public_url}")
            return public_url
        else:
            # Try to get error details from response if possible
            error_details = "Unknown error"
            try:
                error_details = response.json()
            except Exception:
                error_details = response.text if hasattr(response, 'text') else "Could not retrieve error details."
            logging.error(f"Failed to upload file to Supabase. Status: {response.status_code}, Path: {supabase_path_with_filename}, Details: {error_details}")
            return None

    except Exception as e:
        logging.error(f"An error occurred during Supabase file upload for {local_file_path}: {e}", exc_info=True)
        return None
