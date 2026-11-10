import os
import re
import time
import logging
import threading
from typing import Optional, Dict, Any

from modules.config import config_manager, user_manager, logger, jid_to_str, str_to_jid
from modules.gemini_ai import gemini_service
from modules.downloader import media_downloader
from modules.discovery import discovery_engine

class BotHandler:
    def __init__(self, whatsapp_client=None):
        self.client = whatsapp_client
        self.client_routes = {}
        self.scheduler_thread = None
        self.scheduler_stop_event = threading.Event()
        self._start_master_scheduler()

    def set_client(self, whatsapp_client):
        if self.client is None:
            self.client = whatsapp_client

    def register_client_route(self, jid, whatsapp_client):
        """Route outgoing messages for a WhatsApp destination through its owner's session."""
        key = jid_to_str(jid)
        if key:
            self.client_routes[key] = whatsapp_client

    def send_reply(self, to_jid, message: str):
        client = self.client_routes.get(jid_to_str(to_jid), self.client)
        if client:
            try:
                client.send_text(to_jid, message)
            except Exception as e:
                logger.error(f"Failed to send message to {to_jid}: {e}")

    FREE_AI_LIMIT = 3

    def send_english_guide(self, sender_jid, intro_header="🤖 *WhatsApp Bot User Guide & Commands:*"):
        """Send complete English command manual and usage instructions."""
        guide = (
            f"{intro_header}\n\n"
            "This bot allows you to create and manage up to *3 separate research automations* (Slots 1, 2, and 3).\n\n"
            "📋 *All Available Commands:*\n"
            "• */list* - View all 3 automations with status, topics, and timer intervals\n"
            "• */1select* - Select Automation #1 (and stop others)\n"
            "• */2select* - Select Automation #2 (and stop others)\n"
            "• */3select* - Select Automation #3 (and stop others)\n"
            "• */start* - Start running the currently selected automation\n"
            "• */stop* - Pause the currently running automation\n"
            "• */timer <minutes>* - Set or change timer interval (e.g. `/timer 1`, `/timer 2`, `/timer 5`)\n"
            "• */create <1|2|3> <topic>* - Create or update an automation topic\n"
            "• */delete <1|2|3>* - Delete/clear an automation slot\n"
            "• */name <your_name>* - Update or check your registered name\n\n"
            "🎬 *Media & Cloud Video Player:*\n"
            "• */yt <link>* - Watch/Download YouTube video (1080p, 720p, 480p, MP3)\n"
            "• */insta <link>* - Watch/Download Instagram reel or video\n"
            "• Send any *YouTube* or *Instagram* link to get the instant streaming portal!\n"
            "• Send any *photo* for instant AI analysis\n"
            "• Ask any question anytime for live AI answers *(3 free questions)*\n"
            "• */key* - Manage your Gemini API key (Unlock unlimited AI questions!)\n"
            "• */key <API_KEY>* - Enter your Google API key for unlimited free access\n\n"
            "📖 *How to use in 4 easy steps:*\n"
            "1️⃣ Send */list* to see your 3 automation slots\n"
            "2️⃣ Send */1select* (or */2select*, */3select*) to pick which automation you want\n"
            "3️⃣ Send */timer 2* (or any minutes) to set your update interval\n"
            "4️⃣ Send */start* to begin receiving live updates! Send */stop* anytime to pause.\n\n"
            "🧾 *Detailed update format:*\n"
            "Each research update includes a clear title, what the project does, useful features, practical use, quality notes, an official link, and the verification date. Results are selected from live search and repeated discoveries are filtered when possible.\n\n"
            "💡 *Topic ko specific rakhein:* Include category + use case + platform.\n"
            "Example: `/create 1 Open-source Android note-taking apps with offline sync, privacy details, F-Droid links, and recent updates`\n"
            "Example: `/create 2 New Python AI tools for local image generation, GitHub activity, hardware needs, and setup steps`\n"
            "Aap topic me language, budget, region, date range, ya preferred sources bhi likh sakte hain."
        )
        self.send_reply(sender_jid, guide)

    def get_key_required_message_en(self) -> str:
        """Default English message when free AI quota is reached."""
        return (
            "🛑 *Free AI Limit Reached (3/3 Questions Used)* 🛑\n\n"
            "You have used your 3 free AI questions. To protect bot server resources and continue using AI with *Unlimited Questions & Image Analysis*, please add your personal free Google Gemini API key!\n\n"
            "Adding your own API key gives you *Unlimited 24/7 Access* with zero limits! 🚀\n\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "✨ *How to get your FREE Google Gemini API Key:*\n"
            "1️⃣ Open this official Google AI Studio link in your browser:\n"
            "   👉 https://aistudio.google.com/app/apikey\n"
            "2️⃣ Sign in with your Google (Gmail) account.\n"
            "3️⃣ Click the *'Create API key'* button (100% free with high daily quotas).\n"
            "4️⃣ Copy your generated key (keys start with `AQ.` or `AIzaSy`).\n\n"
            "🔑 *How to activate it in WhatsApp:*\n"
            "Send this command in this chat:\n"
            "👉 */key YOUR_API_KEY*\n\n"
            "📝 *Example:*\n"
            "`/key AQ.Abc123YourKeyHere...`\n\n"
            "✅ *What happens next:*\n"
            "• The host API key turns OFF for your chat.\n"
            "• Your personal key takes over with *Unlimited Access*!\n"
            "━━━━━━━━━━━━━━━━━━━"
        )

    def get_key_required_message_hi(self) -> str:
        """Hindi explanation provided when user requests explanation in Hindi."""
        return (
            "🛑 *Free AI Limit Reached (3/3 Questions Used)* 🛑\n\n"
            "Aapne apne 3 free questions use kar liye hain. Bot host ki API quota limit protect karne ke liye, ab aapko apna *Google Gemini API Key* set karna hoga.\n\n"
            "Apna personal API key enter karne ke baad aapko milega *Unlimited AI Access* (Questions + Photo Analysis)! 🚀\n\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "✨ *Apna Free Google API Key kaise nikalein?*\n"
            "1️⃣ Browser me yeh official link open karein:\n"
            "   👉 https://aistudio.google.com/app/apikey\n"
            "2️⃣ Apne Google Account (Gmail) se Login karein.\n"
            "3️⃣ *'Create API key'* button par click karein.\n"
            "4️⃣ Jo key generate hogi use Copy kar lein (Key `AQ....` ya `AIzaSy...` se shuru hoti hai).\n\n"
            "🔑 *WhatsApp Bot me Key kaise activate karein?*\n"
            "Is chat me command bhejein:\n"
            "👉 */key APNA_API_KEY*\n\n"
            "📝 *Example:*\n"
            "`/key AQ.Abc123YourKeyHere...`\n\n"
            "✅ *Key set hote hi:*\n"
            "• Bot host ka original API key aapke liye off ho jayega.\n"
            "• Aapka khud ka API key activate ho jayega with *Unlimited Access*!\n"
            "━━━━━━━━━━━━━━━━━━━"
        )

    def get_key_required_message(self, used_count: int = 3, lang: str = "en") -> str:
        """Get key requirement message in requested language (English default)."""
        if lang == "hi":
            return self.get_key_required_message_hi()
        return self.get_key_required_message_en()

    def handle_key_command(self, sender_jid, raw_arg: Optional[str]):
        """Manage user's personal Google Gemini API key for unlimited AI usage."""
        jid_str = jid_to_str(sender_jid)
        user = user_manager.get_or_create_user(jid_str)
        custom_key = user.get("custom_gemini_key", "").strip()
        used_count = user.get("ai_query_count", 0)

        # 1. No arguments or status check
        if not raw_arg or raw_arg.lower() in ["status", "check", "info"]:
            if custom_key:
                masked = custom_key[:8] + "..." + custom_key[-4:] if len(custom_key) > 12 else "********"
                msg = (
                    "🔑 *Your Personal Gemini API Key:*\n\n"
                    f"• Status: 🟢 *Active (Unlimited Access)*\n"
                    f"• Key: `{masked}`\n"
                    "• Mode: Custom Personal Key (Host key is OFF for you)\n\n"
                    "⚙️ *Available Options:*\n"
                    "• Update key: `/key <NEW_API_KEY>`\n"
                    "• Remove key: `/key remove`\n"
                    "• Help / Guide: `/key help`"
                )
            else:
                remaining = max(0, 3 - used_count)
                msg = (
                    "🔑 *Your Gemini API Key Status:*\n\n"
                    f"• Status: ⚪ *Default Host Key*\n"
                    f"• Free Questions Used: *{min(used_count, 3)}/3* (Remaining: {remaining})\n\n"
                    "🚀 *Want Unlimited AI Access?*\n"
                    "Get your free key from: https://aistudio.google.com/app/apikey\n"
                    "Then send: */key YOUR_API_KEY*"
                )
            self.send_reply(sender_jid, msg)
            return

        arg_lower = raw_arg.strip().lower()

        # 2. Help tutorial (English default)
        if arg_lower in ["help", "guide", "tutorial", "howto"]:
            self.send_reply(sender_jid, self.get_key_required_message_en())
            return

        # 3. Remove key
        if arg_lower in ["remove", "delete", "clear", "reset"]:
            user_manager.remove_user_api_key(jid_str)
            self.send_reply(
                sender_jid,
                "🗑️ *Personal API Key Removed!*\n\n"
                "Your personal key has been cleared. The bot has reverted to default access.\n"
                "To set a new key anytime, send: `/key <API_KEY>`"
            )
            return

        # 4. Set new key
        new_key = raw_arg.strip()
        if len(new_key) < 20 or any(c.isspace() for c in new_key):
            self.send_reply(
                sender_jid,
                "❌ *Invalid API Key Format!*\n\n"
                "The Gemini API key cannot contain spaces and must be at least 20 characters long (typically starting with `AQ.` or `AIzaSy`).\n\n"
                "Please copy the complete key from:\n"
                "👉 https://aistudio.google.com/app/apikey\n\n"
                "Syntax: `/key YOUR_API_KEY`"
            )
            return

        self.send_reply(sender_jid, "⏳ *Verifying your Gemini API Key with Google...* Please wait a moment.")

        is_valid, err_msg = gemini_service.validate_api_key(new_key)
        if not is_valid:
            self.send_reply(
                sender_jid,
                f"❌ *API Key Verification Failed!*\n\n"
                f"Google Gemini rejected this key.\n"
                f"Error: _{err_msg}_\n\n"
                "Please verify:\n"
                "1. You copied the entire key without extra spaces.\n"
                "2. The key is active on Google AI Studio.\n"
                "👉 https://aistudio.google.com/app/apikey"
            )
            return

        # Success - Save key
        user_manager.set_user_api_key(jid_str, new_key)
        masked = new_key[:8] + "..." + new_key[-4:]
        self.send_reply(
            sender_jid,
            f"🎉 *Gemini API Key Verified & Activated!* ✅\n\n"
            f"• Key: `{masked}`\n"
            f"• Access: 🟢 *Unlimited AI Questions & Photo Analysis*\n"
            f"• Bot Host API: *OFF* (Now running exclusively on your key!)\n\n"
            "Your 3-question free limit has been permanently removed. You can now ask unlimited questions and send photos anytime! 🚀\n\n"
            "👉 Try asking any question now!"
        )

    def handle_ai_chat_query(self, sender_jid, text: str):
        """Handle AI question while enforcing 3-query free limit or user's custom key."""
        jid_str = jid_to_str(sender_jid)
        user = user_manager.get_or_create_user(jid_str)
        user_key = user.get("custom_gemini_key", "").strip()
        user_name = user.get("name", "").strip() or "User"

        # Case A: User has their own API key -> UNLIMITED ACCESS!
        if user_key:
            ai_response = gemini_service.chat_response(text, api_key=user_key, user_name=user_name)
            self.send_reply(sender_jid, ai_response)
            return

        # Case B: User is on default host API key -> 3 free questions limit
        used_count = user.get("ai_query_count", 0)
        if used_count >= self.FREE_AI_LIMIT:
            # 4th question or more without key -> BLOCK and ask for key
            msg = self.get_key_required_message(used_count)
            self.send_reply(sender_jid, msg)
            return

        # Still within 3 free questions (Question 1, 2, or 3)
        new_count = user_manager.increment_ai_query_count(jid_str)
        ai_response = gemini_service.chat_response(text, api_key=None, user_name=user_name)

        if new_count < self.FREE_AI_LIMIT:
            footer = f"\n\n_(💡 Free AI questions: {new_count}/{self.FREE_AI_LIMIT} used. Unlock unlimited access with /key)_"
        else:
            footer = (
                f"\n\n_(⚠️ You have used all {new_count}/{self.FREE_AI_LIMIT} free AI questions!\n"
                f"Next questions require your own free Google Gemini API key.\n"
                f"Get it from https://aistudio.google.com/app/apikey and send: /key YOUR_API_KEY)_"
            )
        self.send_reply(sender_jid, ai_response + footer)

    def send_automation_list(self, sender_jid):
        """Send formatted overview of all 3 automation slots."""
        jid_str = jid_to_str(sender_jid)
        user = user_manager.get_or_create_user(jid_str)
        selected_slot = int(user.get("selected_slot", 1))
        is_user_active = user.get("is_active", False)
        automations = user.get("automations", {})

        cards = []
        for i in [1, 2, 3]:
            s_data = automations.get(str(i), {})
            prompt = s_data.get("prompt", "").strip()
            interval = s_data.get("interval_minutes", 5)
            count = s_data.get("discovery_count", 0)

            is_selected = (i == selected_slot)
            if is_selected:
                if is_user_active:
                    status = "🟢 *ACTIVE & RUNNING*"
                else:
                    status = "🟡 *SELECTED (Stopped - Ready to /start)*"
            else:
                if prompt:
                    status = "🔴 *STOPPED*"
                else:
                    status = "⚪ *EMPTY (Available)*"

            if prompt:
                first_line = prompt.split("\n")[0]
                prompt_preview = (first_line[:50] + "...") if len(first_line) > 50 else first_line
            else:
                prompt_preview = f"_(Empty - use /create {i} <topic>)_"

            cards.append(
                f"*{i}️⃣ Automation #{i}* [{status}]\n"
                f"   • *Topic:* {prompt_preview}\n"
                f"   • *Timer:* Every *{interval}* min(s)\n"
                f"   • *Discoveries Sent:* {count}"
            )

        active_label = f"Slot #{selected_slot} ({'🟢 Running' if is_user_active else '🟡 Selected / Stopped'})"
        reply = (
            "📋 *Your Automations (3 Slots):*\n\n"
            + "\n\n".join(cards) + "\n\n"
            f"🎯 *Current Selection:* {active_label}\n\n"
            "⚡ *Control Commands:*\n"
            "• Switch slot: */1select* | */2select* | */3select*\n"
            "• Start selected: */start*\n"
            "• Pause: */stop*\n"
            "• Change timer: */timer <min>* (e.g. `/timer 2`)\n"
            "• Create/Edit: */create <1|2|3> <topic>*\n"
            "• Delete slot: */delete <1|2|3>*"
        )
        self.send_reply(sender_jid, reply)

    def handle_slot_selection(self, sender_jid, target_slot: int):
        """Select slot 1, 2, or 3. Active execution pauses until user sends /start."""
        jid_str = jid_to_str(sender_jid)
        success, slot_data = user_manager.select_slot(jid_str, target_slot)
        if not success:
            self.send_reply(sender_jid, "⚠️ Invalid slot number. Please choose 1, 2, or 3.")
            return

        other_slots = [str(x) for x in [1, 2, 3] if x != target_slot]
        prompt = slot_data.get("prompt", "").strip()
        interval = slot_data.get("interval_minutes", 5)

        if prompt:
            first_line = prompt.split("\n")[0]
            prompt_preview = (first_line[:60] + "...") if len(first_line) > 60 else first_line
            prompt_str = f"\"{prompt_preview}\""
        else:
            prompt_str = f"_(No topic set yet - send /create {target_slot} <topic>)_"

        reply = (
            f"✅ *Automation #{target_slot} Selected!*\n\n"
            f"• *Topic:* {prompt_str}\n"
            f"• *Timer:* Every *{interval}* minute(s)\n"
            f"• *Status:* Ready (Automations #{other_slots[0]} and #{other_slots[1]} are stopped)\n\n"
            f"👉 Send */start* to begin running Automation #{target_slot}!\n"
            f"👉 Or send */timer <minutes>* to adjust the interval."
        )
        self.send_reply(sender_jid, reply)

    def handle_slot_deletion(self, sender_jid, target_slot: Optional[int]):
        """Delete / reset an automation slot."""
        jid_str = jid_to_str(sender_jid)
        if target_slot not in [1, 2, 3]:
            self.send_reply(
                sender_jid,
                "🗑️ *Delete an Automation:*\n\n"
                "Please specify which slot to delete:\n"
                "• Send */delete 1* to delete Automation #1\n"
                "• Send */delete 2* to delete Automation #2\n"
                "• Send */delete 3* to delete Automation #3\n\n"
                "Send */list* to see your current slots before deleting."
            )
            return

        user_manager.delete_slot(jid_str, target_slot)
        self.send_reply(
            sender_jid,
            f"🗑️ *Automation #{target_slot} Deleted!*\n\n"
            f"Slot #{target_slot} has been cleared and stopped.\n"
            f"You can now create a fresh automation in Slot #{target_slot} anytime!\n\n"
            f"👉 To create: send */create {target_slot} <your new topic>*\n"
            f"👉 Send */list* to check your slots."
        )

    def handle_timer_command(self, sender_jid, minutes: Optional[int]):
        """Change or view the timer for the currently selected slot."""
        jid_str = jid_to_str(sender_jid)
        user = user_manager.get_or_create_user(jid_str)
        slot_num = int(user.get("selected_slot", 1))
        slot_data = user.get("automations", {}).get(str(slot_num), {})
        curr_interval = slot_data.get("interval_minutes", 5)

        if minutes is None:
            self.send_reply(
                sender_jid,
                f"⏱️ *Timer Settings for Automation #{slot_num}:*\n\n"
                f"• Current Interval: Every *{curr_interval}* minute(s)\n\n"
                f"To change the timer, send:\n"
                f"👉 */timer 1* (every 1 minute)\n"
                f"👉 */timer 2* (every 2 minutes)\n"
                f"👉 */timer 5* (every 5 minutes)\n"
                f"👉 */timer 15* (every 15 minutes)"
            )
            return

        new_val = max(1, minutes)
        user_manager.set_slot_interval(jid_str, new_val, slot_num=slot_num)
        self.send_reply(
            sender_jid,
            f"⏱️ *Timer Updated for Automation #{slot_num}!*\n\n"
            f"Interval is now set to *{new_val} minute(s)*.\n"
            f"Updates will arrive every {new_val} minute(s) when running.\n\n"
            f"👉 Send */start* if you want to begin running now!"
        )

    def handle_create_command(self, sender_jid, raw_text: str):
        """Create or update an automation slot: /create <1|2|3> <topic> or /create <topic>."""
        jid_str = jid_to_str(sender_jid)
        user = user_manager.get_or_create_user(jid_str)

        # Match /create <1|2|3> <topic>
        m_slot = re.match(r"^/?create\s+([123])\s+(.+)$", raw_text, re.IGNORECASE | re.DOTALL)
        if m_slot:
            slot_num = int(m_slot.group(1))
            topic = m_slot.group(2).strip()
            user_manager.set_slot_prompt(jid_str, slot_num, topic)
            slot_data = user.get("automations", {}).get(str(slot_num), {})
            interval = slot_data.get("interval_minutes", 5)
            first_line = topic.split("\n")[0]
            preview = (first_line[:60] + "...") if len(first_line) > 60 else first_line
            self.send_reply(
                sender_jid,
                f"✅ *Automation #{slot_num} Created & Saved!*\n\n"
                f"🎯 *Topic:* \"{preview}\"\n"
                f"⏱️ *Timer:* Every {interval} minute(s)\n\n"
                f"👉 Send */{slot_num}select* to select this automation, then send */start* to begin!"
            )
            return

        # Match /create <topic> (without slot number, applies to currently selected slot)
        m_curr = re.match(r"^/?create\s+(.+)$", raw_text, re.IGNORECASE | re.DOTALL)
        if m_curr:
            topic = m_curr.group(1).strip()
            slot_num = int(user.get("selected_slot", 1))
            user_manager.set_slot_prompt(jid_str, slot_num, topic)
            slot_data = user.get("automations", {}).get(str(slot_num), {})
            interval = slot_data.get("interval_minutes", 5)
            first_line = topic.split("\n")[0]
            preview = (first_line[:60] + "...") if len(first_line) > 60 else first_line
            self.send_reply(
                sender_jid,
                f"✅ *Automation #{slot_num} Saved!*\n\n"
                f"🎯 *Topic:* \"{preview}\"\n"
                f"⏱️ *Timer:* Every {interval} minute(s)\n\n"
                f"👉 Send */start* to run Automation #{slot_num}!"
            )
            return

        # /create without parameters
        self.send_reply(
            sender_jid,
            "📝 *Create a New Automation:*\n\n"
            "You can configure up to 3 separate automations.\n"
            "Syntax: */create <slot_number> <topic + detail preferences>*\n"
            "Achhe results ke liye topic me category, kis kaam ke liye chahiye, platform, aur kya details chahiye batayein.\n\n"
            "💡 *Examples:*\n"
            "• `/create 1 Latest AI coding tools, key features, pricing/free tier, supported platforms, and official links`\n"
            "• `/create 2 Open-source Android apps with privacy, offline support, F-Droid link, and recent updates`\n"
            "• `/create 3 Gaming news for India: release date, platforms, price, and official source`\n\n"
            "Choose a slot (1, 2, or 3) and send your topic!"
        )

    def handle_topic_command(self, sender_jid, raw_text: str):
        """Update topic for currently selected slot."""
        jid_str = jid_to_str(sender_jid)
        user = user_manager.get_or_create_user(jid_str)
        slot_num = int(user.get("selected_slot", 1))

        parts = raw_text.split(" ", 1)
        if len(parts) > 1 and parts[1].strip():
            new_topic = parts[1].strip()
            user_manager.set_slot_prompt(jid_str, slot_num, new_topic)
            first_line = new_topic.split("\n")[0]
            preview = (first_line[:60] + "...") if len(first_line) > 60 else first_line
            self.send_reply(
                sender_jid,
                f"✅ *Topic Updated for Automation #{slot_num}!*\n\n"
                f"🎯 *New Topic:* \"{preview}\"\n"
                f"Future updates in Automation #{slot_num} will research this topic.\n\n"
                f"👉 Send */start* to begin or */stop* to pause."
            )
        else:
            self.send_reply(
                sender_jid,
                f"⚠️ Please provide a topic:\nExample: */topic Latest AI tools and models*"
            )

    def handle_incoming_text(self, sender_jid, text: str):
        """Main dispatcher for incoming text messages from any WhatsApp user."""
        raw_text = text.strip()
        lower_text = raw_text.lower()
        jid_str = jid_to_str(sender_jid)
        user = user_manager.get_or_create_user(jid_str)
        current_state = user.get("state", "UNAUTHENTICATED")

        logger.info(f"Incoming from {jid_str} [State={current_state}]: {raw_text[:50]}")

        # Global trigger: 'hillo' initiates password authentication
        if lower_text in ["hillo", "hillo!", "hillo."]:
            user_manager.update_user(jid_str, state="WAITING_PASSWORD")
            self.send_reply(
                sender_jid,
                "👋 Hello! Please enter the password to access the bot:"
            )
            return

        # 1. State: UNAUTHENTICATED
        if current_state == "UNAUTHENTICATED":
            creator_ans = gemini_service.check_creator_query(raw_text)
            if creator_ans:
                self.send_reply(sender_jid, creator_ans)
                return

            if any(w in lower_text for w in ["help", "madat", "madad", "samjha nahi"]):
                self.send_reply(
                    sender_jid,
                    "🔒 *WhatsApp Bot Help:*\n\n"
                    "To start using this bot, please send *hillo* to begin authentication.\n"
                    "You will then be prompted to enter the secret password."
                )
                return

            self.send_reply(
                sender_jid,
                "🔒 *Access Restricted.*\n"
                "Please send *hillo* to initiate authentication and access the bot."
            )
            return

        # 2. State: WAITING_PASSWORD
        if current_state == "WAITING_PASSWORD":
            correct_password = config_manager.get("bot_password", "satyam08052010")
            if raw_text == correct_password:
                user_manager.update_user(jid_str, state="WAITING_NAME")
                self.send_reply(
                    sender_jid,
                    "✅ *Password Verified!*\n\n"
                    "What is your name? Please enter your name:"
                )
            else:
                self.send_reply(
                    sender_jid,
                    "❌ *Incorrect password!*\n"
                    "Please enter the correct password to continue."
                )
            return

        # 3. State: WAITING_NAME (Capture user's name and personalize bot)
        if current_state == "WAITING_NAME":
            name = raw_text.strip()
            name = re.sub(r"^/+", "", name).strip()
            if not name or len(name) < 2:
                self.send_reply(
                    sender_jid,
                    "⚠️ Please enter a valid name:\nWhat is your name?"
                )
                return

            # Save personalized user name and transition to AUTHENTICATED
            user_manager.update_user(jid_str, name=name, state="AUTHENTICATED")

            # Personalize default automation topic if it mentions Satyam
            automations = user.get("automations", {})
            for s_key, s_data in automations.items():
                p = s_data.get("prompt", "")
                if "Satyam Discovery Feed" in p:
                    s_data["prompt"] = p.replace("Satyam Discovery Feed", f"{name} Discovery Feed")
            user_manager.save_users()

            # Welcome message with user's name
            welcome_header = f"🎉 *Welcome, {name}! Your access has been activated.*"
            self.send_english_guide(sender_jid, intro_header=welcome_header)
            return

        # 3. State: AUTHENTICATED Commands & Controls

        # /list - View all 3 automations
        if lower_text in ["/list", "list", "/all", "all"]:
            self.send_automation_list(sender_jid)
            return

        # /1select, /2select, /3select or /select 1, /select 2, /select 3
        slot_sel_match = re.match(r"^/?(?:([123])select|select\s*([123])|select([123]))$", lower_text)
        if slot_sel_match:
            slot_num = int(slot_sel_match.group(1) or slot_sel_match.group(2) or slot_sel_match.group(3))
            self.handle_slot_selection(sender_jid, slot_num)
            return

        # /start - Start selected automation
        if lower_text in ["/start", "start", "/run", "run"]:
            self.start_user_automation(sender_jid)
            return

        # /stop - Stop active automation
        if lower_text in ["/stop", "stop", "/pause", "pause"]:
            self.stop_user_automation(sender_jid)
            return

        # /delete [1/2/3] - Delete automation slot
        del_match = re.match(r"^/?delete(?:\s*([123]))?$", lower_text)
        if del_match:
            slot_arg = del_match.group(1)
            target = int(slot_arg) if slot_arg else None
            self.handle_slot_deletion(sender_jid, target)
            return

        # /timer [min] - Change or view timer
        timer_patterns = [
            r"^/?(?:timer|interval)\s+(\d+)$",
            r"^(\d+)\s*(?:min|mins|minute|minutes)$",
            r"^har\s+(\d+)\s*(?:min|mins|minute|minutes)$",
            r"^every\s+(\d+)\s*(?:min|mins|minute|minutes)$"
        ]
        detected_min = None
        for pattern in timer_patterns:
            m = re.match(pattern, lower_text)
            if m:
                detected_min = max(1, int(m.group(1)))
                break

        if detected_min is not None:
            self.handle_timer_command(sender_jid, detected_min)
            return

        if lower_text in ["/timer", "timer", "/interval", "interval"]:
            self.handle_timer_command(sender_jid, None)
            return

        # /create [slot] [topic] - Create new automation
        if lower_text == "/create" or lower_text == "create" or lower_text.startswith("/create ") or lower_text.startswith("create "):
            self.handle_create_command(sender_jid, raw_text)
            return

        # /key command - Manage personal Gemini API key
        key_match = re.match(r"^/?(?:key|apikey)(?:\s+(.+))?$", raw_text, re.IGNORECASE | re.DOTALL)
        if key_match:
            arg = key_match.group(1)
            self.handle_key_command(sender_jid, arg.strip() if arg else None)
            return

        # /name command - View or update user's registered name
        name_match = re.match(r"^/?name(?:\s+(.+))?$", raw_text, re.IGNORECASE)
        if name_match:
            new_name_val = name_match.group(1)
            if new_name_val and new_name_val.strip():
                clean_name = new_name_val.strip()
                user_manager.update_user(jid_str, name=clean_name)
                self.send_reply(sender_jid, f"✅ Your name has been updated to *{clean_name}*!")
            else:
                curr_name = user.get("name") or "Friend"
                self.send_reply(
                    sender_jid,
                    f"👤 *Your Registered Name:* {curr_name}\n\n"
                    "To update your name, send:\n"
                    "👉 `/name <new_name>`\n"
                    "Example: `/name Rahul`"
                )
            return

        # /topic [topic] - Update topic of currently selected slot
        if lower_text.startswith("/topic ") or lower_text.startswith("topic ") or lower_text.startswith("/prompt ") or lower_text.startswith("prompt "):
            self.handle_topic_command(sender_jid, raw_text)
            return

        # /help or help
        if lower_text in ["/help", "help", "/commands", "commands", "/guide", "guide", "madat", "madad"]:
            self.send_english_guide(sender_jid)
            return

        # On-demand Hindi explanation when user asks in Hindi or says they didn't understand
        hindi_triggers = [
            "samajh nahi aaya", "samjha nahi", "samajh nhi aaya", "kuch samajh nahi aaya",
            "hindi me batao", "hindi me samjhao", "hindi mein batao", "hindi mein samjhao",
            "hindi me", "in hindi", "hindi please", "hindi help"
        ]
        if any(trig in lower_text for trig in hindi_triggers):
            self.send_reply(sender_jid, self.get_key_required_message_hi())
            return

        # /yt <link> - YouTube video streaming & quality download
        yt_match = re.match(r"^/?(?:yt|youtube)\s+(.+)$", raw_text, re.IGNORECASE)
        if yt_match:
            candidate_url = yt_match.group(1).strip()
            v_url = media_downloader.extract_video_url(candidate_url) or candidate_url
            self.handle_video_download(sender_jid, v_url)
            return

        # /insta <link> - Instagram video streaming & quality download
        insta_match = re.match(r"^/?(?:insta|instagram|ig)\s+(.+)$", raw_text, re.IGNORECASE)
        if insta_match:
            candidate_url = insta_match.group(1).strip()
            v_url = media_downloader.extract_video_url(candidate_url) or candidate_url
            self.handle_video_download(sender_jid, v_url)
            return

        # Auto-detect direct video links (YouTube or Instagram)
        video_url = media_downloader.extract_video_url(raw_text)
        if video_url:
            self.handle_video_download(sender_jid, video_url)
            return

        # Creator query check
        creator_ans = gemini_service.check_creator_query(raw_text)
        if creator_ans:
            self.send_reply(sender_jid, creator_ans)
            return

        # Photo generation refusal check
        img_gen_refusal = gemini_service.check_image_generation_query(raw_text)
        if img_gen_refusal:
            self.send_reply(sender_jid, img_gen_refusal)
            return

        # General questions / chat with 3-question quota protection & custom key support
        self.handle_ai_chat_query(sender_jid, raw_text)

    def handle_incoming_image(self, sender_jid, image_bytes: bytes, caption: str = ""):
        """Handle incoming image analysis for authenticated users with quota / custom key check."""
        jid_str = jid_to_str(sender_jid)
        user = user_manager.get_or_create_user(jid_str)
        if user.get("state") != "AUTHENTICATED":
            self.send_reply(
                jid_str,
                "🔒 Please authenticate with *hillo* and the password first to analyze images."
            )
            return

        user_key = user.get("custom_gemini_key", "").strip()
        new_count = 0
        if not user_key:
            used_count = user.get("ai_query_count", 0)
            if used_count >= self.FREE_AI_LIMIT:
                msg = self.get_key_required_message(used_count)
                self.send_reply(jid_str, msg)
                return
            new_count = user_manager.increment_ai_query_count(jid_str)

        self.send_reply(jid_str, "🔍 Analyzing image, please wait...")
        analysis = gemini_service.analyze_image(image_bytes, caption, api_key=user_key or None)

        if not user_key:
            if new_count < self.FREE_AI_LIMIT:
                analysis += f"\n\n_(💡 Free AI queries: {new_count}/{self.FREE_AI_LIMIT} used. Set your key with /key for unlimited access)_"
            else:
                analysis += f"\n\n_(⚠️ 3/3 free queries used. Set your key with /key for unlimited access)_"

        self.send_reply(jid_str, analysis)

    def handle_video_download(self, sender_jid, video_url: str):
        """Send cloud streaming portal link with quality selection (1080p, 720p, 480p, MP3) and handle downloads."""
        target_jid = jid_to_str(sender_jid)

        def task():
            self.send_reply(target_jid, f"🔍 *Inspecting video link...*\n`{video_url}`")
            info = media_downloader.get_video_info(video_url)
            watch_url = media_downloader.get_watch_url(video_url)

            if info:
                title = info.get("title", "Video")
                duration = info.get("duration_str", "N/A")
                uploader = info.get("uploader", "Creator")
                platform = info.get("platform", "Video")

                card = (
                    f"🎬 *{title}*\n\n"
                    f"👤 *Creator:* {uploader}\n"
                    f"⏱️ *Duration:* {duration}\n"
                    f"🌐 *Platform:* {platform}\n\n"
                    f"🍿 *Cloud Watch & Download Link (No WiFi Needed!):*\n"
                    f"👉 {watch_url}\n\n"
                    "⚡ *Cloud Portal Features:*\n"
                    "• ☁️ *Cloudflare HTTPS:* Opens anywhere on 4G/5G mobile data or WiFi\n"
                    "• 🎚️ *Choose Quality:* 1080p Full HD, 720p HD, 480p, 360p, or MP3 Audio\n"
                    "• 📺 *Stream Directly:* Fast in-browser video player\n"
                    "• 📥 *Direct Download:* 1-tap download directly to your phone gallery\n"
                    "• 🚀 *Bypasses WhatsApp 65MB 'File Too Large' Limit!*"
                )
                self.send_reply(target_jid, card)

                # Optional: For small clips (< 90s), also attempt sending quick compressed preview in WhatsApp chat
                dur_sec = info.get("duration", 0)
                if dur_sec and dur_sec <= 90:
                    try:
                        vid_info = media_downloader.download_video(video_url)
                        if vid_info and vid_info.get("path") and os.path.exists(vid_info["path"]):
                            file_size_mb = os.path.getsize(vid_info["path"]) / (1024 * 1024)
                            if file_size_mb <= 25:  # Strict safe limit to prevent "file is large" error
                                file_path = vid_info["path"]
                                caption = (
                                    f"🎬 *{title}*\n\n"
                                    f"✨ HD 1080p & Audio Player: {watch_url}"
                                )
                                if self.client:
                                    self.client.send_video(target_jid, file_path, caption=caption)
                    except Exception as e:
                        logger.warning(f"Direct WhatsApp send skipped safely: {e}")
            else:
                fallback_card = (
                    "🎬 *Video Link Detected!*\n\n"
                    "🍿 *Cloud Watch & Download Portal (No WiFi Needed!):*\n"
                    f"👉 {watch_url}\n\n"
                    "Tap the link above to select quality (1080p, 720p, 480p, MP3) and watch or download directly on your phone!"
                )
                self.send_reply(target_jid, fallback_card)

        threading.Thread(target=task, daemon=True).start()

    def start_user_automation(self, sender_jid):
        """Start the recurring dynamic research for this specific user on their selected slot."""
        jid_str = jid_to_str(sender_jid)
        user = user_manager.get_or_create_user(jid_str)
        slot_num, slot_data = user_manager.get_selected_automation(jid_str)
        topic = slot_data.get("prompt", "").strip()
        interval = slot_data.get("interval_minutes", 5)

        if not topic:
            self.send_reply(
                jid_str,
                f"⚠️ *Automation #{slot_num} has no topic set yet!*\n\n"
                f"Please set what topic you want researched by sending:\n"
                f"👉 `/create {slot_num} <your topic>`\n"
                f"Example: `/create {slot_num} Latest AI models and tools`"
            )
            return

        other_slots = [str(x) for x in [1, 2, 3] if x != slot_num]
        user_manager.update_user(jid_str, is_active=True, last_run=time.time())
        topic_preview = (topic[:75] + "...") if len(topic) > 75 else topic

        self.send_reply(
            jid_str,
            f"🚀 *Automation #{slot_num} Started!* 🟢\n\n"
            f"🎯 *Topic:* \"{topic_preview}\"\n"
            f"⏱️ *Timer:* Every *{interval}* minute(s)\n"
            f"🔍 *Engine:* Live Google Search Grounding + Gemini AI\n"
            f"⏸️ *Other Automations:* #{other_slots[0]} and #{other_slots[1]} are stopped.\n\n"
            f"Researching your first update now... (Send */stop* anytime to pause)"
        )

        # Trigger first discovery immediately in background
        threading.Thread(target=self._send_user_update, args=(jid_str,), daemon=True).start()

    def stop_user_automation(self, sender_jid):
        """Stop recurring dynamic research for this specific user."""
        jid_str = jid_to_str(sender_jid)
        user = user_manager.get_or_create_user(jid_str)
        slot_num = int(user.get("selected_slot", 1))
        user_manager.update_user(jid_str, is_active=False)
        self.send_reply(
            jid_str,
            f"⏹️ *Automation #{slot_num} Stopped.* 🔴\n\n"
            f"Your research updates are now paused.\n"
            f"• Send */start* to resume Automation #{slot_num}\n"
            f"• Send */list* to view all 3 automations\n"
            f"• Send */1select*, */2select*, or */3select* to switch slots"
        )

    def _send_user_update(self, user_jid_str: str):
        """Perform research and dispatch to a specific user for their active slot."""
        clean_jid = jid_to_str(user_jid_str)
        try:
            res = discovery_engine.research_for_user(clean_jid)
            if res and res.get("message") and not res.get("skipped"):
                self.send_reply(clean_jid, res["message"])
                logger.info(f"Dispatched custom update to {clean_jid}")
        except Exception as e:
            logger.error(f"Error researching for user {clean_jid}: {e}")

    def _start_master_scheduler(self):
        """Master background thread that checks all active users and triggers their research according to their chosen intervals."""
        def scheduler_loop():
            logger.info("Multi-user master scheduler thread started.")
            while not self.scheduler_stop_event.is_set():
                time.sleep(10)  # Tick every 10 seconds
                try:
                    active_users = user_manager.get_all_active_users()
                    now = time.time()
                    for u in active_users:
                        jid = u.get("jid")
                        sel_slot = str(u.get("selected_slot", 1))
                        slot_data = u.get("automations", {}).get(sel_slot, {})
                        interval_sec = slot_data.get("interval_minutes", u.get("interval_minutes", 5)) * 60
                        last_run = slot_data.get("last_run", u.get("last_run", 0))

                        if now - last_run >= interval_sec:
                            # Update timestamp first to avoid multiple triggers
                            user_manager.update_user(jid, last_run=now)
                            threading.Thread(target=self._send_user_update, args=(jid,), daemon=True).start()
                except Exception as e:
                    logger.error(f"Scheduler loop error: {e}")

        self.scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True, name="MasterSchedulerThread")
        self.scheduler_thread.start()

bot_handler = BotHandler()
