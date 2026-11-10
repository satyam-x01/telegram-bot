"""Telegram menu and guided setup for WhatsApp research automations."""
import asyncio
import base64
import importlib
import json
import os
import re
import sys
import time
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

_wa_app = None
_wa_clients = {}
_start_lock = asyncio.Lock()
_flow_key = "whatsapp_setup_flow"
_mapping_path = Path(os.environ.get(
    "WHATSAPP_DATA_DIR",
    str(Path(__file__).resolve().parents[1] / "whatsapp" / "data"),
)) / "telegram_recipients.json"


def _load_whatsapp_app():
    global _wa_app
    if _wa_app is None:
        whatsapp_dir = Path(__file__).resolve().parents[1] / "whatsapp"
        if str(whatsapp_dir) not in sys.path:
            sys.path.insert(0, str(whatsapp_dir))
        _wa_app = importlib.import_module("whatsapp.app")
    return _wa_app


def _get_whatsapp_client(telegram_user_id: int):
    """Give each Telegram user an isolated persistent WhatsApp session."""
    wa_app = _load_whatsapp_app()
    client = _wa_clients.get(telegram_user_id)
    if client is None:
        from modules.whatsapp_client import WhatsAppClient
        client = WhatsAppClient(
            wa_app.bot_handler,
            session_name=f"telegram_user_{telegram_user_id}_whatsapp",
        )
        _wa_clients[telegram_user_id] = client
    return client


def _load_mappings():
    try:
        return json.loads(_mapping_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_mapping(telegram_id: int, jid: str):
    _mapping_path.parent.mkdir(parents=True, exist_ok=True)
    mappings = _load_mappings()
    mappings[str(telegram_id)] = jid
    _mapping_path.write_text(json.dumps(mappings, indent=2), encoding="utf-8")


def _get_mapping(telegram_id: int):
    return _load_mappings().get(str(telegram_id))


def _main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📲 Connect WhatsApp", callback_data="wa_connect")],
        [InlineKeyboardButton("📖 Automation details", callback_data="wa_details")],
    ])


def _automation_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("1️⃣ Automation 1", callback_data="wa_slot_1"),
         InlineKeyboardButton("2️⃣ Automation 2", callback_data="wa_slot_2")],
        [InlineKeyboardButton("3️⃣ Automation 3", callback_data="wa_slot_3")],
        [InlineKeyboardButton("⬅️ Back", callback_data="wa_home")],
    ])


async def whatsapp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not message:
        return
    if update.effective_chat and update.effective_chat.type != "private":
        await message.reply_text("🔒 WhatsApp setup private Telegram chat me karein. Mujhe DM karke `/whatsapp` bhejein.")
        return
    try:
        status = _get_whatsapp_client(update.effective_user.id).get_status()
    except Exception as exc:
        await message.reply_text(
            "⚠️ WhatsApp dependencies load nahi hue. Project folder me "
            "`pip install -r whatsapp/requirements.txt` chalakar bot restart karein.\n"
            f"Details: {type(exc).__name__}: {exc}"
        )
        return
    state = "✅ Connected" if status.get("connected") else "⚪ Not connected"
    await message.reply_text(
        "📲 *WhatsApp Automation Center*\n\n"
        f"Connection: {state}\n"
        "Yahan se WhatsApp link karein, 3 automations manage karein, aur apne topic ke hisaab se AI se research prompt banwayein.\n\n"
        "👇 Ek option choose karein:",
        parse_mode="Markdown",
        reply_markup=_main_keyboard(),
    )


