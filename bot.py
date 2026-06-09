
import asyncio
import os
import time
import sys
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

# =============== PORT WEB SERVER FOR RENDER ================
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        html = """
        <!DOCTYPE html>
        <html>
        <head><title>Spam Bot</title></head>
        <body style="background: #1a1a2e; color: white; text-align: center; font-family: Arial;">
            <h1>SPAM BOT IS RUNNING</h1>
            <p>Bot is active and ready to spam!</p>
            <p>Owner ID: 8722144519</p>
            <p>Status: ONLINE</p>
        </body>
        </html>
        """
        self.wfile.write(html.encode('utf-8'))
    
    def log_message(self, format, *args):
        pass

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"Web server running on port {port}")
    server.serve_forever()

web_thread = Thread(target=run_web_server, daemon=True)
web_thread.start()
print("Web server thread started")

# =============== FIX FOR EVENT LOOP ERROR ================
if sys.version_info[0] == 3 and sys.version_info[1] >= 10:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

# =============== CONFIG ================
API_ID = int(os.environ.get("API_ID", 39035274))
API_HASH = os.environ.get("API_HASH", "6a0b24e16c4bea2bbc975b7dbb0c1e64")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8931408596:AAH-7SkyKtohZqKPE8ixyEfCV04h_rXagc8")
OWNER_ID = int(os.environ.get("OWNER_ID", 8722144519))

