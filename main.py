import discord
from discord.ext import commands
from discord.ui import Button, View
import requests
import uuid
import json

# ==========================================
# CONFIGURATION
# ==========================================
# PASTE YOUR TOKEN HERE
BOT_TOKEN = "MTQ1MjU2NzY0Njc3NTI4MzcxNA.GERt2K.mQiH5LSEJxZi6uI0LwQFsWck6FryRTkG94bPFg" 
FIREBASE_URL = "https://key-verifier-66677-default-rtdb.firebaseio.com/SCRIPT_DATA"
ADMIN_PASSWORD = "43924"
# ==========================================

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

def get_firebase_data(path):
    try:
        url = f"{FIREBASE_URL}/{path}.json"
        response = requests.get(url)
        return response.json() or {}
    except: return None

def write_firebase_data(path, data, method="PATCH"):
    try:
        url = f"{FIREBASE_URL}/{path}.json"
        if method == "PATCH": requests.patch(url, json=data)
        elif method == "PUT": requests.put(url, json=data)
        elif method == "DELETE": requests.delete(url)
        return True
    except: return False

class ConfirmView(View):
    def __init__(self): super().__init__(timeout=60)
    @discord.ui.button(label="Yes, Proceed", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer(ephemeral=True)
        try: await interaction.message.delete()
        except: pass
        try:
            user_id = str(interaction.user.id)
            user_check = get_firebase_data(f"discord_users/{user_id}")
            if user_check:
                await interaction.followup.send(f"❌ **You already have a key!**\nKey: `{user_check}`", ephemeral=True)
                return
            new_key = str(uuid.uuid4())
            write_firebase_data("keys", {new_key: {"used": False, "ownerID": 0}}, "PATCH")
            write_firebase_data("discord_users", {user_id: new_key}, "PATCH")
            await interaction.followup.send(f"✅ **Key Generated**\n```{new_key}```", ephemeral=True)
        except Exception as e: await interaction.followup.send(f"Error: {e}", ephemeral=True)
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction, button): await interaction.response.edit_message(content="Cancelled.", view=None)

class GeneratorView(View):
    def __init__(self): super().__init__(timeout=None) 
    @discord.ui.button(label="Generate Script Key", style=discord.ButtonStyle.blurple, custom_id="gen_btn")
    async def generate_callback(self, interaction, button): await interaction.response.send_message("Generate new key?", view=ConfirmView(), ephemeral=True)

@bot.event
async def on_ready(): print(f'Logged in as {bot.user}')
@bot.command()
async def setup(ctx): await ctx.send("## Script Key Generator", view=GeneratorView())
@bot.command()
async def clearsetups(ctx):
    if ctx.author.guild_permissions.administrator:
        await ctx.message.delete()
        await ctx.channel.purge(limit=20, check=lambda m: m.author == bot.user)
@bot.command()
async def resetkey(ctx, member: discord.Member = None):
    if not ctx.author.guild_permissions.administrator: return
    target_id = str(member.id) if member else str(ctx.author.id)
    existing_key = get_firebase_data(f"discord_users/{target_id}")
    if existing_key:
        write_firebase_data(f"keys/{existing_key}", None, "DELETE")
        write_firebase_data(f"discord_users/{target_id}", None, "DELETE")
        await ctx.send(f"✅ Key reset for <@{target_id}>.")
    else: await ctx.send("❌ No key found.")
@bot.command()
async def resetallkeys(ctx, password: str = None):
    if password == ADMIN_PASSWORD:
        write_firebase_data("", {"keys": {}, "discord_users": {}}, "PUT")
        await ctx.send("⚠️ **DATABASE WIPED** ⚠️")

try:
    bot.run(BOT_TOKEN)
except Exception as e:
    print(f"Error: {e}")
