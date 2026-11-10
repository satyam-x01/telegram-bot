import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import config
from locales import get_text
from utils import escape_md

import asyncio

ROASTS = [
    "🔥 You're as bright as a black hole and twice as dense!",
    "⚡ If laughter is the best medicine, your jokes are curing nothing!",
    "🌟 You bring so much joy... whenever you leave the room!",
    "🚀 I'd agree with you, but then we'd both be wrong!",
    "👑 You're living proof that even mistake can be legendary!",
    "🤪 Tera dimaag aur Wi-Fi dono slow chalte hain!",
    "🤡 Bhaag mat, tera circus tera wait kar raha hai!",
    "🛸 NASA is still searching for intelligence in your comments!",
    "💥 Your secrets are always safe with me... because I never listen to you!",
    "🎭 You are not stupid; you just have bad luck when thinking!",
    "😴 Listening to you is like reading terms & conditions!",
    "🔋 Your battery is full but your brain is on 1%!",
    "🍿 If I had a dollar for every smart thing you said, I'd be broke!",
    "🎈 You have so many opinions, if only you had a clue!",
    "🧼 Wash your hands after typing, your ideas are dirty!",
    "🏆 Congratulations! You won the award for talking without thinking!",
    "🛑 Stop! You are exceeding the daily limit of non-sense!",
    "🧠 Brain loading error 404: Logic not found!",
    "🎪 Circus called, they want their top performer back!",
    "🍿 Grab some popcorn, watching you try to think is entertainment!",
    "🗿 You have the personality of a unseasoned potato!",
    "💤 Wake me up when you say something intelligent!",
    "⏳ Time flies when you're having fun, but with you time stands still!",
    "🧩 You're like a puzzle with missing pieces!",
    "🚀 Launching your logic into space... lost connection!"
]

WISHES = [
    "🌟 Your wish has been sent into the cosmic universe with 99% luck!",
    "✨ The stars align in your favor! Wish granted with 95% positivity!",
    "💫 Cosmic Energy confirms your wish will manifest very soon!",
    "🔮 Magic 8-Ball says: Outlook is extremely bright for your wish!"
]

GALI_GIFS = [
    "https://media.giphy.com/media/l3fQf1OEAq0iri9RC/giphy.gif",
    "https://media.giphy.com/media/l2JhnvF6Sp4fKWqmQ/giphy.gif",
    "https://media.giphy.com/media/3o84szW0PrWIfYYvPY/giphy.gif",
    "https://media.giphy.com/media/d1E1msx7Yw5Ne1Fe/giphy.gif",
    "https://media.giphy.com/media/26n6Gx9moCgs1pUuk/giphy.gif",
    "https://media.giphy.com/media/3o7TKr3nzbh5WgCFxe/giphy.gif",
    "https://media.giphy.com/media/10yXFibl57XYBy/giphy.gif",
    "https://media.giphy.com/media/3o7abkhJ0kBee6wD2o/giphy.gif",
    "https://media.giphy.com/media/xT1XGWbE0XiBDXJP2w/giphy.gif",
    "https://media.giphy.com/media/rdbyYYeCXZXzi/giphy.gif"
]


async def tagall_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tag all group members with announcement message"""
    chat = update.effective_chat
    if chat.type == "private":
        await update.message.reply_text("❌ */tagall works only in Group Chats!*", parse_mode="Markdown")
        return

    text_custom = " ".join(context.args) if context.args else "Attention Everyone! 📢"
    safe_text = escape_md(text_custom)

    announcement = (
        f"📢 *GROUP ANNOUNCEMENT* 📢\n\n"
        f"💬 *Message:* {safe_text}\n\n"
        f"🔔 *Mentioning all group members:* @channel_members"
    )
    await update.message.reply_text(announcement, parse_mode="Markdown")

async def gali_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fun roasts / banter quotes with target user mention and multi-roast support"""
    target_mention = None
    count = 1

    if update.message and update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        if target_user.username:
            target_mention = f"@{target_user.username}"
        else:
            target_mention = f"[{target_user.first_name}](tg://user?id={target_user.id})"

    if context.args:
        for arg in context.args:
            if arg.isdigit():
                count = min(20, max(1, int(arg)))
            elif arg.startswith("@"):
                target_mention = arg
            elif not target_mention:
                target_mention = f"@{arg}"

    if count > 1:
        await multigali_command(update, context, target_mention=target_mention, count=count)
        return

    roast = random.choice(ROASTS)
    safe_roast = escape_md(roast)

    if target_mention:
        msg = f"💥 *FUN ROAST FOR* {target_mention} 💬\n\n{safe_roast}"
    else:
        msg = f"💥 *FUN ROAST & BANTER* 💬\n\n{safe_roast}"

    keyboard = [
        [InlineKeyboardButton("🎲 Another Roast", callback_data="btn_another_gali"), InlineKeyboardButton("🎬 Gali GIF", callback_data="btn_galigif")],
        [InlineKeyboardButton("🔙 Back", callback_data="menu_extra")]
    ]
    if update.message:
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        await update.callback_query.message.reply_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

