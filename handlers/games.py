import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import db
from utils import escape_md

async def dice_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Roll a dice 🎲"""
    if update.message:
        msg = await update.message.reply_dice(emoji="🎲")
        score = msg.dice.value
        await update.message.reply_text(f"🎲 *You rolled a {score}!*", parse_mode="Markdown")

async def dart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Throw a dart 🎯"""
    if update.message:
        msg = await update.message.reply_dice(emoji="🎯")
        score = msg.dice.value
        result = "Bullseye! 🎯🔥" if score == 6 else f"You scored {score}/6 points!"
        await update.message.reply_text(f"🎯 *{result}*", parse_mode="Markdown")

async def basketball_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Play Basketball 🏀"""
    if update.message:
        msg = await update.message.reply_dice(emoji="🏀")
        score = msg.dice.value
        result = "SWISH! Perfect Basket! 🏀🔥" if score in [4, 5] else "Missed the basket! Try again! 🏀"
        await update.message.reply_text(f"🏀 *{result}*", parse_mode="Markdown")

async def football_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Play Football ⚽"""
    if update.message:
        msg = await update.message.reply_dice(emoji="⚽")
        score = msg.dice.value
        result = "GOOOAALLL! ⚽🔥" if score in [3, 4, 5] else "Saved by the goalkeeper! ⚽"
        await update.message.reply_text(f"⚽ *{result}*", parse_mode="Markdown")

async def slot_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Play Slot Machine / Jackpot 🎰"""
    if update.message:
        msg = await update.message.reply_dice(emoji="🎰")
        score = msg.dice.value
        result = "JACKPOT WINNER! 🎰🎉" if score == 64 else f"Slot combination score: {score}! Try again!"
        await update.message.reply_text(f"🎰 *{result}*", parse_mode="Markdown")

async def bowling_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Play Bowling 🎳"""
    if update.message:
        msg = await update.message.reply_dice(emoji="🎳")
        score = msg.dice.value
        result = "STRIKE! 🎳🔥 All pins down!" if score == 6 else f"Knocked down {score} pins!"
        await update.message.reply_text(f"🎳 *{result}*", parse_mode="Markdown")

async def ludo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Play Ludo 🎲"""
    if update.message:
        msg = await update.message.reply_dice(emoji="🎲")
        score = msg.dice.value
        extra = "🎉 Extra Turn! Move 6 steps & roll again!" if score == 6 else f"Move {score} steps on the Ludo board!"
        await update.message.reply_text(f"🎲 *Ludo Roll:* {score}\n\n{extra}", parse_mode="Markdown")

async def couple_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Pick Couple of the Day in group ❤️"""
    chat = update.effective_chat
    if chat.type == "private":
        await update.message.reply_text("❌ *Couple of the Day works in Group Chats!* Add me to a group to use this feature ❤️", parse_mode="Markdown")
        return

    cached = db.get_couple_of_day(chat.id)
    if cached:
        u1_name = escape_md(cached["user1_name"])
        u2_name = escape_md(cached["user2_name"])
        msg_text = (
            f"❤️ *COUPLE OF THE DAY* ❤️\n\n"
            f"👩‍❤️‍👨 Today's Chosen Couple:\n"
            f"✨ *{u1_name}* + *{u2_name}* = 💞\n\n"
            f"🎉 Congratulations to the sweet pair of the day!"
        )
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="menu_extra")]]
        await update.message.reply_text(msg_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    user = update.effective_user
    user1_name = user.first_name
    user1_id = user.id

    bot_user = await context.bot.get_me()
    user2_name = "Lovely Partner"
    user2_id = bot_user.id

    db.set_couple_of_day(chat.id, user1_id, user1_name, user2_id, user2_name)
    u1_safe = escape_md(user1_name)
    u2_safe = escape_md(user2_name)

    msg_text = (
        f"❤️ *COUPLE OF THE DAY* ❤️\n\n"
        f"👩‍❤️‍👨 Today's Chosen Couple:\n"
        f"✨ *{u1_safe}* + *{u2_safe}* = 💞\n\n"
        f"🎉 Congratulations to the sweet pair of the day!"
    )
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="menu_extra")]]
    await update.message.reply_text(msg_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def love_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Calculate Love Birds match percentage 💘"""
    user = update.effective_user
    target_name = "Your Soulmate"
    if context.args:
        target_name = " ".join(context.args)
    elif update.message and update.message.reply_to_message:
        target_name = update.message.reply_to_message.from_user.first_name

    percent = random.randint(65, 100)
    u_name = escape_md(user.first_name)
    t_name = escape_md(target_name)

    if percent > 90:
        vibe = "💖 Match Made in Heaven! Pure True Love!"
    elif percent > 75:
        vibe = "💕 Strong Romantic Chemistry!"
    else:
        vibe = "💓 Sweet Connection & Good Vibrations!"

    love_text = (
        f"💘 *LOVE BIRDS MATCH CALCULATOR* 💘\n\n"
        f"👤 *Person 1:* {u_name}\n"
        f"👤 *Person 2:* {t_name}\n\n"
        f"📊 *Love Score:* `{percent}%` [{ '❤️' * (percent // 10) }]\n"
        f"✨ *Vibe Check:* {vibe}"
    )
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="menu_extra")]]
    await update.message.reply_text(love_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
