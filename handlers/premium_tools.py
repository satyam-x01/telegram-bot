"""Twenty locally processed tools available only to Premium members."""
import base64
import datetime as dt
import hashlib
import html
import json
import math
import secrets
import urllib.parse
import uuid

from telegram import ForceReply, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from database import db

TOOLS = {
    "password": ("🔐 Password Generator", False), "uuid": ("🆔 UUID Generator", False),
    "hash": ("#️⃣ SHA-256 Hash", True), "b64encode": ("🔒 Base64 Encode", True),
    "b64decode": ("🔓 Base64 Decode", True), "urlencode": ("🔗 URL Encode", True),
    "urldecode": ("🔓 URL Decode", True), "jsonformat": ("🧾 JSON Formatter", True),
    "jsonminify": ("🗜️ JSON Minifier", True), "wordstats": ("📝 Word Counter", True),
    "case": ("🔤 Text Case Converter", True), "reverse": ("🔄 Reverse Text", True),
    "bmi": ("⚖️ BMI Calculator", True), "age": ("🎂 Age Calculator", True),
    "gst": ("🧾 GST Calculator", True), "emi": ("💰 EMI Calculator", True),
    "picker": ("🎯 Random Picker", True), "dice": ("🎲 Smart Dice", False),
    "colors": ("🎨 Color Palette", False), "timestamp": ("🕒 Timestamp Tool", False),
}

HELP = {
    "hash": "Send text to hash.", "b64encode": "Send text to encode.", "b64decode": "Send Base64 text to decode.",
    "urlencode": "Send text or URL to encode.", "urldecode": "Send encoded URL/text to decode.",
    "jsonformat": "Send valid JSON.", "jsonminify": "Send valid JSON.", "wordstats": "Send text.",
    "case": "Send text to convert.", "reverse": "Send text to reverse.", "bmi": "Send: `weight_kg height_cm` — e.g. `70 175`.",
    "age": "Send birth date: `YYYY-MM-DD` — e.g. `2005-08-15`.", "gst": "Send: `amount gst_percent` — e.g. `500 18`.",
    "emi": "Send: `principal annual_rate months` — e.g. `100000 12 12`.", "picker": "Send comma-separated choices — e.g. `Pizza,Burger,Roll`.",
}


def _active(user_id: int) -> bool:
    return db.is_premium_user(user_id)