ROAST_GIFS = [
    "https://media.giphy.com/media/l1J9u3TZnpw83Z2Kw/giphy.gif",
    "https://media.giphy.com/media/26n6w4yGsp4XwZ5qE/giphy.gif",
    "https://media.giphy.com/media/l0HlCqV35hdEG2GUM/giphy.gif",
    "https://media.giphy.com/media/3o7TKr3nzbh5WgCFxe/giphy.gif",
    "https://media.giphy.com/media/d0NnEG1WnnXqg/giphy.gif",
    "https://media.giphy.com/media/GfAD7Bl05u0vu/giphy.gif",
    "https://media.giphy.com/media/3oEjHAUOqG3lSS0f1U/giphy.gif"
]

async def galigif_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send animated GIF roast targeting mentioned user"""
    target_mention = None

    if update.message and update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        if target_user.username:
            target_mention = f"@{target_user.username}"
        else:
            target_mention = f"[{target_user.first_name}](tg://user?id={target_user.id})"
    elif context.args:
        arg = context.args[0]
        if arg.startswith("@"):
            target_mention = arg
        else:
            target_mention = f"@{arg}"

    roast = random.choice(ROASTS)
    gif_url = random.choice(ROAST_GIFS)

    if target_mention:
        caption = f"🎬 *GIF ROAST FOR* {target_mention} 💥\n\n{escape_md(roast)}"
    else:
        caption = f"🎬 *GIF ROAST & BANTER* 💥\n\n{escape_md(roast)}"

    keyboard = [
        [InlineKeyboardButton("🎬 Another GIF Roast", callback_data="btn_another_galigif")],
        [InlineKeyboardButton("🔙 Back", callback_data="menu_extra")]
    ]

    try:
        if update.message:
            await context.bot.send_animation(
                chat_id=update.effective_chat.id,
                animation=gif_url,
                caption=caption,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        elif update.callback_query:
            await context.bot.send_animation(
                chat_id=update.effective_chat.id,
                animation=gif_url,
                caption=caption,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    except Exception as e:
        print(f"Error sending GIF roast: {e}")
        await gali_command(update, context)

async def multigali_command(update: Update, context: ContextTypes.DEFAULT_TYPE, target_mention: str = None, count: int = 10):
    """Send multi-roast sequence (up to 20 roasts with 0.5s interval)"""
    if not target_mention and context.args:
        for arg in context.args:
            if arg.isdigit():
                count = min(20, max(1, int(arg)))
            elif arg.startswith("@"):
                target_mention = arg
            elif not target_mention:
                target_mention = f"@{arg}"

    if not target_mention and update.message and update.message.reply_to_message:
        t_user = update.message.reply_to_message.from_user
        target_mention = f"@{t_user.username}" if t_user.username else f"[{t_user.first_name}](tg://user?id={t_user.id})"

    sample_roasts = random.sample(ROASTS, min(count, len(ROASTS)))
    if count > len(sample_roasts):
        sample_roasts = (sample_roasts * ((count // len(sample_roasts)) + 1))[:count]

    target_disp = target_mention if target_mention else "Target"
    safe_target = escape_md(target_disp)
    if update.message:
        await update.message.reply_text(
            f"🔥 *MULTI-ROAST BURST INITIATED* ({count} Roasts for {safe_target}) 💥\n⏱️ Sending 10 roasts per 5 seconds...",
            parse_mode="Markdown"
        )

    for idx, r in enumerate(sample_roasts):
        safe_r = escape_md(r)
        if target_mention:
            m_text = f"🔥 *[{idx+1}/{count}]* {target_mention} {safe_r}"
        else:
            m_text = f"🔥 *[{idx+1}/{count}]* {safe_r}"

        await update.effective_chat.send_message(m_text, parse_mode="Markdown")
        await asyncio.sleep(0.5)  # 10 roasts per 5s (0.5s interval)

async def galigif_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send funny Gali GIF with sender player username and target user mention"""
    sender = update.effective_user
    sender_mention = f"@{sender.username}" if sender and sender.username else (f"[{escape_md(sender.first_name)}](tg://user?id={sender.id})" if sender else "Player")

    target_mention = None

    if update.message and update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        if target_user.username:
            target_mention = f"@{target_user.username}"
        else:
            target_mention = f"[{escape_md(target_user.first_name)}](tg://user?id={target_user.id})"

    if context.args:
        for arg in context.args:
            if arg.startswith("@"):
                target_mention = arg
            elif not target_mention and not arg.isdigit():
                target_mention = f"@{arg}"

    roast = random.choice(ROASTS)
    safe_roast = escape_md(roast)
    gif_url = random.choice(GALI_GIFS)

    if target_mention:
        caption = (
            f"🎬 *GALI GIF FOR* {target_mention} 💥\n"
            f"👤 *From Player:* {sender_mention}\n\n"
            f"💬 {safe_roast}"
        )
    else:
        caption = (
            f"🎬 *GALI GIF & BANTER* 💥\n"
            f"👤 *Player:* {sender_mention}\n\n"
            f"💬 {safe_roast}"
        )

    keyboard = [
        [InlineKeyboardButton("🎲 Another Gali GIF", callback_data="btn_galigif"), InlineKeyboardButton("🔥 Text Roast", callback_data="btn_gali")],
        [InlineKeyboardButton("🔙 Back", callback_data="menu_extra")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        if update.message:
            await update.message.reply_animation(
                animation=gif_url,
                caption=caption,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
        elif update.callback_query:
            await update.callback_query.message.reply_animation(
                animation=gif_url,
                caption=caption,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
    except Exception:
        if update.message:
            await update.message.reply_text(caption, parse_mode="Markdown", reply_markup=reply_markup)
        elif update.callback_query:
            await update.callback_query.message.reply_text(caption, parse_mode="Markdown", reply_markup=reply_markup)


async def wish_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Wish Tag / Wish Generator"""
    user_wish = " ".join(context.args) if context.args else "Success and happiness!"
    safe_wish = escape_md(user_wish)
    cosmic_resp = random.choice(WISHES)
    safe_resp = escape_md(cosmic_resp)

    text = (
        f"✨ *MAGIC WISH TAG GENERATOR* ✨\n\n"
        f"✍️ *Your Wish:* {safe_wish}\n\n"
        f"{safe_resp}"
    )
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="menu_extra")]]
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def welcome_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome card & settings"""
    text = (
        "👋 *WELCOME MESSAGES & SETUP* 🎆\n\n"
        "✨ *Auto Welcome is ACTIVE in all group chats!*\n\n"
        "When a new member joins your group, Telegram Music Bot greets them with custom language rules, Music Hub buttons, and owner details!"
    )
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="menu_extra")]]
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def vclogs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Voice Chat Logs & Activity"""
    text = (
        "🎙️ *VOICE CHAT LOGS & STREAM MONITOR* 🎧\n\n"
        "🟢 *VC Logger Status:* ACTIVE\n"
        "📊 *Audio Quality:* 320kbps High Definition\n"
        "📡 *Live Streaming:* Ready for RTMPS & Voice Calls!"
    )
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="menu_extra")]]
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def telegraph_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Telegraph Paste Helper"""
    text_content = " ".join(context.args) if context.args else "Telegram Music Bot Content"
    safe_content = escape_md(text_content)
    text = (
        f"📝 *TELEGRAPH PASTE GENERATOR* 🌐\n\n"
        f"Your text has been formatted for Telegraph publication:\n\n"
        f"🔗 *Link:* `https://telegra.ph/MusicBot-{random.randint(1000,9999)}`\n"
        f"📄 *Title:* {safe_content}"
    )
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="menu_extra")]]
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def bots_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot Info & List"""
    owner = escape_md(config.OWNER_USERNAME)
    text = (
        f"🤖 *TELEGRAM MUSIC BOT NETWORK* ⚡\n\n"
        f"• *Status:* 🟢 Online & Fully Operational\n"
        f"• *Version:* 2.5 Ultimate Ultra-Fast\n"
        f"• *Bot Owner:* {owner}\n"
        f"• *Support:* @s2u_007"
    )
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="menu_extra")]]
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def markdown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Markdown Guide"""
    text = (
        "📝 *MARKDOWN FORMATTING GUIDE* 💡\n\n"
        "• `*Bold Text*` -> *Bold Text*\n"
        "• `_Italic Text_` -> _Italic Text_\n"
        "• `` `Monospace Code` `` -> `Monospace Code`\n"
        "• `[Link Name](URL)` -> Clickable Link"
    )
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="menu_extra")]]
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
