import asyncio
import os
import time
import sys
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message

# =============== FIX FOR EVENT LOOP ERROR ================
if sys.version_info[0] == 3 and sys.version_info[1] >= 10:
    import asyncio
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

# =============== CONFIG - ENVIRONMENT VARIABLES ================
API_ID = int(os.environ.get("API_ID", 39035274))
API_HASH = os.environ.get("API_HASH", "6a0b24e16c4bea2bbc975b7dbb0c1e64")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8931408596:AAH-7SkyKtohZqKPE8ixyEfCV04h_rXagc8")
OWNER_ID = int(os.environ.get("OWNER_ID", 8722144519))

# =============== BOT INIT ================
app = Client(
    "spam_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# =============== SPAM ACTIVE TRACKER ================
spam_active = {}

# =============== CHECK OWNER ONLY ================
async def is_owner(user_id):
    return user_id == OWNER_ID

# =============== GET TARGET MENTION ================
async def get_target_mention(client, target_input, message):
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
        return target_user.mention, target_user.id
    
    if target_input and target_input.startswith("@"):
        try:
            target_user = await client.get_users(target_input)
            return target_user.mention, target_user.id
        except:
            return target_input, None
    
    if target_input and target_input.isdigit():
        try:
            target_user = await client.get_users(int(target_input))
            return target_user.mention, target_user.id
        except:
            return f"`{target_input}`", None
    
    return None, None

# =============== SPAM FUNCTION - WITH TAG ================
async def spam_loop(client, chat_id, target_mention, spam_message, count):
    global spam_active
    
    spam_active[chat_id] = True
    sent = 0
    
    final_message = f"{target_mention} {spam_message}"
    
    try:
        if count == -1:
            await client.send_message(
                chat_id,
                f"╔══════════════════════╗\n"
                f"   🔥 **UNLIMITED SPAM** 🔥\n"
                f"╚══════════════════════╝\n\n"
                f"🎯 **Target:** {target_mention}\n"
                f"📝 **Message:** `{spam_message[:50]}`\n"
                f"♾️ **Mode:** UNLIMITED\n"
                f"🛑 **Stop:** `.stopspam`\n\n"
                f"✅ Spam shuru ho gaya!"
            )
            
            while spam_active.get(chat_id, False):
                try:
                    await client.send_message(chat_id, final_message)
                    sent += 1
                    if sent % 100 == 0:
                        print(f"📊 Sent {sent} messages")
                except Exception as e:
                    if "flood" in str(e).lower():
                        await asyncio.sleep(1)
                    continue
                await asyncio.sleep(0)
        else:
            status_msg = await client.send_message(
                chat_id,
                f"⏳ Spamming `{count}` messages to {target_mention}..."
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
                f"✅ **Spam Complete!**\n"
                f"📊 Sent: `{sent}/{count}` messages\n"
                f"🎯 Target: {target_mention}"
            )
    except Exception as e:
        print(f"Spam error: {e}")
    finally:
        spam_active[chat_id] = False

# =============== SPAM COMMAND ================
@app.on_message(filters.command("spam", prefixes=".") & filters.group)
async def spam_command(client, message: Message):
    if message.from_user.id != OWNER_ID:
        await message.reply_text(f"❌ Sirf owner! ID: `{OWNER_ID}`")
        return
    
    chat_id = message.chat.id
    
    if spam_active.get(chat_id, False):
        await message.reply_text("❌ Spam already active! Use `.stopspam` first.")
        return
    
    parts = message.text.split(maxsplit=3)
    
    if len(parts) < 2 and not message.reply_to_message:
        await message.reply_text(
            f"⚠️ **Usage:** `.spam @username count message`\n\n"
            f"📝 **Examples:**\n"
            f"• `.spam @user 50 Hello`\n"
            f"• `.spam @user unlimited MKC`\n"
            f"• Reply to user → `.spam 50 hello`\n\n"
            f"🛑 **Stop:** `.stopspam`"
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
        await message.reply_text("❌ Please tag a user or reply to a message!")
        return
    
    if not target_mention:
        await message.reply_text("❌ Invalid user!")
        return
    
    count = -1
    spam_msg = ""
    
    if len(parts) > arg_index:
        try:
            count = int(parts[arg_index])
            if len(parts) > arg_index + 1:
                spam_msg = parts[arg_index + 1]
            else:
                await message.reply_text("❌ Message likhna bhi zaroori hai!")
                return
        except ValueError:
            spam_msg = parts[arg_index]
            count = -1
    
    if not spam_msg:
        await message.reply_text("❌ Kuch message likho!")
        return
    
    if str(count).lower() in ["unlimited", "inf", "infinite", "0"]:
        count = -1
    
    try:
        await message.delete()
    except:
        pass
    
    asyncio.create_task(spam_loop(client, chat_id, target_mention, spam_msg, count))

# =============== STOP SPAM ================
@app.on_message(filters.command("stopspam", prefixes=".") & filters.group)
async def stop_spam(client, message: Message):
    if message.from_user.id != OWNER_ID:
        await message.reply_text("❌ Sirf owner stop kar sakta hai!")
        return
    
    chat_id = message.chat.id
    
    if not spam_active.get(chat_id, False):
        await message.reply_text("❌ Koi active spam nahi hai!")
        return
    
    spam_active[chat_id] = False
    
    try:
        await message.delete()
    except:
        pass
    
    await client.send_message(chat_id, "🛑 **SPAM STOPPED!**")

# =============== ALIVE CHECK ================
@app.on_message(filters.command("alive", prefixes="."))
async def alive_command(client, message: Message):
    if message.from_user.id != OWNER_ID:
        return
    
    await message.reply_text(
        f"✅ **BOT ONLINE**\n"
        f"👑 Owner: `{OWNER_ID}`\n"
        f"⚡ Status: READY\n"
        f"💡 `.spam @user count message`"
    )

# =============== START ================
@app.on_message(filters.command("start", prefixes="."))
async def start_command(client, message: Message):
    if message.from_user.id != OWNER_ID:
        await message.reply_text(f"❌ Sirf owner! ID: `{OWNER_ID}`")
        return
    
    await message.reply_text(
        f"🔥 **SPAM BOT** 🔥\n\n"
        f"👑 Owner: `{OWNER_ID}`\n"
        f"📝 `.spam @user 50 message`\n"
        f"🛑 `.stopspam`\n"
        f"💡 Har message mein TAG hoga!"
    )

# =============== MAIN ================
if __name__ == "__main__":
    print("=" * 50)
    print("🔥 SPAM BOT STARTED 🔥")
    print("=" * 50)
    print(f"👑 Owner ID: {OWNER_ID}")
    print(f"⚡ Mode: ONLY OWNER CAN USE")
    print(f"💡 Feature: TAG with every message")
    print("=" * 50)
    
    app.run()