async def whatsapp_entry_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Open the same control center from the Telegram main menu button."""
    query = update.callback_query
    await query.message.reply_text(
        "📲 *WhatsApp Automation Center*\n\n"
        "Connect WhatsApp, view automation details, or configure one of three slots.",
        parse_mode="Markdown", reply_markup=_main_keyboard())


async def _connect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    status = _get_whatsapp_client(update.effective_user.id).get_status()
    if status.get("connected"):
        await query.message.reply_text(
            f"✅ WhatsApp connected: `{status.get('phone_number') or status.get('connected_jid') or 'Connected'}`",
            parse_mode="Markdown", reply_markup=_main_keyboard())
        return
    await query.message.reply_text(
        "WhatsApp connect karne ka tareeqa chunein:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📷 Link new number with QR", callback_data="wa_qr")],
            [InlineKeyboardButton("🔢 Link new number without QR", callback_data="wa_pair")],
            [InlineKeyboardButton("↩️ Reconnect previously linked number", callback_data="wa_reconnect")],
        ]),
    )


async def whatsapp_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data or ""
    if update.effective_chat and update.effective_chat.type != "private":
        await query.message.reply_text("🔒 WhatsApp connect/pairing ko private Telegram chat mein kholen: `/whatsapp`.")
        return
    if data == "wa_connect":
        try:
            await _connect(update, context)
        except Exception as exc:
            await query.message.reply_text(f"⚠️ WhatsApp connect error: {type(exc).__name__}: {exc}")
        return

    if data == "wa_qr":
        wa_client = _get_whatsapp_client(update.effective_user.id)
        if wa_client.get_status().get("worker_alive"):
            await query.message.reply_text("WhatsApp connection attempt already running. Wait for its QR or code.")
            return
        async with _start_lock:
            wa_client.start(new_device=True)
        status = wa_client.get_status()
        for _ in range(40):
            if status.get("connected") or status.get("qr_data_url"):
                break
            if status.get("connection_error"):
                break
            await asyncio.sleep(0.5)
            status = wa_client.get_status()
        if status.get("connected"):
            await query.message.reply_text("✅ WhatsApp is already connected.", reply_markup=_main_keyboard())
        elif status.get("qr_data_url"):
            qr = base64.b64decode(status["qr_data_url"].split(",", 1)[-1])
            await query.message.reply_photo(
                photo=qr,
                caption="📲 WhatsApp → Linked devices → Link a device se QR scan karein. QR expire ho to Refresh QR dabayein.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Refresh QR", callback_data="wa_qr")]]),
            )
        else:
            err = status.get("connection_error")
            detail = f"\n\nError: {err[:500]}" if err else ""
            await query.message.reply_text("⚠️ QR abhi generate nahi hua." + detail + "\nBot console ke latest logs bhi check karein.")
        return

    if data == "wa_reconnect":
        wa_client = _get_whatsapp_client(update.effective_user.id)
        status = wa_client.get_status()
        if status.get("worker_alive"):
            await query.message.reply_text("WhatsApp connection attempt already running. Restart the Telegram bot before switching sessions.")
            return
        async with _start_lock:
            wa_client.start()
        for _ in range(40):
            status = wa_client.get_status()
            if status.get("connected") or status.get("qr_data_url") or status.get("connection_error"):
                break
            await asyncio.sleep(0.5)
        if status.get("connected"):
            await query.message.reply_text(f"✅ Reconnected saved WhatsApp account: {status.get('phone_number') or status.get('connected_jid')}")
        elif status.get("qr_data_url"):
            qr = base64.b64decode(status["qr_data_url"].split(",", 1)[-1])
            await query.message.reply_photo(photo=qr, caption="No saved session was found. Scan this QR to link WhatsApp.")
        else:
            await query.message.reply_text("⚠️ Saved WhatsApp account reconnect nahi hua.\n" + (status.get("connection_error") or "Check the bot console logs."))
        return

    if data == "wa_pair":
        status = _get_whatsapp_client(update.effective_user.id).get_status()
        if status.get("worker_alive"):
            await query.message.reply_text("WhatsApp connection attempt already running. Pehle use complete hone dein ya bot restart karein.")
            return
        context.user_data[_flow_key] = {"stage": "pair_number", "deadline": time.time() + 300}
        await query.message.reply_text(
            "📱 Apne WhatsApp account ka phone number country code ke saath bhejein (sirf digits, jaise `919876543210`).\n\n"
            "Uske baad WhatsApp app mein Linked devices → Link a device → Link with phone number instead kholkar code enter karein.",
            parse_mode="Markdown")
        return

    if data == "wa_home":
        await query.message.reply_text("📲 *WhatsApp Automation Center*", parse_mode="Markdown", reply_markup=_main_keyboard())
        return
    if data == "wa_details":
        await query.message.reply_text(
            "📘 *3 WhatsApp Automations kaise kaam karti hain*\n\n"
            "• Har slot ka apna topic aur on/off status hai.\n"
            "• Slot button dabakar apna idea likhein; 5 minute ke andar prompt bhejna hoga.\n"
            "• AI aapke idea ko clear research instructions me badlega. Gemini key available na ho to aapka original prompt use hoga.\n"
            "• Prompt review/save hone ke baad *Start* dabayein. Updates har 5 minute me aayenge.\n"
            "• *Stop* se us slot ke updates rok sakte hain.\n"
            "• Pehla number linked WhatsApp account hai; self-chat choose karein. Dusra WhatsApp number ho to us par bhi delivery select kar sakte hain.\n\n"
            "Har update me topic ke mutabik summary, key details/features, usefulness, source link aur available ho to date/price jaise facts honge.",
            parse_mode="Markdown", reply_markup=_automation_keyboard())
        return
    if data.startswith("wa_slot_"):
        slot = int(data.rsplit("_", 1)[1])
        wa_app = _load_whatsapp_app()
        wa_client = _get_whatsapp_client(update.effective_user.id)
        status = wa_client.get_status()
        if not status.get("connected"):
            await query.message.reply_text("Pehle Connect WhatsApp dabakar account link karein.", reply_markup=_main_keyboard())
            return
        recipient = _get_mapping(update.effective_user.id)
        context.user_data[_flow_key] = {"stage": "topic", "slot": slot, "deadline": time.time() + 300}
        if recipient:
            await query.message.reply_text(
                f"📝 *Automation {slot} ke liye apna idea/prompt bhejein.*\n\n"
                "Example: `India ke naye AI tools, free/paid price, Android availability aur official links`\n\n"
                "⏳ Aapke paas 5 minute hain.", parse_mode="Markdown")
        else:
            context.user_data[_flow_key]["stage"] = "recipient"
            await query.message.reply_text(
                "📱 Updates kahan bhejne hain?\n\n"
                "Agar sirf linked number hai to *This WhatsApp (self)* chunein. Agar aapke paas doosra WhatsApp number hai, *Other number* chunein aur country code ke saath number bhejein.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("This WhatsApp (self)", callback_data=f"wa_self_{slot}")],
                    [InlineKeyboardButton("Other WhatsApp number", callback_data=f"wa_other_{slot}")],
                ]))
        return
    if data.startswith("wa_self_"):
        slot = int(data.rsplit("_", 1)[1])
        wa_app = _load_whatsapp_app()
        wa_client = _get_whatsapp_client(update.effective_user.id)
        jid = wa_client.get_status().get("connected_jid", "")
        phone = wa_client.get_status().get("phone_number", "")
        recipient = phone or jid
        if not recipient:
            await query.message.reply_text("WhatsApp connected nahi mila. Connect WhatsApp dabayein.")
            return
        _save_mapping(update.effective_user.id, recipient)
        wa_app.bot_handler.register_client_route(recipient, wa_client)
        context.user_data[_flow_key] = {"stage": "topic", "slot": slot, "deadline": time.time() + 300}
        await query.message.reply_text(f"✅ Self-chat recipient set. Ab Automation {slot} ka idea bhejein (5 minute ke andar).")
        return
    if data.startswith("wa_other_"):
        slot = int(data.rsplit("_", 1)[1])
        context.user_data[_flow_key] = {"stage": "number", "slot": slot, "deadline": time.time() + 300}
        await query.message.reply_text("📱 Doosra WhatsApp number country code ke saath bhejein (sirf digits, jaise `919876543210`). 5 minute ka samay hai.", parse_mode="Markdown")
        return
    if data.startswith("wa_review_"):
        slot = int(data.rsplit("_", 1)[1])
        jid = _get_mapping(update.effective_user.id)
        if not jid:
            await query.message.reply_text("Recipient set nahi hai. `/whatsapp` se dobara setup karein.")
            return
        wa_app = _load_whatsapp_app()
        wa_client = _get_whatsapp_client(update.effective_user.id)
        user_manager = _load_user_manager(wa_app)
        user_manager.update_user(jid, state="AUTHENTICATED", name=update.effective_user.first_name or "User")
        user_manager.select_slot(jid, slot)
        prompt = context.user_data.pop("wa_review_prompt", "")
        user_manager.set_slot_prompt(jid, slot, prompt, interval=5)
        wa_app.bot_handler.register_client_route(jid, wa_client)
        await query.message.reply_text(
            f"✅ Automation {slot} save ho gaya. Updates har 5 minute me {jid} par jayenge.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("▶️ Start automation", callback_data=f"wa_start_{slot}")],
                [InlineKeyboardButton("✏️ Edit prompt", callback_data=f"wa_slot_{slot}")],
                [InlineKeyboardButton("⬅️ Menu", callback_data="wa_home")],
            ]))
        return
    if data.startswith("wa_start_") or data.startswith("wa_stop_"):
        slot = int(data.rsplit("_", 1)[1])
        jid = _get_mapping(update.effective_user.id)
        if not jid:
            await query.message.reply_text("Recipient set nahi hai. `/whatsapp` se dobara setup karein.")
            return
        wa_app = _load_whatsapp_app()
        wa_client = _get_whatsapp_client(update.effective_user.id)
        user_manager = _load_user_manager(wa_app)
        wa_app.bot_handler.register_client_route(jid, wa_client)
        user_manager.select_slot(jid, slot)
        if data.startswith("wa_start_"):
            wa_app.bot_handler.start_user_automation(jid)
            buttons = [[InlineKeyboardButton("⏹ Stop automation", callback_data=f"wa_stop_{slot}")]]
        else:
            wa_app.bot_handler.stop_user_automation(jid)
            buttons = [[InlineKeyboardButton("▶️ Start automation", callback_data=f"wa_start_{slot}")]]
        await query.message.reply_text(f"Automation {slot} control updated for `{jid}`.", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))


def _load_user_manager(wa_app):
    return importlib.import_module("modules.config").user_manager


async def handle_whatsapp_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Consume text replies while a recipient or automation prompt is being configured."""
    message = update.effective_message
    flow = context.user_data.get(_flow_key)
    if not message or not message.text or not flow:
        return False
    if update.effective_chat and update.effective_chat.type != "private":
        return False
    if time.time() > flow.get("deadline", 0):
        context.user_data.pop(_flow_key, None)
        await message.reply_text("⏰ 5 minute ka setup time khatam. `/whatsapp` se dobara automation choose karein.")
        return True
    answer = message.text.strip()
    if flow["stage"] == "pair_number":
        digits = re.sub(r"[\s()+-]", "", answer)
        if not digits.isdigit() or not 8 <= len(digits) <= 15:
            await message.reply_text("Number country code ke saath bhejein. Example: `919876543210`", parse_mode="Markdown")
            return True
        wa_app = _load_whatsapp_app()
        wa_client = _get_whatsapp_client(update.effective_user.id)
        async with _start_lock:
            status = wa_client.get_status()
            if status.get("worker_alive"):
                await message.reply_text("WhatsApp client pehle se start hai. Mode switch karne ke liye bot restart karke dobara try karein.")
                context.user_data.pop(_flow_key, None)
                return True
            wa_client.start(phone_number=digits, new_device=True)
        status = wa_client.get_status()
        for _ in range(40):
            if status.get("pairing_code") or status.get("connected"):
                break
            if status.get("connection_error"):
                break
            await asyncio.sleep(0.5)
            status = wa_client.get_status()
        context.user_data.pop(_flow_key, None)
        if status.get("pairing_code"):
            await message.reply_text(
                "🔢 *WhatsApp linking code:*\n\n"
                f"`{status['pairing_code']}`\n\n"
                "WhatsApp app mein Settings → Linked devices → Link a device → *Link with phone number instead* chunein, phir code enter karein. Telegram par QR scan ki zarurat nahi hai.",
                parse_mode="Markdown")
        elif status.get("connected"):
            await message.reply_text("✅ WhatsApp account pehle se connected hai.")
        else:
            err = status.get("connection_error")
            detail = f"\n\nError: {err[:500]}" if err else ""
            await message.reply_text("⚠️ Pairing code nahi mila. `/whatsapp` se dobara try karein ya QR method chunein." + detail)
        return True
    if flow["stage"] == "number":
        digits = re.sub(r"[\s()+-]", "", answer)
        if not digits.isdigit() or not 8 <= len(digits) <= 15:
            await message.reply_text("Number sahi format me bhejein, country code ke saath. Example: `919876543210`", parse_mode="Markdown")
            return True
        _save_mapping(update.effective_user.id, digits)
        wa_client = _get_whatsapp_client(update.effective_user.id)
        _load_whatsapp_app().bot_handler.register_client_route(digits, wa_client)
        slot = flow["slot"]
        context.user_data[_flow_key] = {"stage": "topic", "slot": slot, "deadline": time.time() + 300}
        await message.reply_text(f"✅ Recipient number save ho gaya. Ab Automation {slot} ka topic/prompt bhejein (5 minute ke andar).")
        return True
    if flow["stage"] == "topic":
        if len(answer) < 5:
            await message.reply_text("Thoda aur detail likhein: kis topic par, kya jankari chahiye, aur koi preferred platform/region?")
            return True
        slot = flow["slot"]
        context.user_data.pop(_flow_key, None)
        wa_app = _load_whatsapp_app()
        prompt = await asyncio.to_thread(
            _draft_prompt, wa_app, answer
        )
        context.user_data["wa_review_prompt"] = prompt
        await message.reply_text(
            f"🧠 *Automation {slot} ke liye tayyar kiya gaya prompt:*\n\n"
            f"{prompt[:3000]}\n\nIs prompt ko save karke automation start karein?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Save prompt", callback_data=f"wa_review_{slot}")],
                [InlineKeyboardButton("✏️ Change prompt", callback_data=f"wa_slot_{slot}")],
            ]))
        return True
    return False


def _draft_prompt(wa_app, user_idea: str) -> str:
    """Expand the user's description into clear, grounded research instructions."""
    try:
        gemini = importlib.import_module("modules.gemini_ai").gemini_service
        refined = gemini.generate_with_fallback(
            f"Turn this user's WhatsApp automation idea into a focused recurring web-research prompt. "
            "Preserve their intent. Specify what to find, useful details to include, freshness, reliable/official sources, "
            "and a readable WhatsApp message format. Do not invent facts. Output only the finished prompt.\n\n"
            f"User idea: {user_idea}"
        )
        if refined and len(refined.strip()) >= 20:
            return refined.strip()
    except Exception:
        pass
    return (
        f"Research this topic: {user_idea}\n"
        "Find recent, relevant results. Verify key facts against reliable or official sources. "
        "For each result, provide a clear title, concise summary, important features/details, practical usefulness, "
        "and a direct source link. Do not repeat earlier discoveries or invent missing facts. Format the update for easy WhatsApp reading."
    )
