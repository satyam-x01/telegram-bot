"""Premium purchase and one-time code redemption flow."""
from pathlib import Path

from telegram import ForceReply, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

import config
from database import db
from utils import escape_md

PREMIUM_PRICE = "₹50 (about US$0.60)"
CODE_EXPORT = Path(__file__).resolve().parent.parent / "premium_codes.txt"


def _is_owner(user) -> bool:
    if not user:
        return False
    owner = config.OWNER_USERNAME.lstrip("@").lower()
    return bool(user.username and user.username.lstrip("@").lower() == owner) or db.is_dev_user(user.id)


async def premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    owner_handle = config.OWNER_USERNAME
    safe_owner_handle = escape_md(owner_handle)
    owner_url = f"https://t.me/{owner_handle.lstrip('@')}"
    if db.is_premium_user(user.id):
        text = (
            "💎 *SHIBH PREMIUM ACTIVE*\n\n"
            "✅ *Unlimited AI Song Finder* — text descriptions\n"
            "✅ *Unlimited Voice Tune Finder* — hum/voice-note matching\n"
            "✅ *20 Premium private tools*\n"
            "✅ VIP badge and future all-in-one VIP upgrades\n\n"
            "Your account has permanent Premium access."
        )
        keyboard = [
            [InlineKeyboardButton("🧰 Open 20 Premium Tools", callback_data="premium_tools")],
            [InlineKeyboardButton("👑 Contact Owner", url=owner_url)],
        ]
    else:
        text = (
            "💎 *SHIBH PREMIUM*\n\n"
            "Unlock Premium access and receive your personal activation code.\n\n"
            f"💰 *Price:* `{PREMIUM_PRICE}`\n"
            f"👑 *Purchase from Admin/Owner:* {safe_owner_handle}\n\n"
            "After payment, ask the owner for one unused 6-digit code. Each code can be used only once by one user."
        )
        keyboard = [
            [InlineKeyboardButton("👑 Purchase from Owner", url=owner_url)],
            [InlineKeyboardButton("🔢 Enter 6-Digit Premium Code", callback_data="premium_enter_code")],
        ]
    await update.effective_message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))


async def premium_enter_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["awaiting_premium_code"] = True
    await update.callback_query.message.reply_text(
        "🔐 *Enter your 6-digit Premium code*\n\nSend only the six numbers, just like an OTP.\nExample: `123456`",
        parse_mode="Markdown",
        reply_markup=ForceReply(selective=True),
    )


async def redeem_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = context.args[0].strip() if context.args else ""
    if not code:
        context.user_data["awaiting_premium_code"] = True
        await update.effective_message.reply_text("Usage: `/redeem 123456`\n\nOr send your six-digit code now.", parse_mode="Markdown")
        return
    await redeem_code(update, context, code)


async def redeem_code(update: Update, context: ContextTypes.DEFAULT_TYPE, code: str):
    context.user_data.pop("awaiting_premium_code", None)
    if not code.isdigit() or len(code) != 6:
        await update.effective_message.reply_text("❌ Code must contain exactly 6 digits. Please try again.")
        return
    result = db.redeem_premium_code_status(update.effective_user.id, code)
    if result == "already_premium":
        await update.effective_message.reply_text("💎 Your Premium is already active.")
        return
    if result == "redeemed":
        await update.effective_message.reply_text(
            "🎉 *SHIBH PREMIUM ACTIVATED!* 💎\n\nYour code has been securely linked to this Telegram account.",
            parse_mode="Markdown",
        )
    elif result == "already_used":
        await update.effective_message.reply_text("⚠️ This premium code was already used by another account. Please contact the owner.")
    else:
        await update.effective_message.reply_text("❌ Invalid code. Please check the six digits and try again.")


async def handle_premium_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not context.user_data.get("awaiting_premium_code"):
        return False
    await redeem_code(update, context, update.effective_message.text.strip())
    return True


async def premium_codes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_owner(update.effective_user):
        await update.effective_message.reply_text("❌ Only the bot owner can generate premium code exports.")
        return
    await generate_and_send_codes(update, context)


async def generate_and_send_codes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_owner(update.effective_user):
        await update.callback_query.answer("Only the owner can generate codes.", show_alert=True)
        return
    status = await update.effective_message.reply_text("⏳ Creating 1,00,000 unique premium codes. Please wait...")
    try:
        total_before, _ = db.premium_stats()
        codes = db.create_premium_codes(100_000) if total_before == 0 else db.get_premium_codes()
        CODE_EXPORT.write_text("\n".join(codes) + "\n", encoding="utf-8")
        total, redeemed = db.premium_stats()
        with CODE_EXPORT.open("rb") as export_file:
            await update.effective_message.reply_document(
                document=export_file,
                filename="premium_codes.txt",
                caption=(
                    "💎 *SHIBH PREMIUM CODES*\n\n"
                    f"Total codes: `{total}` | Redeemed: `{redeemed}`\n"
                    "Keep this file private; each code activates one account."
                ),
                parse_mode="Markdown",
            )
        await status.delete()
    except Exception as exc:
        await status.edit_text(f"❌ Could not create code export: `{exc}`", parse_mode="Markdown")
