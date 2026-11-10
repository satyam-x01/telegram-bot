import logging
import asyncio
from typing import Dict, Optional, Any
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    PhoneCodeExpiredError,
    PasswordHashInvalidError,
    PhoneNumberInvalidError,
    ApiIdInvalidError
)
from telethon.tl.functions.channels import (
    CreateChannelRequest,
    EditAdminRequest,
    InviteToChannelRequest,
    DeleteChannelRequest
)
from telethon.tl.functions.messages import ExportChatInviteRequest
from telethon.tl.types import ChatAdminRights

import config
from database import db

logger = logging.getLogger(__name__)

class TelegramStorageService:
    def __init__(self):
        self.api_id = config.TELEGRAM_API_ID
        self.api_hash = config.TELEGRAM_API_HASH
        # Temporary in-memory cache for ongoing login flows: user_id -> dict
        self._pending_logins: Dict[int, Dict[str, Any]] = {}

    def update_api_credentials(self, api_id: int, api_hash: str):
        """Updates and persists custom Telegram API_ID and API_HASH."""
        self.api_id = int(api_id)
        self.api_hash = str(api_hash).strip()
        config.TELEGRAM_API_ID = self.api_id
        config.TELEGRAM_API_HASH = self.api_hash

        # 1. Save to .bot_credentials.json
        import json
        from pathlib import Path
        cred_path = Path(__file__).parent.parent / ".bot_credentials.json"
        creds = {}
        if cred_path.exists():
            try:
                with open(cred_path, "r", encoding="utf-8") as f:
                    creds = json.load(f)
            except Exception:
                creds = {}
        creds["api_id"] = self.api_id
        creds["api_hash"] = self.api_hash
        try:
            with open(cred_path, "w", encoding="utf-8") as f:
                json.dump(creds, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to write .bot_credentials.json: {e}")

        # 2. Update .env file
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            try:
                content = env_path.read_text(encoding="utf-8")
                lines = content.splitlines()
                new_lines = []
                has_id = False
                has_hash = False
                for line in lines:
                    if line.startswith("TELEGRAM_API_ID="):
                        new_lines.append(f"TELEGRAM_API_ID={self.api_id}")
                        has_id = True
                    elif line.startswith("TELEGRAM_API_HASH="):
                        new_lines.append(f"TELEGRAM_API_HASH={self.api_hash}")
                        has_hash = True
                    else:
                        new_lines.append(line)
                if not has_id:
                    new_lines.append(f"TELEGRAM_API_ID={self.api_id}")
                if not has_hash:
                    new_lines.append(f"TELEGRAM_API_HASH={self.api_hash}")
                env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
            except Exception as e:
                logger.warning(f"Failed to update .env: {e}")

    def get_pending_login(self, user_id: int) -> Optional[Dict[str, Any]]:
        return self._pending_logins.get(user_id)

    def clear_pending_login(self, user_id: int):
        login_data = self._pending_logins.pop(user_id, None)
        if login_data and "client" in login_data:
            client: TelegramClient = login_data["client"]
            if client.is_connected():
                try:
                    asyncio.create_task(client.disconnect())
                except Exception:
                    pass

    async def send_login_code(self, user_id: int, phone_number: str) -> Dict[str, Any]:
        """Initiates Telegram MTProto login and sends OTP to the user's Telegram app."""
        # Clean existing pending login if any
        self.clear_pending_login(user_id)

        clean_phone = phone_number.strip().replace(" ", "").replace("-", "")
        if not clean_phone.startswith("+"):
            clean_phone = f"+{clean_phone}"

        client = TelegramClient(StringSession(), self.api_id, self.api_hash)
        try:
            await client.connect()
            sent_code = await client.send_code_request(clean_phone)
            self._pending_logins[user_id] = {
                "client": client,
                "phone": clean_phone,
                "phone_code_hash": sent_code.phone_code_hash
            }
            return {
                "success": True,
                "phone": clean_phone,
                "phone_code_hash": sent_code.phone_code_hash
            }
        except PhoneNumberInvalidError:
            if client.is_connected():
                await client.disconnect()
            return {"success": False, "error": "invalid_phone", "message": "Phone number is invalid. Please use international format (e.g. `+919876543210`)."}
        except ApiIdInvalidError:
            if client.is_connected():
                await client.disconnect()
            return {"success": False, "error": "invalid_api_id", "message": "The api_id/api_hash combination is invalid."}
        except Exception as e:
            logger.error(f"Error sending login code to {clean_phone}: {e}")
            if client.is_connected():
                await client.disconnect()
            if "api_id" in str(e).lower() or "api_hash" in str(e).lower():
                return {"success": False, "error": "invalid_api_id", "message": str(e)}
            return {"success": False, "error": "unknown", "message": str(e)}

    async def verify_login_code(self, user_id: int, code: str) -> Dict[str, Any]:
        """Verifies the OTP code sent to user."""
        pending = self._pending_logins.get(user_id)
        if not pending:
            return {
                "success": False,
                "error": "no_pending_login",
                "message": "Login session expire ho gaya hai (bot restart hua tha). Kripya /storage bhejiye aur phone number dubara enter karein."
            }

        client: TelegramClient = pending["client"]
        phone = pending["phone"]
        phone_code_hash = pending["phone_code_hash"]
        
        # Cleanly extract all digits (supports spaces like '1 2 3 4 5', dashes, or keypad)
        clean_code = "".join(filter(str.isdigit, str(code)))

        if not clean_code:
            return {"success": False, "error": "invalid_format", "message": "OTP sirf numbers me hona chahiye (e.g. `12345`)."}

        try:
            if not client.is_connected():
                await client.connect()
            user = await client.sign_in(phone=phone, code=clean_code, phone_code_hash=phone_code_hash)
            session_str = client.session.save()
            db.save_user_telegram_session(user_id, phone, session_str, is_connected=1)
            
            # Clean up pending
            self._pending_logins.pop(user_id, None)
            if client.is_connected():
                await client.disconnect()

            first_name = getattr(user, "first_name", "") or "Telegram User"
            return {
                "success": True,
                "status": "connected",
                "first_name": first_name,
                "phone": phone
            }
        except SessionPasswordNeededError:
            # 2FA Password is required
            return {
                "success": True,
                "status": "2fa_required",
                "message": "Two-step verification (2FA) is enabled on your account."
            }
        except PhoneCodeInvalidError:
            return {"success": False, "error": "invalid_code", "message": "The OTP code you entered is invalid. Please check and try again."}
        except PhoneCodeExpiredError:
            self.clear_pending_login(user_id)
            return {"success": False, "error": "code_expired", "message": "The OTP code has expired. Please request a new one by typing /storage."}
        except Exception as e:
            logger.error(f"Error verifying login code for user {user_id}: {e}")
            return {"success": False, "error": "verification_failed", "message": str(e)}

    async def verify_2fa_password(self, user_id: int, password: str) -> Dict[str, Any]:
        """Signs in with 2FA password if account has two-step verification enabled."""
        pending = self._pending_logins.get(user_id)
        if not pending:
            return {"success": False, "error": "no_pending_login", "message": "No login session found. Please start again."}

        client: TelegramClient = pending["client"]
        phone = pending["phone"]

        try:
            if not client.is_connected():
                await client.connect()
            user = await client.sign_in(password=password.strip())
            session_str = client.session.save()
            db.save_user_telegram_session(user_id, phone, session_str, is_connected=1)

            # Clean up pending
            self._pending_logins.pop(user_id, None)
            if client.is_connected():
                await client.disconnect()

            first_name = getattr(user, "first_name", "") or "Telegram User"
            return {
                "success": True,
                "status": "connected",
                "first_name": first_name,
                "phone": phone
            }
        except PasswordHashInvalidError:
            return {"success": False, "error": "invalid_password", "message": "Incorrect 2FA password. Please try again."}
        except Exception as e:
            logger.error(f"Error verifying 2FA password for user {user_id}: {e}")
            return {"success": False, "error": "2fa_failed", "message": str(e)}

    def is_user_connected(self, user_id: int) -> bool:
        session = db.get_user_telegram_session(user_id)
        return bool(session and session.get("is_connected") and session.get("session_string"))

    def get_connected_phone(self, user_id: int) -> str:
        session = db.get_user_telegram_session(user_id)
        return session.get("phone_number", "") if session else ""

    async def disconnect_user(self, user_id: int) -> bool:
        """Disconnects and removes the user's MTProto session from database."""
        self.clear_pending_login(user_id)
        session = db.get_user_telegram_session(user_id)
        if session and session.get("session_string"):
            try:
                client = TelegramClient(StringSession(session["session_string"]), self.api_id, self.api_hash)
                await client.connect()
                if await client.is_user_authorized():
                    await client.log_out()
                await client.disconnect()
            except Exception as e:
                logger.warning(f"Error logging out user client {user_id}: {e}")
        db.delete_user_telegram_session(user_id)
        return True

    async def get_authorized_client(self, user_id: int) -> Optional[TelegramClient]:
        session = db.get_user_telegram_session(user_id)
        if not session or not session.get("session_string"):
            return None
        client = TelegramClient(StringSession(session["session_string"]), self.api_id, self.api_hash)
        try:
            await client.connect()
            if await client.is_user_authorized():
                return client
            else:
                await client.disconnect()
                return None
        except Exception as e:
            logger.error(f"Failed to initialize client for user {user_id}: {e}")
            return None

    async def create_private_group(self, user_id: int, group_name: str, bot_username: str = "") -> Dict[str, Any]:
        """Creates a private supergroup/megagroup on user's Telegram account, adds bot as admin, and generates invite link."""
        client = await self.get_authorized_client(user_id)
        if not client:
            return {"success": False, "error": "not_authorized", "message": "Telegram account is not connected or session expired."}

        try:
            # 1. Create Megagroup (Supergroup)
            res = await client(CreateChannelRequest(
                title=group_name.strip(),
                about="🔒 Private Cloud Storage Vault created via Bot",
                megagroup=True
            ))
            channel = res.chats[0]
            raw_id = channel.id
            telegram_chat_id = int(f"-100{raw_id}")

            # 2. Export invite link
            invite_link = ""
            try:
                invite_res = await client(ExportChatInviteRequest(peer=channel))
                invite_link = getattr(invite_res, "link", "") or ""
            except Exception as e:
                logger.warning(f"Could not export invite link: {e}")

            # 3. Add bot as administrator so bot can directly send messages & media
            bot_clean = (bot_username or getattr(config, "BOT_USERNAME", "")).replace("@", "").strip()
            if bot_clean and bot_clean != "MusicBot":
                try:
                    bot_entity = await client.get_entity(bot_clean)
                    await client(InviteToChannelRequest(channel=channel, users=[bot_entity]))
                    admin_rights = ChatAdminRights(
                        change_info=True,
                        post_messages=True,
                        edit_messages=True,
                        delete_messages=True,
                        ban_users=True,
                        invite_users=True,
                        pin_messages=True,
                        add_admins=False,
                        manage_call=True
                    )
                    await client(EditAdminRequest(
                        channel=channel,
                        user_id=bot_entity,
                        admin_rights=admin_rights,
                        rank="Cloud Storage Bot"
                    ))
                except Exception as e:
                    logger.warning(f"Could not invite/promote bot in created group: {e}")

            # 4. Save to Database
            group_id = db.add_cloud_group(user_id, group_name.strip(), telegram_chat_id, invite_link)

            await client.disconnect()
            return {
                "success": True,
                "group_id": group_id,
                "group_name": group_name.strip(),
                "telegram_chat_id": telegram_chat_id,
                "invite_link": invite_link
            }
        except Exception as e:
            logger.error(f"Error creating private group for user {user_id}: {e}")
            if client.is_connected():
                await client.disconnect()
            return {"success": False, "error": "creation_failed", "message": str(e)}

    async def delete_group(self, user_id: int, group_id: int) -> Dict[str, Any]:
        """Deletes the group on Telegram via user's client and removes it from database."""
        group = db.get_cloud_group_by_id(group_id, user_id)
        if not group:
            return {"success": False, "error": "not_found", "message": "Group not found."}

        client = await self.get_authorized_client(user_id)
        if client:
            try:
                raw_chat_id = group["telegram_chat_id"]
                # Convert -100xxx to positive entity id for Telethon
                clean_id_str = str(abs(raw_chat_id))
                if clean_id_str.startswith("100"):
                    clean_id = int(clean_id_str[3:])
                else:
                    clean_id = int(clean_id_str)

                channel_entity = await client.get_entity(clean_id)
                await client(DeleteChannelRequest(channel=channel_entity))
            except Exception as e:
                logger.warning(f"Could not delete group {group_id} via Telethon: {e}")
            finally:
                if client.is_connected():
                    await client.disconnect()

        db.delete_cloud_group(group_id, user_id)
        return {"success": True, "group_name": group["group_name"]}

    async def forward_or_send_media_to_group(
        self,
        bot_context,
        user_id: int,
        group_chat_id: int,
        message
    ) -> Dict[str, Any]:
        """Sends or forwards user-provided text, photo, video, or document to the private group."""
        try:
            # First attempt: Try sending via bot directly
            # If message is photo
            if message.photo:
                photo_file_id = message.photo[-1].file_id
                caption = message.caption or "🖼️ Cloud Storage Photo"
                sent = await bot_context.bot.send_photo(chat_id=group_chat_id, photo=photo_file_id, caption=caption)
                return {"success": True, "type": "photo", "message_id": sent.message_id}
            # If video
            elif message.video:
                video_file_id = message.video.file_id
                caption = message.caption or "🎥 Cloud Storage Video"
                sent = await bot_context.bot.send_video(chat_id=group_chat_id, video=video_file_id, caption=caption)
                return {"success": True, "type": "video", "message_id": sent.message_id}
            # If document
            elif message.document:
                doc_file_id = message.document.file_id
                caption = message.caption or f"📁 {message.document.file_name or 'Document'}"
                sent = await bot_context.bot.send_document(chat_id=group_chat_id, document=doc_file_id, caption=caption)
                return {"success": True, "type": "document", "message_id": sent.message_id}
            # If audio
            elif message.audio:
                audio_file_id = message.audio.file_id
                caption = message.caption or f"🎵 {message.audio.title or 'Audio'}"
                sent = await bot_context.bot.send_audio(chat_id=group_chat_id, audio=audio_file_id, caption=caption)
                return {"success": True, "type": "audio", "message_id": sent.message_id}
            # If voice
            elif message.voice:
                voice_file_id = message.voice.file_id
                sent = await bot_context.bot.send_voice(chat_id=group_chat_id, voice=voice_file_id)
                return {"success": True, "type": "voice", "message_id": sent.message_id}
            # If text
            elif message.text:
                sent = await bot_context.bot.send_message(
                    chat_id=group_chat_id,
                    text=f"📝 *Cloud Note:*\n\n{message.text}",
                    parse_mode="Markdown"
                )
                return {"success": True, "type": "text", "message_id": sent.message_id}
            else:
                # Forward generic message
                sent = await bot_context.bot.forward_message(
                    chat_id=group_chat_id,
                    from_chat_id=message.chat_id,
                    message_id=message.message_id
                )
                return {"success": True, "type": "forward", "message_id": sent.message_id}

        except Exception as e:
            logger.warning(f"Direct bot send to group {group_chat_id} failed: {e}. Trying Telethon client fallback...")
            # Fallback: send via user's Telethon client
            client = await self.get_authorized_client(user_id)
            if not client:
                return {"success": False, "error": str(e)}

            try:
                clean_id_str = str(abs(group_chat_id))
                if clean_id_str.startswith("100"):
                    clean_id = int(clean_id_str[3:])
                else:
                    clean_id = int(clean_id_str)
                entity = await client.get_entity(clean_id)

                if message.text:
                    await client.send_message(entity, f"📝 Cloud Note:\n\n{message.text}")
                    return {"success": True, "type": "text"}
                else:
                    # Download file from Telegram bot and upload via Telethon
                    file_obj = None
                    if message.photo:
                        file_obj = await message.photo[-1].get_file()
                    elif message.video:
                        file_obj = await message.video.get_file()
                    elif message.document:
                        file_obj = await message.document.get_file()
                    elif message.audio:
                        file_obj = await message.audio.get_file()

                    if file_obj:
                        import tempfile
                        import os
                        with tempfile.NamedTemporaryFile(delete=False) as tmp:
                            tmp_path = tmp.name
                        await file_obj.download_to_drive(custom_path=tmp_path)
                        caption = message.caption or "Cloud Storage Media"
                        await client.send_file(entity, tmp_path, caption=caption)
                        try:
                            os.remove(tmp_path)
                        except Exception:
                            pass
                        return {"success": True, "type": "media"}

                return {"success": False, "error": "unsupported_type"}
            except Exception as ex:
                logger.error(f"Telethon fallback upload failed: {ex}")
                return {"success": False, "error": str(ex)}
            finally:
                if client.is_connected():
                    await client.disconnect()

storage_service = TelegramStorageService()
