import discord
from discord.ext import commands
import os
import logging
import aiohttp
import json
import io
from typing import Optional, List, Dict, Any # Added Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
BACKEND_URL_GENERATE = os.getenv("BACKEND_URL_GENERATE", "http://127.0.0.1:5000/generate_stem")
BACKEND_URL_REFINE = os.getenv("BACKEND_URL_REFINE", "http://127.0.0.1:5000/refine_stem")
APP_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

if not DISCORD_BOT_TOKEN:
    logging.error("CRITICAL: DISCORD_BOT_TOKEN environment variable not set.")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix=commands.when_mentioned_or("/"), intents=intents)

@bot.event
async def on_ready():
    logging.info(f'Bot logged in as {bot.user.name} (ID: {bot.user.id})')
    try:
        synced = await bot.tree.sync()
        logging.info(f"Synced {len(synced)} application command(s).")
    except Exception as e:
        logging.error(f"Error syncing application commands: {e}")

async def common_backend_request_and_response_handling(
    interaction: discord.Interaction,
    url: str,
    payload: dict,
    action_description: str,
    user_facing_prompt_desc: str
):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                response_text_for_error_logging = await response.text(encoding='utf-8', errors='ignore')

                if response.status == 200:
                    backend_response_data = json.loads(response_text_for_error_logging)
                    logging.info(f"Backend {action_description} response received successfully.")
                    logging.debug(f"Full backend {action_description} response data: {backend_response_data}")

                    claude_output_json = backend_response_data.get("claude_output", {})
                    generation_id = backend_response_data.get("generation_id")
                    output_wav_url = backend_response_data.get("output_wav_url")
                    output_midi_url = backend_response_data.get("output_midi_url")

                    claude_output_filename = "llm_interpretation.json"
                    if action_description == "refinement":
                        claude_output_filename = "refined_llm_interpretation.json"

                    pretty_claude_output = json.dumps(claude_output_json, indent=2)
                    claude_output_bytes = io.BytesIO(pretty_claude_output.encode('utf-8'))
                    claude_output_file = discord.File(claude_output_bytes, filename=claude_output_filename)

                    files_to_send = [claude_output_file]

                    embed = discord.Embed(
                        title=f"Stem {action_description.capitalize()} Complete!",
                        description=f"Results for your request: \"{user_facing_prompt_desc}\"",
                        color=discord.Color.green()
                    )
                    if generation_id:
                        embed.add_field(name="Generation ID", value=str(generation_id), inline=False)
                    if output_wav_url:
                        embed.add_field(name="WAV Download", value=f"[Click here to download WAV]({output_wav_url})", inline=True)
                    else:
                        embed.add_field(name="WAV File", value="Not available.", inline=True)
                    if output_midi_url:
                        embed.add_field(name="MIDI Download", value=f"[Click here to download MIDI]({output_midi_url})", inline=True)
                    else:
                        embed.add_field(name="MIDI File", value="Not available.", inline=True)
                    embed.set_footer(text="LLM interpretation is attached as a JSON file.")
                    await interaction.followup.send(embed=embed, files=files_to_send)
                else:
                    logging.error(f"Backend error during {action_description}. Status: {response.status}, Response: {response_text_for_error_logging[:1000]}")
                    error_payload = None
                    try: error_payload = json.loads(response_text_for_error_logging)
                    except json.JSONDecodeError: pass
                    error_message_from_backend = "An unspecified error occurred at the backend."
                    if error_payload and error_payload.get("error"): error_message_from_backend = error_payload["error"]
                    elif response.reason: error_message_from_backend = f"Backend responded with: {response.reason}"
                    llm_raw_output_snippet = ""
                    if error_payload and error_payload.get("llm_raw_output"): llm_raw_output_snippet = f"\nLLM Raw (snippet): ```\n{error_payload['llm_raw_output'][:500]}...\n```"
                    embed = discord.Embed(title=f"{action_description.capitalize()} Failed", description=f"Sorry, there was an error processing your request for \"{user_facing_prompt_desc}\".\n**Backend Status {response.status}:** {error_message_from_backend}{llm_raw_output_snippet}", color=discord.Color.red())
                    if error_payload and error_payload.get("generation_id"): embed.add_field(name="Generation ID (if logged)", value=str(error_payload["generation_id"]), inline=False)
                    if error_payload and error_payload.get("output_wav_url"): embed.add_field(name="Partial WAV Link (if available)", value=f"[WAV Link]({error_payload['output_wav_url']})", inline=True)
                    if error_payload and error_payload.get("output_midi_url"): embed.add_field(name="Partial MIDI Link (if available)", value=f"[MIDI Link]({error_payload['output_midi_url']})", inline=True)
                    await interaction.followup.send(embed=embed, ephemeral=True)
    except aiohttp.ClientConnectorError as e:
        logging.error(f"Cannot connect to backend for {action_description}: {e}")
        await interaction.followup.send(f"Sorry, I couldn't connect to the music generation service for {action_description}. It might be down.", ephemeral=True)
    except Exception as e:
        logging.error(f"An unexpected error occurred in bot during {action_description}: {e}", exc_info=True)
        await interaction.followup.send(f"An unexpected error occurred on my end during {action_description}. Please try again.", ephemeral=True)