async def show_premium_tools(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _active(update.effective_user.id):
        await update.effective_message.reply_text("🔒 These 20 tools are Premium-only. Use /premium to activate access.")
        return
    keys = list(TOOLS)
    keyboard = []
    for i in range(0, len(keys), 2):
        keyboard.append([InlineKeyboardButton(TOOLS[key][0], callback_data=f"premium_tool_{key}") for key in keys[i:i + 2]])
    keyboard.append([InlineKeyboardButton("💎 Premium Status", callback_data="premium_menu")])
    await update.effective_message.reply_text(
        "💎 <b>SHIBH PREMIUM TOOLKIT</b>\n\n20 private tools — choose any tool below.",
        parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def choose_premium_tool(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _active(update.effective_user.id):
        await update.callback_query.answer("Premium access required. Open /premium.", show_alert=True)
        return
    key = update.callback_query.data.removeprefix("premium_tool_")
    if key not in TOOLS:
        await update.callback_query.answer("Unknown tool.", show_alert=True)
        return
    title, needs_input = TOOLS[key]
    if needs_input:
        context.user_data["premium_tool"] = key
        await update.callback_query.message.reply_text(f"{title}\n\n{HELP[key]}", parse_mode="Markdown", reply_markup=ForceReply(selective=True))
        return
    await _send_result(update, key, "")


def _result(key: str, value: str) -> str:
    if key == "password":
        alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#$%"
        return "<code>" + "".join(secrets.choice(alphabet) for _ in range(16)) + "</code>"
    if key == "uuid": return f"<code>{uuid.uuid4()}</code>"
    if key == "hash": return f"<code>{hashlib.sha256(value.encode()).hexdigest()}</code>"
    if key == "b64encode": return f"<code>{base64.b64encode(value.encode()).decode()}</code>"
    if key == "b64decode": return f"<code>{html.escape(base64.b64decode(value.encode(), validate=True).decode())}</code>"
    if key == "urlencode": return f"<code>{html.escape(urllib.parse.quote(value, safe=''))}</code>"
    if key == "urldecode": return f"<code>{html.escape(urllib.parse.unquote(value))}</code>"
    if key == "jsonformat": return f"<pre>{html.escape(json.dumps(json.loads(value), indent=2, ensure_ascii=False))}</pre>"
    if key == "jsonminify": return f"<code>{html.escape(json.dumps(json.loads(value), separators=(',', ':'), ensure_ascii=False))}</code>"
    if key == "wordstats":
        return f"Words: <b>{len(value.split())}</b>\nCharacters: <b>{len(value)}</b>\nLines: <b>{len(value.splitlines())}</b>"
    if key == "case": return f"UPPER: <code>{html.escape(value.upper())}</code>\nLOWER: <code>{html.escape(value.lower())}</code>\nTITLE: <code>{html.escape(value.title())}</code>"
    if key == "reverse": return f"<code>{html.escape(value[::-1])}</code>"
    if key == "bmi":
        weight, height = map(float, value.replace(",", " ").split()[:2]); bmi = weight / (height / 100) ** 2
        category = "Underweight" if bmi < 18.5 else "Healthy" if bmi < 25 else "Overweight" if bmi < 30 else "Obesity"
        return f"BMI: <b>{bmi:.1f}</b>\nCategory: <b>{category}</b>"
    if key == "age":
        born = dt.date.fromisoformat(value); today = dt.date.today(); years = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        return f"Age: <b>{years} years</b>"
    if key == "gst":
        amount, rate = map(float, value.replace(",", " ").split()[:2]); tax = amount * rate / 100
        return f"GST: <b>₹{tax:.2f}</b>\nTotal: <b>₹{amount + tax:.2f}</b>"
    if key == "emi":
        principal, annual_rate, months = map(float, value.replace(",", " ").split()[:3]); months = int(months); rate = annual_rate / 1200
        emi = principal / months if rate == 0 else principal * rate * (1 + rate) ** months / ((1 + rate) ** months - 1)
        return f"Monthly EMI: <b>₹{emi:.2f}</b>\nTotal payable: <b>₹{emi * months:.2f}</b>"
    if key == "picker":
        choices = [part.strip() for part in value.split(",") if part.strip()]
        if len(choices) < 2: raise ValueError("Provide at least two comma-separated choices")
        return f"Selected: <b>{html.escape(secrets.choice(choices))}</b>"
    if key == "dice": return f"🎲 You rolled: <b>{secrets.randbelow(6) + 1}</b>"
    if key == "colors": return "\n".join(f"<code>#{secrets.token_hex(3).upper()}</code>" for _ in range(5))
    if key == "timestamp":
        now = dt.datetime.now(dt.timezone.utc)
        return f"Unix: <code>{int(now.timestamp())}</code>\nUTC: <code>{now.strftime('%Y-%m-%d %H:%M:%S')}</code>"
    raise ValueError("Tool unavailable")


async def _send_result(update: Update, key: str, value: str):
    try:
        result = _result(key, value)
        await update.effective_message.reply_text(f"{TOOLS[key][0]}\n\n{result}", parse_mode="HTML")
    except Exception as exc:
        await update.effective_message.reply_text(f"❌ Invalid input: {html.escape(str(exc))}", parse_mode="HTML")


async def handle_premium_tool_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    key = context.user_data.pop("premium_tool", None)
    if not key:
        return False
    if not _active(update.effective_user.id):
        await update.effective_message.reply_text("🔒 Premium access is required. Use /premium.")
        return True
    await _send_result(update, key, update.effective_message.text.strip())
    return True