app = Client("spam_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

spam_active = {}

# =============== GET CLICKABLE MENTION ================
async def get_target_mention(client, target_input, message):
    """
    Returns clickable mention for ANY user - even without username
    """
    target_user = None
    
    # Case 1: Reply to a message
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
        if target_user:
            # Pyrogram's .mention creates clickable link
            return target_user.mention, target_user.id
    
    # Case 2: @username mention
    if target_input and target_input.startswith("@"):
        try:
            target_user = await client.get_users(target_input)
            return target_user.mention, target_user.id
        except:
            return target_input, None
    
    # Case 3: Direct user ID
    if target_input and target_input.isdigit():
        try:
            target_user = await client.get_users(int(target_input))
            return target_user.mention, target_user.id
        except:
            return f"`{target_input}`", None
    
    return None, None

# =============== GET BOT MENTION ================
async def get_bot_mention():
    """Returns bot's own clickable mention"""
    me = await app.get_me()
    return me.mention

# =============== SPAM LOOP WITH CLICKABLE MENTION ================
async def spam_loop(client, chat_id, target_mention, spam_message, count):
    global spam_active
    
    spam_active[chat_id] = True
    sent = 0
    
    # Final message with clickable mention
    final_message = f"{target_mention} {spam_message}"
    
    try:
        if count == -1:
            await client.send_message(
                chat_id,
                f"UNLIMITED SPAM\n\n"
                f"Target: {target_mention}\n"
                f"Message: `{spam_message[:50]}`\n"
                f"Stop: .stopspam\n\n"
                f"Spam started!"
            )
            
            while spam_active.get(chat_id, False):
                try:
                    await client.send_message(chat_id, final_message)
                    sent += 1
                    if sent % 100 == 0:
                        print(f"Sent {sent} messages")
                except Exception as e:
                    if "flood" in str(e).lower():
                        await asyncio.sleep(1)
                    continue
                await asyncio.sleep(0)
        else:
            status_msg = await client.send_message(
                chat_id,
                f"Spamming {count} messages to {target_mention}..."
            )
            
            for i in range(count):
                if not spam_active.get(chat_id, True):
                    break
                try:
                    await client.send_message(chat_id, final_message)
                    sent += 1
                except:
                    pass
                await asyncio.sleep(0)
            
            await status_msg.edit_text(
                f"Spam Complete!\n"
                f"Sent: {sent}/{count} messages\n"
                f"Target: {target_mention}"
            )
    except Exception as e:
        print(f"Spam error: {e}")
    finally:
        spam_active[chat_id] = False

# =============== SPAM COMMAND ================
@app.on_message(filters.command("spam", prefixes=".") & filters.group)
async def spam_command(client, message: Message):
    if message.from_user.id != OWNER_ID:
        await message.reply_text(f"Only owner! ID: `{OWNER_ID}`")
        return
    
    chat_id = message.chat.id
    
    if spam_active.get(chat_id, False):
        await message.reply_text("Spam already active! Use `.stopspam` first.")
        return
    
    parts = message.text.split(maxsplit=3)
    
    if len(parts) < 2 and not message.reply_to_message:
        await message.reply_text(
            f"Usage: `.spam @username count message`\n\n"
            f"Examples:\n"
            f".spam @user 50 Hello\n"
            f".spam @user unlimited MKC\n"
            f"Reply to user -> .spam 50 hello\n\n"
            f"Note: Mention will be CLICKABLE even without username!\n\n"
            f"Stop: .stopspam"
        )
        return
    
    target_mention = None
    arg_index = 1
    
    if len(parts) >= 2 and (parts[1].startswith("@") or parts[1].isdigit()):
        target_mention, _ = await get_target_mention(client, parts[1], message)
        arg_index = 2
    elif message.reply_to_message:
        target_mention, _ = await get_target_mention(client, None, message)
        arg_index = 1
    else:
        await message.reply_text("Please tag a user or reply to a message!")
        return
    
    if not target_mention:
        await message.reply_text("Invalid user!")
        return
    
    count = -1
    spam_msg = ""
    
    if len(parts) > arg_index:
        try:
            count = int(parts[arg_index])
            if len(parts) > arg_index + 1:
                spam_msg = parts[arg_index + 1]
            else:
                await message.reply_text("Message likhna bhi zaroori hai!")
                return
        except ValueError:
            spam_msg = parts[arg_index]
            count = -1
    
    if not spam_msg:
        await message.reply_text("Kuch message likho!")
        return
    
    if str(count).lower() in ["unlimited", "inf", "infinite", "0"]:
        count = -1
    
    # Delete command message
    try:
        await message.delete()
    except:
        pass
    
    asyncio.create_task(spam_loop(client, chat_id, target_mention, spam_msg, count))

# =============== STOP SPAM ================
@app.on_message(filters.command("stopspam", prefixes=".") & filters.group)
async def stop_spam(client, message: Message):
    if message.from_user.id != OWNER_ID:
        await message.reply_text("Only owner can stop spam!")
        return
    
    chat_id = message.chat.id
    
    if not spam_active.get(chat_id, False):
        await message.reply_text("No active spam!")
        return
    
    spam_active[chat_id] = False
    
    try:
        await message.delete()
    except:
        pass
    
    await client.send_message(chat_id, "SPAM STOPPED!")

# =============== TEST MENTION COMMAND ================
@app.on_message(filters.command("testmention", prefixes="."))
async def test_mention(client, message: Message):
    """Test command to check if mention is clickable"""
    if message.from_user.id != OWNER_ID:
        return
    
    if message.reply_to_message:
        target = message.reply_to_message.from_user
        await message.reply_text(f"Testing clickable mention: {target.mention}\n\nClick on the name above! It should open profile.")
    else:
        await message.reply_text("Reply to any user with .testmention to check if mention is clickable")

# =============== ALIVE ================
@app.on_message(filters.command("alive", prefixes="."))
async def alive_command(client, message: Message):
    if message.from_user.id != OWNER_ID:
        return
    
    bot_mention = await get_bot_mention()
    await message.reply_text(
        f"BOT ONLINE\n"
        f"Owner: `{OWNER_ID}`\n"
        f"Bot: {bot_mention}\n"
        f"Status: READY\n"
        f"Command: .spam @user count message\n\n"
        f"Note: Mentions are CLICKABLE - even without username!"
    )

# =============== START ================
@app.on_message(filters.command("start", prefixes="."))
async def start_command(client, message: Message):
    if message.from_user.id != OWNER_ID:
        await message.reply_text(f"Only owner! ID: `{OWNER_ID}`")
        return
    
    bot_mention = await get_bot_mention()
    await message.reply_text(
        f"SPAM BOT\n\n"
        f"Owner: `{OWNER_ID}`\n"
        f"Bot: {bot_mention}\n\n"
        f"Commands:\n"
        f".spam @user 50 message\n"
        f".stopspam\n"
        f".testmention (reply to check clickable mention)\n\n"
        f"NOTE: Har message mein TARGET CLICKABLE hoga!\n"
        f"Bina username ke bhi profile open hogi!"
    )

# =============== MAIN ================
if __name__ == "__main__":
    print("=" * 50)
    print("SPAM BOT STARTED")
    print("=" * 50)
    print(f"Owner ID: {OWNER_ID}")
    print(f"Mode: ONLY OWNER CAN USE")
    print(f"Feature: CLICKABLE MENTIONS (even without username)")
    print(f"Port: {os.environ.get('PORT', 10000)}")
    print("=" * 50)
    
    app.run()
