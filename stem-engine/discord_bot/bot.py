import discord
from discord.ext import commands
import os
import logging
import aiohttp
import json

# Basic logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:5000/generate_stem")

# Define the base directory of the application (stem-engine)
# Assumes bot.py is in stem-engine/discord_bot/
APP_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

if not DISCORD_BOT_TOKEN:
    logging.error("CRITICAL: DISCORD_BOT_TOKEN environment variable not set.")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=commands.when_mentioned_or("/"), intents=intents)

@bot.event
async def on_ready():
    logging.info(f'Bot logged in as {bot.user.name} (ID: {bot.user.id})')
    try:
        synced = await bot.tree.sync()
        logging.info(f"Synced {len(synced)} application command(s).")
    except Exception as e:
        logging.error(f"Error syncing application commands: {e}")

@bot.tree.command(
    name="generate",
    description="Generates a musical stem based on a prompt."
)
async def generate_slash(
    interaction: discord.Interaction,
    prompt: str,
    genre: str = None,
    bpm: int = None,
    key: str = None,
    bars: int = None
):
    logging.info(f"Received /generate: Prompt='{prompt}', Genre={genre}, BPM={bpm}, Key={key}, Bars={bars}")

    await interaction.response.send_message(
        f"Processing your request for: \"{prompt}\". Contacting backend...",
        ephemeral=True
    )

    payload = {
        "prompt": prompt, "genre": genre, "bpm": bpm, "key": key, "bars": bars
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(BACKEND_URL, json=payload) as response:
                if response.status == 200:
                    backend_response_json = await response.json()
                    logging.info(f"Backend response: {backend_response_json}")

                    selected_filename = backend_response_json.get("selected_audio_filename")
                    path_from_root = backend_response_json.get("audio_file_path_from_root")

                    if selected_filename and path_from_root:
                        # Construct the full path to the audio file from the project root
                        audio_file_full_path = os.path.join(APP_BASE_DIR, path_from_root)
                        logging.info(f"Attempting to send file: {audio_file_full_path}")

                        if os.path.exists(audio_file_full_path):
                            await interaction.followup.send(
                                content=f"Here's your generated stem for \"{prompt}\" (mocked: {selected_filename}):",
                                file=discord.File(audio_file_full_path, filename=selected_filename)
                            )
                        else:
                            logging.error(f"Audio file not found at path: {audio_file_full_path}")
                            await interaction.followup.send(
                                f"Backend selected '{selected_filename}', but I couldn't find the file to send it. Please check server logs.",
                                ephemeral=True
                            )
                    else:
                        logging.error(f"Backend response missing key audio file information: {backend_response_json}")
                        await interaction.followup.send(
                            "Sorry, the backend response was incomplete. Could not retrieve audio file information.",
                            ephemeral=True
                        )
                else:
                    error_text = await response.text()
                    logging.error(f"Backend error. Status: {response.status}, Response: {error_text}")
                    await interaction.followup.send(
                        f"Sorry, backend error (Status: {response.status}). Try again later.",
                        ephemeral=True
                    )
    except aiohttp.ClientConnectorError as e:
        logging.error(f"Cannot connect to backend: {e}")
        await interaction.followup.send(
            "Sorry, I couldn't connect to the music generation service. It might be down.",
            ephemeral=True
        )
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)
        await interaction.followup.send(
            "An unexpected error occurred. Please try again later.",
            ephemeral=True
        )

if __name__ == "__main__":
    if not DISCORD_BOT_TOKEN:
        logging.critical("DISCORD_BOT_TOKEN is not set. Bot cannot start.")
    else:
        try:
            bot.run(DISCORD_BOT_TOKEN)
        except discord.LoginFailure:
            logging.error("Login to Discord failed. Check token.")
        except Exception as e:
            logging.error(f"Error running bot: {e}")