@bot.tree.command(name="generate", description="Generates a musical stem (.wav & .midi) from your prompt.")
async def generate_slash(interaction: discord.Interaction, prompt: str, genre: Optional[str] = None, bpm: Optional[int] = None, key: Optional[str] = None, bars: Optional[int] = None):
    logging.info(f"User {interaction.user.id} in G:{interaction.guild_id}/C:{interaction.channel_id} called /generate: Prompt='{prompt}'")
    await interaction.response.defer(ephemeral=False, thinking=True)
    payload = {
        "prompt": prompt, "genre": genre, "bpm": bpm, "key": key, "bars": bars,
        "user_id": str(interaction.user.id),
        "guild_id": str(interaction.guild_id) if interaction.guild_id else None,
        "channel_id": str(interaction.channel_id) if interaction.channel_id else None,
    }
    await common_backend_request_and_response_handling(interaction, BACKEND_URL_GENERATE, payload, "generation", prompt)

@bot.tree.command(name="refine", description="Refines a previous generation. Provide its Message ID and your refinement prompt.")
async def refine_slash(interaction: discord.Interaction, message_id: str, new_prompt: str):
    logging.info(f"User {interaction.user.id} called /refine: Message ID='{message_id}', New Prompt='{new_prompt}'")
    await interaction.response.defer(ephemeral=False, thinking=True)

    original_claude_json: Optional[Dict[str, Any]] = None
    original_prompt_desc = f"message ID {message_id}" # Fallback description

    try:
        msg_id = int(message_id)
    except ValueError:
        await interaction.followup.send("Invalid Message ID format. Please provide a valid numerical ID.", ephemeral=True)
        return

    try:
        # Fetch the original message from the current channel
        original_bot_message = await interaction.channel.fetch_message(msg_id)

        if original_bot_message.author != bot.user:
            await interaction.followup.send("The Message ID provided does not belong to me (the bot). Please provide the ID of my message that contains the 'llm_interpretation.json' file.", ephemeral=True)
            return

        found_attachment = False
        for attachment in original_bot_message.attachments:
            # Allow fetching from either initial generation or a previous refinement
            if attachment.filename == "llm_interpretation.json" or attachment.filename == "refined_llm_interpretation.json":
                try:
                    json_bytes = await attachment.read()
                    original_claude_json_str = json_bytes.decode('utf-8')
                    original_claude_json = json.loads(original_claude_json_str)
                    found_attachment = True
                    logging.info(f"Successfully read '{attachment.filename}' from target message {message_id}.")
                    # Update description for user-facing messages
                    original_prompt_desc = original_claude_json.get("user_request", {}).get("original_prompt", f"message ID {message_id}")
                    break
                except json.JSONDecodeError as e:
                    logging.error(f"Failed to parse '{attachment.filename}' from message {message_id}: {e}")
                    await interaction.followup.send(f"Error: The '{attachment.filename}' file attached to message {message_id} is not valid JSON. Cannot refine.", ephemeral=True)
                    return
                except Exception as e:
                    logging.error(f"Error reading '{attachment.filename}' from message {message_id}: {e}")
                    await interaction.followup.send(f"Error: Could not read the context file '{attachment.filename}' from message {message_id}. Cannot refine.", ephemeral=True)
                    return

        if not found_attachment:
            await interaction.followup.send(f"Error: Could not find an 'llm_interpretation.json' or 'refined_llm_interpretation.json' attachment on message {message_id}. Make sure you provide the ID of my message that contains this file.", ephemeral=True)
            return

    except discord.NotFound:
        logging.warning(f"/refine: Message with ID {message_id} not found in this channel.")
        await interaction.followup.send(f"Error: Message with ID `{message_id}` not found in this channel. Please ensure the ID is correct and from the current channel.", ephemeral=True)
        return
    except discord.Forbidden:
        logging.error(f"/refine: Bot does not have permissions to fetch message {message_id}.")
        await interaction.followup.send("Error: I don't have permission to fetch the message history needed to get context. Please check my permissions.", ephemeral=True)
        return
    except Exception as e:
        logging.error(f"Unexpected error fetching/parsing context for /refine (Message ID: {message_id}): {e}", exc_info=True)
        await interaction.followup.send("An unexpected error occurred while trying to get the context for refinement. Please try again.", ephemeral=True)
        return

    # If original_claude_json is successfully populated
    if original_claude_json:
        payload = {
            "original_claude_json": original_claude_json,
            "refinement_prompt": new_prompt,
            "user_id": str(interaction.user.id),
            "guild_id": str(interaction.guild_id) if interaction.guild_id else None,
            "channel_id": str(interaction.channel_id) if interaction.channel_id else None,
        }
        user_facing_desc_for_handler = f"refinement of '{original_prompt_desc}' with '{new_prompt}'"
        await common_backend_request_and_response_handling(interaction, BACKEND_URL_REFINE, payload, "refinement", user_facing_desc_for_handler)
    else:
        # This case should ideally be caught by earlier checks, but as a fallback:
        await interaction.followup.send("Failed to obtain the necessary context for refinement. Please ensure you provide a valid Message ID of my previous generation response.", ephemeral=True)


if __name__ == '__main__':
    if not DISCORD_BOT_TOKEN: logging.critical("DISCORD_BOT_TOKEN is not set.")
    else:
        try: bot.run(DISCORD_BOT_TOKEN)
        except discord.LoginFailure: logging.error("Login to Discord failed. Check token.")
        except Exception as e: logging.error(f"Error running bot: {e}")
