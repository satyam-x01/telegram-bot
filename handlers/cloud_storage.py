import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes

import config
from database import db
from services.telegram_storage_service import storage_service

logger = logging.getLogger(__name__)

def get_five_action_keyboard(group_id: int) -> InlineKeyboardMarkup:
    """Returns the 5 requested action buttons: Back, Add, Add file/folder, Add photo, Add video."""
    keyboard = [
        [
            InlineKeyboardButton("🔙 Back", callback_data="cs_menu"),
            InlineKeyboardButton("➕ Add", callback_data=f"cs_mode_add_{group_id}")
        ],
        [
            InlineKeyboardButton("📁 Add File/Folder", callback_data=f"cs_mode_file_{group_id}"),
            InlineKeyboardButton("🖼️ Add Photo", callback_data=f"cs_mode_photo_{group_id}")
        ],
        [
            InlineKeyboardButton("🎥 Add Video", callback_data=f"cs_mode_video_{group_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_add_to_group_button(media_type: str = "media") -> InlineKeyboardButton:
    """Returns an inline button to add the downloaded media to user's active cloud storage group."""
    type_labels = {
        "video": "🎬 Add this Video to Group",
        "photo": "🖼️ Add this Photo to Group",
        "music": "🎵 Add this Music to Group",
        "audio": "🎵 Add this Music to Group",
        "file": "📁 Add this File to Group",
        "document": "📁 Add this File to Group"
    }
    label = type_labels.get(media_type.lower(), "☁️ Add to Group")
    return InlineKeyboardButton(label, callback_data=f"cs_save_{media_type.lower()}")


def get_otp_keypad(current_input: str = "") -> InlineKeyboardMarkup:
    """Returns an inline numeric keypad for entering OTP securely without sending text into chat."""
    display = " ".join(list(current_input)) if current_input else "_ _ _ _ _"
    keyboard = [
        [
            InlineKeyboardButton(f"🔢 Code: [ {display} ]", callback_data="noop")
        ],
        [
            InlineKeyboardButton("1", callback_data="cs_num_1"),
            InlineKeyboardButton("2", callback_data="cs_num_2"),
            InlineKeyboardButton("3", callback_data="cs_num_3"),
        ],
        [
            InlineKeyboardButton("4", callback_data="cs_num_4"),
            InlineKeyboardButton("5", callback_data="cs_num_5"),
            InlineKeyboardButton("6", callback_data="cs_num_6"),
        ],
        [
            InlineKeyboardButton("7", callback_data="cs_num_7"),
            InlineKeyboardButton("8", callback_data="cs_num_8"),
            InlineKeyboardButton("9", callback_data="cs_num_9"),
        ],
        [
            InlineKeyboardButton("⌫ Clear", callback_data="cs_num_clear"),
            InlineKeyboardButton("0", callback_data="cs_num_0"),
            InlineKeyboardButton("✅ Verify", callback_data="cs_num_submit"),
        ],
        [
            InlineKeyboardButton("🔄 New Code (/storage)", callback_data="cs_menu"),
            InlineKeyboardButton("❌ Cancel", callback_data="cs_cancel")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


async def cloud_storage_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main entry point for Cloud Storage / Telegram Group management."""
    user = update.effective_user
    if not user:
        return

    user_id = user.id
    is_connected = storage_service.is_user_connected(user_id)

    if not is_connected:
        # User not connected yet -> prompt for phone number
        context.user_data["cs_state"] = "awaiting_phone"
        text = (
            f"☁️ *Telegram Cloud Storage Setup* 🚀\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Namaste *{user.first_name}*! Telegram Cloud Storage use karne ke liye pehle apna Telegram account connect karein.\n\n"
            f"⚡ *Ek baar connect karne ke baad aapko baar-baar login nahi karna padega!* Next time click karte hi direct ye options aayenge:\n"
            f"• 📋 Group List\n"
            f"• 👉 Select Group\n"
            f"• 🗑️ Delete Group\n"
            f"• ➕ Add Group\n\n"
            f"📲 *Abhi connect karne ke liye apna Telegram Phone Number bhejiye:*\n"
            f"_(Country code ke sath international format me, e.g. `+919876543210`)_\n\n"
            f"🔒 _Aapka session secure SQLite database me store rehta hai._"
        )
        keyboard = [
            [InlineKeyboardButton("❌ Cancel / Back to Menu", callback_data="menu_main")]
        ]
        if update.message:
            await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        elif update.callback_query:
            try:
                await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
            except Exception:
                await update.callback_query.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # If already connected, show the Telegram Group Dashboard
    await show_cloud_dashboard(update, context)


async def show_cloud_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays the main Cloud Storage & Telegram Group dashboard."""
    user = update.effective_user
    if not user:
        return
    user_id = user.id

    # If user is not connected yet, show connect / phone number setup flow
    if not storage_service.is_user_connected(user_id):
        await cloud_storage_command(update, context)
        return

    phone = storage_service.get_connected_phone(user_id) or "Connected"
    active_group = db.get_user_active_cloud_group(user_id)
    all_groups = db.get_user_cloud_groups(user_id)

    group_name = active_group["group_name"] if active_group else "No Group Created Yet"
    group_id = active_group["id"] if active_group else 0
    invite_link = active_group.get("invite_link", "") if active_group else ""

    link_display = f"[Join Private Group]({invite_link})" if invite_link else "`(Private)`"

    text = (
        f"☁️ *Telegram Cloud Storage Dashboard* 🚀\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📱 *Connected Account:* `{phone}`\n"
        f"👥 *Total Groups:* `{len(all_groups)}`\n"
        f"🔒 *Active Cloud Group:* **{group_name}**\n"
        f"🔗 *Group Link:* {link_display}\n\n"
        f"👇 *Niche diye gaye buttons se files upload karein ya groups manage karein:*"
    )

    keyboard = [
        [
            InlineKeyboardButton("📋 Group List", callback_data="cs_list_groups"),
            InlineKeyboardButton("👉 Select Group", callback_data="cs_select_group")
        ],
        [
            InlineKeyboardButton("🗑️ Delete Group", callback_data="cs_delete_group_menu"),
            InlineKeyboardButton("➕ Add Group", callback_data="cs_new_group")
        ]
    ]

    # If an active group exists, add the 5 action buttons
    if active_group:
        keyboard.extend([
            [
                InlineKeyboardButton("➕ Add", callback_data=f"cs_mode_add_{group_id}"),
                InlineKeyboardButton("📁 Add File/Folder", callback_data=f"cs_mode_file_{group_id}")
            ],
            [
                InlineKeyboardButton("🖼️ Add Photo", callback_data=f"cs_mode_photo_{group_id}"),
                InlineKeyboardButton("🎥 Add Video", callback_data=f"cs_mode_video_{group_id}")
            ]
        ])

    keyboard.extend([
        [
            InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu_main"),
            InlineKeyboardButton("🚪 Disconnect Account", callback_data="cs_disconnect_confirm")
        ]
    ])

    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        try:
            await update.callback_query.edit_message_text(text, parse_mode="Markdown", disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception:
            await update.callback_query.message.reply_text(text, parse_mode="Markdown", disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(keyboard))


async def perform_otp_verification(
    user_id: int,
    clean_code: str,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    message_to_edit=None
) -> bool:
    """Verifies user's Telegram OTP code and updates UI accordingly."""
    if message_to_edit:
        status_msg = message_to_edit
        try:
            await status_msg.edit_text("⏳ *Verifying OTP code...*", parse_mode="Markdown")
        except Exception:
            pass
    else:
        status_msg = await update.effective_message.reply_text("⏳ *Verifying OTP code...*", parse_mode="Markdown")

    res = await storage_service.verify_login_code(user_id, clean_code)

    if res.get("status") == "2fa_required":
        context.user_data["cs_state"] = "awaiting_2fa"
        await status_msg.edit_text(
            "🔐 *Two-Step Verification (2FA) Password Required*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Aapke Telegram account par Two-Step Verification (Cloud Password) enable hai.\n\n"
            "🔑 *Kripya apna 2FA Password yahan type karein:*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cs_cancel")]])
        )
        return True

    elif res.get("status") == "connected":
        context.user_data["cs_state"] = "awaiting_group_name"
        context.user_data.pop("cs_otp_input", None)
        await status_msg.edit_text(
            "✅ *Connected! Telegram Account Safalta Se Connect Hua!* 🎉\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Ab bot aapke account par ek private group create karega.\n\n"
            "🏷️ *Group ka naam kya rakhna hai?*\n"
            "_(Type karke bhejiye, e.g. `My Cloud Storage` ya `Personal Vault`)_",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cs_cancel")]])
        )
        return True

    else:
        err_msg = res.get("message", "Invalid OTP.")
        err_code = res.get("error")
        if err_code == "no_pending_login":
            context.user_data["cs_state"] = "awaiting_phone"
            context.user_data.pop("cs_otp_input", None)
            await status_msg.edit_text(
                f"⚠️ *Session Reset:*\n`{err_msg}`\n\n"
                f"📲 *Kripya apna phone number dubara bhejiye:*",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cs_cancel")]])
            )
        else:
            context.user_data["cs_otp_input"] = ""
            await status_msg.edit_text(
                f"❌ *OTP Verification Error:*\n`{err_msg}`\n\n"
                f"⚠️ *Telegram Security Alert:* Telegram login code ko chat me bina spaces ke type karne par expire kar deta hai!\n"
                f"Kripya niche keypad se code enter karein ya spaces ke sath type karein (e.g. `1 2 3 4 5`):",
                parse_mode="Markdown",
                reply_markup=get_otp_keypad("")
            )
        return True


async def handle_cloud_storage_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Handles conversational text input for phone, OTP, 2FA, group name, or active uploads.
    Returns True if the message was handled by Cloud Storage, False otherwise.
    """
    if not update.message or not update.message.text:
        return False

    user_id = update.effective_user.id
    state = context.user_data.get("cs_state")
    text = update.message.text.strip()

    # 1. Awaiting Phone Number
    if state == "awaiting_phone":
        clean_phone = text.replace(" ", "").replace("-", "")
        # Basic check for phone format
        if not clean_phone.startswith("+") and not clean_phone.isdigit():
            await update.message.reply_text(
                "❌ *Amanaya Phone Number Format!*\nKripya country code ke sath phone number bhejiye (e.g. `+919876543210`):",
                parse_mode="Markdown"
            )
            return True

        status_msg = await update.message.reply_text("⏳ *Connecting to Telegram & Sending OTP code...*", parse_mode="Markdown")
        res = await storage_service.send_login_code(user_id, clean_phone)

        if res.get("success"):
            context.user_data["cs_state"] = "awaiting_otp"
            context.user_data["cs_phone"] = res.get("phone")
            context.user_data["cs_otp_input"] = ""
            await status_msg.edit_text(
                f"📩 *OTP Code Sent Successfully!* 🚀\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"Aapke Telegram app par official verification code bheja gaya hai.\n\n"
                f"🛡️ *Telegram Anti-Block Security:* Telegram chat me direct plain OTP code type karne par use cancel kar deta hai.\n\n"
                f"👇 *Niche diye gaye keypad se apna 5 digit code tap karein:*",
                parse_mode="Markdown",
                reply_markup=get_otp_keypad("")
            )
        else:
            err_code = res.get("error", "")
            err_msg = res.get("message", "Could not send OTP.")
            if err_code == "invalid_api_id" or "api_id" in err_msg.lower() or "api_hash" in err_msg.lower():
                await status_msg.edit_text(
                    f"❌ *Telegram API Credentials Error!*\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"⚠️ *Ye error phone number ka nahi hai!*\n\n"
                    f"Telegram MTProto (Cloud Storage login) ke liye valid `api_id` aur `api_hash` zaroori hai.\n\n"
                    f"📌 *Ise kaise set karein:*\n"
                    f"1️⃣ Browser me **https://my.telegram.org** open karein aur login karein.\n"
                    f"2️⃣ *API development tools* par click karke koi bhi App banayein.\n"
                    f"3️⃣ Wahan se **App api_id** aur **App api_hash** copy karein.\n"
                    f"4️⃣ Yahan direct command bhejiye:\n"
                    f"`/setapi <api_id> <api_hash>`\n"
                    f"_(Example: `/setapi 12345678 abcdef0123456789abcdef0123456789`)_\n\n"
                    f"Ya project ki `.env` file me `TELEGRAM_API_ID` aur `TELEGRAM_API_HASH` add karein.",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cs_cancel")]])
                )
            else:
                await status_msg.edit_text(
                    f"❌ *OTP Bhejne me Error:*\n`{err_msg}`\n\n"
                    f"Kripya sahi number dubara bhejiye ya try again karein:",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cs_cancel")]])
                )
        return True

    # 2. Awaiting OTP Code (Text input support with spaces or digits)
    elif state == "awaiting_otp":
        clean_code = "".join(filter(str.isdigit, text))
        if not clean_code:
            await update.message.reply_text(
                "❌ *Amanaya Code!* Kripya sirf numbers me verification code bhejiye ya niche keypad use karein:",
                parse_mode="Markdown",
                reply_markup=get_otp_keypad(context.user_data.get("cs_otp_input", ""))
            )
            return True

        await perform_otp_verification(user_id, clean_code, update, context)
        return True

    # 3. Awaiting 2FA Password
    elif state == "awaiting_2fa":
        status_msg = await update.message.reply_text("⏳ *Verifying 2FA Password...*", parse_mode="Markdown")
        res = await storage_service.verify_2fa_password(user_id, text)

        if res.get("status") == "connected":
            context.user_data["cs_state"] = "awaiting_group_name"
            await status_msg.edit_text(
                "✅ *Connected! Telegram Account Safalta Se Connect Hua!* 🎉\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "Ab bot aapke account par ek private group create karega.\n\n"
                "🏷️ *Group ka naam kya rakhna hai?*\n"
                "_(Type karke bhejiye, e.g. `My Cloud Storage` ya `Personal Vault`)_",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cs_cancel")]])
            )
            return True
        else:
            err_msg = res.get("message", "Incorrect password.")
            await status_msg.edit_text(
                f"❌ *2FA Password Galat Hai:*\n`{err_msg}`\n\n"
                f"Kripya sahi password dubara type karein:",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cs_cancel")]])
            )
            return True

    # 4. Awaiting Group Name
    elif state == "awaiting_group_name":
        group_name = text.strip()
        if len(group_name) < 2:
            await update.message.reply_text("❌ *Kripya kam se kam 2 aksharo ka group name likhein:*", parse_mode="Markdown")
            return True

        status_msg = await update.message.reply_text(
            f"⏳ *Creating private group '{group_name}' on your Telegram account...*",
            parse_mode="Markdown"
        )
        bot_username = getattr(config, "BOT_USERNAME", "")
        if not bot_username and context.bot.username:
            bot_username = context.bot.username

        res = await storage_service.create_private_group(user_id, group_name, bot_username)

        if res.get("success"):
            context.user_data["cs_state"] = "active"
            context.user_data["upload_mode"] = "any"
            new_group_id = res["group_id"]
            invite_link = res.get("invite_link", "")

            link_part = f"\n🔗 *Private Group Link:* [Join Private Group]({invite_link})" if invite_link else ""

            await status_msg.edit_text(
                f"🎉 *Private Group Created Successfully!* 🚀\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🏷️ *Group Name:* **{group_name}**{link_part}\n\n"
                f"✨ Ab aap is group me Photos, Videos, Files aur Notes add kar sakte hain!\n"
                f"Niche diye gaye options chuniye ya direct media send kijiye:",
                parse_mode="Markdown",
                disable_web_page_preview=True,
                reply_markup=get_five_action_keyboard(new_group_id)
            )
            return True
        else:
            err_msg = res.get("message", "Failed to create group.")
            await status_msg.edit_text(
                f"❌ *Group Banane me Error:*\n`{err_msg}`\n\n"
                f"Kripya dubara group ka naam likhkar try karein ya Cancel karein:",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cs_cancel")]])
            )
            return True

    # 5. Direct Text Note Upload to Cloud Storage Group if in upload mode
    upload_mode = context.user_data.get("upload_mode")
    if upload_mode in ["any", "text"] and not text.startswith("/"):
        active_group = db.get_user_active_cloud_group(user_id)
        if active_group and storage_service.is_user_connected(user_id):
            res = await storage_service.forward_or_send_media_to_group(
                bot_context=context,
                user_id=user_id,
                group_chat_id=active_group["telegram_chat_id"],
                message=update.message
            )
            if res.get("success"):
                await update.message.reply_text(
                    f"✅ *Successfully Saved to '{active_group['group_name']}'!* 📝\n"
                    f"Aapka text note private group me add ho gaya hai.\n\n"
                    f"_Aur bhi kuch send karein ya niche options chuniye:_",
                    parse_mode="Markdown",
                    reply_markup=get_five_action_keyboard(active_group["id"])
                )
                return True

    return False


async def handle_cloud_storage_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Handles Photo, Video, Document, Audio, and Voice uploads into user's private Cloud Group."""
    if not update.message:
        return False

    user = update.effective_user
    if not user:
        return False

    user_id = user.id
    if not storage_service.is_user_connected(user_id):
        return False

    active_group = db.get_user_active_cloud_group(user_id)
    if not active_group:
        return False

    # Check media type
    msg = update.message
    is_media = bool(msg.photo or msg.video or msg.document or msg.audio or msg.voice)
    if not is_media:
        return False

    status_msg = await msg.reply_text(f"⏳ *Adding to your private group '{active_group['group_name']}'...*", parse_mode="Markdown")

    res = await storage_service.forward_or_send_media_to_group(
        bot_context=context,
        user_id=user_id,
        group_chat_id=active_group["telegram_chat_id"],
        message=msg
    )

    if res.get("success"):
        media_type = res.get("type", "Media").capitalize()
        await status_msg.edit_text(
            f"✅ *Successfully Added {media_type} to '{active_group['group_name']}'!* 🚀\n\n"
            f"📦 *Type:* `{media_type}`\n"
            f"🔒 *Target Group:* **{active_group['group_name']}**\n\n"
            f"_Aap aur bhi files/media bhej sakte hain ya options chuniye:_",
            parse_mode="Markdown",
            reply_markup=get_five_action_keyboard(active_group["id"])
        )
        return True
    else:
        err = res.get("error", "Upload failed")
        await status_msg.edit_text(
            f"❌ *Upload Error:* `{err}`\n"
            f"Kripya check karein ki Bot aapke group me added hai ya dubara send karein.",
            parse_mode="Markdown",
            reply_markup=get_five_action_keyboard(active_group["id"])
        )
        return True


async def cloud_storage_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Router for all inline callback queries starting with cs_"""
    query = update.callback_query
    data = query.data or ""
    user_id = update.effective_user.id

    try:
        await query.answer()
    except Exception:
        pass

    # Cancel action
    if data == "cs_cancel":
        context.user_data.pop("cs_state", None)
        context.user_data.pop("upload_mode", None)
        from handlers.start import start_command
        if not storage_service.is_user_connected(user_id):
            await start_command(update, context)
        else:
            await show_cloud_dashboard(update, context)

    # Return to dashboard or connect flow
    elif data == "cs_menu":
        context.user_data.pop("cs_state", None)
        context.user_data.pop("cs_otp_input", None)
        if not storage_service.is_user_connected(user_id):
            await cloud_storage_command(update, context)
        else:
            await show_cloud_dashboard(update, context)

    # OTP Keypad Callbacks
    elif data.startswith("cs_num_"):
        action = data.replace("cs_num_", "")
        current = context.user_data.get("cs_otp_input", "")
        if action == "clear":
            current = ""
            context.user_data["cs_otp_input"] = current
            try:
                await query.edit_message_reply_markup(reply_markup=get_otp_keypad(current))
            except Exception:
                pass
        elif action == "submit":
            if len(current) < 5:
                await query.answer("⚠️ Kripya kam se kam 5 ankon ka code enter karein!", show_alert=True)
                return
            await perform_otp_verification(user_id, current, update, context, message_to_edit=query.message)
        elif action in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]:
            if len(current) < 6:
                current += action
                context.user_data["cs_otp_input"] = current
                if len(current) == 5:
                    # Automatically verify when 5 digits are entered
                    await perform_otp_verification(user_id, current, update, context, message_to_edit=query.message)
                else:
                    try:
                        await query.edit_message_reply_markup(reply_markup=get_otp_keypad(current))
                    except Exception:
                        pass
        return

    # Save current media (YouTube, Insta, Pin, GitHub, GDrive, Music) to Cloud Storage Group
    elif data.startswith("cs_save_"):
        media_type = data.replace("cs_save_", "")
        if not storage_service.is_user_connected(user_id):
            await query.answer(
                "⚠️ Pehle Telegram Cloud Storage connect karein! Menu me '☁️ Telegram Group' par click karein ya /storage bhejiye.",
                show_alert=True
            )
            return

        active_group = db.get_user_active_cloud_group(user_id)
        if not active_group:
            await query.answer(
                "⚠️ Koi active cloud group nahi mila! /storage par jaakar '➕ Add Group' karein.",
                show_alert=True
            )
            return

        target_msg = query.message
        if not target_msg:
            await query.answer("❌ Message not found.", show_alert=True)
            return

        res = await storage_service.forward_or_send_media_to_group(
            bot_context=context,
            user_id=user_id,
            group_chat_id=active_group["telegram_chat_id"],
            message=target_msg
        )

        if res.get("success"):
            gname = active_group["group_name"]
            invite_link = active_group.get("invite_link", "")

            await query.answer(f"✅ '{gname}' me successfully save ho gaya! 🎉", show_alert=True)

            # Update inline button to direct Open Group link or confirmation
            new_button = (
                InlineKeyboardButton(f"✅ Added! 🔗 Open '{gname[:15]}'", url=invite_link)
                if invite_link
                else InlineKeyboardButton(f"✅ Added to '{gname[:15]}' 🎉", callback_data="noop")
            )

            current_markup = target_msg.reply_markup
            new_keyboard = []
            if current_markup and current_markup.inline_keyboard:
                for row in current_markup.inline_keyboard:
                    new_row = []
                    for btn in row:
                        if btn.callback_data and btn.callback_data.startswith("cs_save_"):
                            new_row.append(new_button)
                        else:
                            new_row.append(btn)
                    new_keyboard.append(new_row)
            else:
                new_keyboard = [[new_button]]

            try:
                await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(new_keyboard))
            except Exception as ex:
                logger.warning(f"Could not update reply_markup on saved message: {ex}")
        else:
            err = res.get("error", "Unknown error")
            await query.answer(f"❌ Save error: {err}", show_alert=True)

    # 5 Action Mode Buttons:
    # 1. ➕ Add (Any media / text)
    elif data.startswith("cs_mode_add_"):
        try:
            group_id = int(data.replace("cs_mode_add_", ""))
        except ValueError:
            group_id = 0
        context.user_data["upload_mode"] = "any"
        group = db.get_cloud_group_by_id(group_id, user_id)
        gname = group["group_name"] if group else "Private Group"

        text = (
            f"➕ *Add Anything Mode Active* 📥\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔒 *Target Group:* **{gname}**\n\n"
            f"Aap jo bhi message, text note, photo, video ya file bhejenge, "
            f"vo direct aapke **{gname}** group me add ho jayegi!\n\n"
            f"👇 *Abhi kuch bhi send karein:*"
        )
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=get_five_action_keyboard(group_id))

    # 2. 📁 Add File/Folder
    elif data.startswith("cs_mode_file_"):
        try:
            group_id = int(data.replace("cs_mode_file_", ""))
        except ValueError:
            group_id = 0
        context.user_data["upload_mode"] = "file"
        group = db.get_cloud_group_by_id(group_id, user_id)
        gname = group["group_name"] if group else "Private Group"

        text = (
            f"📁 *Add File / Folder Mode Active* 📄\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔒 *Target Group:* **{gname}**\n\n"
            f"Kripya koi bhi Document, PDF, ZIP ya File send karein. "
            f"Vo turant aapke **{gname}** me save ho jayegi!\n\n"
            f"👇 *File yahan send karein:*"
        )
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=get_five_action_keyboard(group_id))

    # 3. 🖼️ Add Photo
    elif data.startswith("cs_mode_photo_"):
        try:
            group_id = int(data.replace("cs_mode_photo_", ""))
        except ValueError:
            group_id = 0
        context.user_data["upload_mode"] = "photo"
        group = db.get_cloud_group_by_id(group_id, user_id)
        gname = group["group_name"] if group else "Private Group"

        text = (
            f"🖼️ *Add Photo Mode Active* 📸\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔒 *Target Group:* **{gname}**\n\n"
            f"Kripya koi bhi Photo/Image send karein. "
            f"Vo turant aapke **{gname}** me add ho jayegi!\n\n"
            f"👇 *Photo yahan send karein:*"
        )
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=get_five_action_keyboard(group_id))

    # 4. 🎥 Add Video
    elif data.startswith("cs_mode_video_"):
        try:
            group_id = int(data.replace("cs_mode_video_", ""))
        except ValueError:
            group_id = 0
        context.user_data["upload_mode"] = "video"
        group = db.get_cloud_group_by_id(group_id, user_id)
        gname = group["group_name"] if group else "Private Group"

        text = (
            f"🎥 *Add Video Mode Active* 🎬\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔒 *Target Group:* **{gname}**\n\n"
            f"Kripya koi bhi Video clip send karein. "
            f"Vo turant aapke **{gname}** me add ho jayegi!\n\n"
            f"👇 *Video yahan send karein:*"
        )
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=get_five_action_keyboard(group_id))

    # 📋 Group List
    elif data == "cs_list_groups":
        groups = db.get_user_cloud_groups(user_id)
        active_group = db.get_user_active_cloud_group(user_id)
        active_id = active_group["id"] if active_group else None

        if not groups:
            text = (
                f"📋 *Your Telegram Cloud Groups*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"Abhi tak koi group nahi banaya gaya hai.\n"
                f"Niche diye gaye button se naya group banayein!"
            )
            keyboard = [
                [InlineKeyboardButton("➕ Add Group", callback_data="cs_new_group")],
                [InlineKeyboardButton("🔙 Back to Dashboard", callback_data="cs_menu")]
            ]
        else:
            text = (
                f"📋 *Your Telegram Cloud Groups ({len(groups)})*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            )
            keyboard = []
            for g in groups:
                status = "✅ Active" if g["id"] == active_id else "⚪ Switch"
                link = f" • [Join]({g['invite_link']})" if g.get("invite_link") else ""
                text += f"• **{g['group_name']}** ({status}){link}\n"
                keyboard.append([
                    InlineKeyboardButton(f"{'✅ ' if g['id'] == active_id else ''}{g['group_name']}", callback_data=f"cs_select_{g['id']}"),
                    InlineKeyboardButton("🗑️", callback_data=f"cs_delconf_{g['id']}")
                ])
            keyboard.append([InlineKeyboardButton("➕ Create New Group", callback_data="cs_new_group")])
            keyboard.append([InlineKeyboardButton("🔙 Back to Dashboard", callback_data="cs_menu")])

        await query.edit_message_text(text, parse_mode="Markdown", disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(keyboard))

    # 👉 Select Group Menu
    elif data == "cs_select_group":
        groups = db.get_user_cloud_groups(user_id)
        active_group = db.get_user_active_cloud_group(user_id)
        active_id = active_group["id"] if active_group else None

        if not groups:
            await query.answer("Pehle ek group banayein!", show_alert=True)
            return

        text = (
            f"👉 *Select Active Cloud Group*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Jis group me aap media save karna chahte hain, use select karein:"
        )
        keyboard = []
        for g in groups:
            prefix = "✅ " if g["id"] == active_id else "📁 "
            keyboard.append([InlineKeyboardButton(f"{prefix}{g['group_name']}", callback_data=f"cs_select_{g['id']}")])
        keyboard.append([InlineKeyboardButton("🔙 Back to Dashboard", callback_data="cs_menu")])

        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    # Switch Active Group
    elif data.startswith("cs_select_"):
        try:
            group_id = int(data.replace("cs_select_", ""))
        except ValueError:
            return
        db.set_user_active_cloud_group(user_id, group_id)
        group = db.get_cloud_group_by_id(group_id, user_id)
        gname = group["group_name"] if group else "Group"
        await query.answer(f"✅ '{gname}' set as Active Group!", show_alert=True)
        await show_cloud_dashboard(update, context)

    # ➕ Add New Group
    elif data == "cs_new_group":
        context.user_data["cs_state"] = "awaiting_group_name"
        text = (
            f"➕ *Create New Cloud Storage Group*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🏷️ *Naye group ka naam kya rakhna hai?*\n"
            f"_(Type karke bhejiye, e.g. `Photos Vault` ya `Work Documents`)_"
        )
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="cs_menu")]]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    # 🗑️ Delete Group Menu
    elif data == "cs_delete_group_menu":
        groups = db.get_user_cloud_groups(user_id)
        if not groups:
            await query.answer("Koi group delete karne ke liye nahi hai!", show_alert=True)
            return

        text = (
            f"🗑️ *Delete Cloud Storage Group*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Konse group ko delete karna hai select karein:"
        )
        keyboard = []
        for g in groups:
            keyboard.append([InlineKeyboardButton(f"🗑️ Delete '{g['group_name']}'", callback_data=f"cs_delconf_{g['id']}")])
        keyboard.append([InlineKeyboardButton("🔙 Back to Dashboard", callback_data="cs_menu")])

        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    # Delete confirmation prompt
    elif data.startswith("cs_delconf_"):
        try:
            group_id = int(data.replace("cs_delconf_", ""))
        except ValueError:
            return
        group = db.get_cloud_group_by_id(group_id, user_id)
        if not group:
            await query.answer("Group nahi mila!", show_alert=True)
            return

        text = (
            f"⚠️ *Delete Confirmation*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Kya aap sachme **'{group['group_name']}'** ko Telegram aur Database se permanently delete karna chahte hain?"
        )
        keyboard = [
            [
                InlineKeyboardButton("✅ Yes, Delete", callback_data=f"cs_delete_do_{group_id}"),
                InlineKeyboardButton("❌ No, Cancel", callback_data="cs_list_groups")
            ]
        ]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    # Execute group deletion
    elif data.startswith("cs_delete_do_"):
        try:
            group_id = int(data.replace("cs_delete_do_", ""))
        except ValueError:
            return
        await query.edit_message_text("⏳ *Deleting group from Telegram...*", parse_mode="Markdown")
        res = await storage_service.delete_group(user_id, group_id)
        if res.get("success"):
            await query.answer("✅ Group successfully deleted!", show_alert=True)
        else:
            await query.answer("❌ Deletion error", show_alert=True)
        await show_cloud_dashboard(update, context)

    # Disconnect confirmation prompt
    elif data == "cs_disconnect_confirm":
        text = (
            f"⚠️ *Disconnect Account Confirmation*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Kya aap apna Telegram account bot se disconnect karna chahte hain?\n"
            f"_(Aapke banaye hue groups Telegram par safe rahenge, par bot se manage karne ke liye firse login karna hoga.)_"
        )
        keyboard = [
            [
                InlineKeyboardButton("🚪 Yes, Disconnect", callback_data="cs_disconnect_do"),
                InlineKeyboardButton("❌ Cancel", callback_data="cs_menu")
            ]
        ]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    # Execute disconnect
    elif data == "cs_disconnect_do":
        await storage_service.disconnect_user(user_id)
        context.user_data.pop("cs_state", None)
        context.user_data.pop("upload_mode", None)
        await query.answer("🚪 Account disconnected successfully.", show_alert=True)
        await query.edit_message_text(
            "🚪 *Telegram Account Disconnected!*\n\nAapka session safalta se remove kar diya gaya hai.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")]])
        )


async def set_api_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Allows setting TELEGRAM_API_ID and TELEGRAM_API_HASH via bot command."""
    if not update.message:
        return

    user = update.effective_user
    args = context.args or []

    if len(args) < 2:
        await update.message.reply_text(
            "📌 *Usage:*\n`/setapi <api_id> <api_hash>`\n\n"
            "Example:\n`/setapi 12345678 abcdef0123456789abcdef0123456789`\n\n"
            "💡 *API ID & Hash kahan se milega?*\n"
            "1. https://my.telegram.org par jayein aur phone se login karein\n"
            "2. 'API development tools' par click karein\n"
            "3. App create karke API ID aur API Hash copy karein.",
            parse_mode="Markdown"
        )
        return

    try:
        api_id = int(args[0].strip())
        api_hash = args[1].strip()
    except ValueError:
        await update.message.reply_text("❌ `api_id` ek number hona chahiye! Example: `/setapi 12345678 your_hash`", parse_mode="Markdown")
        return

    storage_service.update_api_credentials(api_id, api_hash)
    await update.message.reply_text(
        f"✅ *Telegram API Credentials Successfully Updated!* 🚀\n\n"
        f"🆔 *API ID:* `{api_id}`\n"
        f"🔑 *API Hash:* `{api_hash[:4]}...{api_hash[-4:]}`\n\n"
        f"Ab aap `/storage` ya menu me jaakar apna phone number enter karke Telegram Cloud Storage connect kar sakte hain!",
        parse_mode="Markdown"
    )

