import io
import time
import base64
import logging
import threading
from typing import Optional, Dict, Any

import segno
from neonize.client import NewClient
from neonize.events import (
    ConnectedEv,
    DisconnectedEv,
    LoggedOutEv,
    MessageEv,
    PairStatusEv
)
from neonize.proto.Neonize_pb2 import JID
from modules.config import DATA_DIR, logger, config_manager, jid_to_str, str_to_jid

class WhatsAppClient:
    def __init__(self, bot_handler, session_name: str = "satyam_whatsapp_session"):
        self.bot_handler = bot_handler
        self.session_path = str(DATA_DIR / session_name)
        self.client: Optional[NewClient] = None
        self.is_connected = False
        self.is_pairing = False
        self.qr_code_data = ""
        self.qr_code_data_url = ""
        self.qr_timestamp = 0
        self.pairing_code = ""
        self.connection_error = ""
        self.phone_number = ""
        self.push_name = ""
        self.connected_jid = ""
        self.worker_thread: Optional[threading.Thread] = None

    def get_status(self) -> Dict[str, Any]:
        """Return status for the web dashboard."""
        return {
            "connected": self.is_connected,
            "pairing": self.is_pairing,
            "qr_data_url": self.qr_code_data_url,
            "qr_timestamp": self.qr_timestamp,
            "pairing_code": self.pairing_code,
            "connection_error": self.connection_error,
            "worker_alive": bool(self.worker_thread and self.worker_thread.is_alive()),
            "phone_number": self.phone_number,
            "push_name": self.push_name,
            "connected_jid": self.connected_jid,
            "automation_active": config_manager.get("is_automation_active", False),
            "interval_minutes": config_manager.get("interval_minutes", 5),
            "discovery_counter": config_manager.get("discovery_counter", 0),
            "active_chat": config_manager.get("active_chat_jid", "")
        }

    def _setup_events(self):
        """Register Neonize event listeners."""
        @self.client.event.qr
        def on_qr(client: NewClient, data_qr: bytes):
            try:
                qr_str = data_qr.decode("utf-8", errors="ignore")
                self.qr_code_data = qr_str
                self.qr_timestamp = time.time()
                self.is_pairing = True
                self.is_connected = False

                # Convert to PNG Data URL for browser display
                qr_img = segno.make_qr(data_qr)
                buff = io.BytesIO()
                qr_img.save(buff, kind="png", scale=8, border=2)
                b64_str = base64.b64encode(buff.getvalue()).decode("utf-8")
                self.qr_code_data_url = f"data:image/png;base64,{b64_str}"

                logger.info("New WhatsApp Web QR code generated! Scan on http://localhost:5000")
                # Also print to terminal for immediate visibility
                qr_img.terminal(compact=True)
            except Exception as e:
                logger.error(f"Error processing QR event: {e}")

        @self.client.event(ConnectedEv)
        def on_connected(client: NewClient, ev: ConnectedEv):
            self.is_connected = True
            self.is_pairing = False
            self.qr_code_data_url = ""
            try:
                if client.me:
                    self.connected_jid = client.me.JID.User if hasattr(client.me, 'JID') else str(client.me)
                    self.phone_number = getattr(client.me.JID, 'User', '') if hasattr(client.me, 'JID') else ''
                    self.push_name = getattr(client.me, 'PushName', '')
            except Exception as e:
                logger.debug(f"Extracting user info on connect: {e}")

            logger.info(f"✅ WhatsApp client successfully connected as {self.phone_number or self.connected_jid}!")
            self.bot_handler.register_client_route(self.connected_jid, self)

        @self.client.event(PairStatusEv)
        def on_pair_status(client: NewClient, ev: PairStatusEv):
            logger.info(f"Pairing status update: ID={ev.ID}")

        @self.client.event(LoggedOutEv)
        def on_logged_out(client: NewClient, ev: LoggedOutEv):
            self.is_connected = False
            self.is_pairing = False
            logger.warning("WhatsApp client logged out. Scan QR again to re-link.")

        @self.client.event(DisconnectedEv)
        def on_disconnected(client: NewClient, ev: DisconnectedEv):
            self.is_connected = False
            logger.warning("WhatsApp client disconnected from server.")

        @self.client.event(MessageEv)
        def on_message(client: NewClient, message: MessageEv):
            try:
                # Ignore messages sent by self
                if message.Info.MessageSource.IsFromMe:
                    return

                chat_jid = message.Info.MessageSource.Chat
                self.bot_handler.register_client_route(chat_jid, self)
                msg_proto = message.Message

                # 1. Text Message (conversation or extendedTextMessage)
                text = ""
                if msg_proto.HasField("conversation") and msg_proto.conversation:
                    text = msg_proto.conversation
                elif msg_proto.HasField("extendedTextMessage") and msg_proto.extendedTextMessage.text:
                    text = msg_proto.extendedTextMessage.text

                # 2. Image Message (photo received)
                if msg_proto.HasField("imageMessage"):
                    caption = msg_proto.imageMessage.caption or ""
                    try:
                        img_bytes = client.download_any(msg_proto)
                        if img_bytes:
                            self.bot_handler.handle_incoming_image(chat_jid, img_bytes, caption)
                            return
                    except Exception as err:
                        logger.error(f"Failed to download image message: {err}")

                # Process text message
                if text:
                    self.bot_handler.handle_incoming_text(chat_jid, text)

            except Exception as e:
                logger.error(f"Error handling incoming message: {e}")

    def send_text(self, to_jid: JID | str, message: str):
        """Send plain text message to a user/chat JID."""
        if not self.client:
            raise RuntimeError("WhatsApp Client not initialized")
        target_jid = str_to_jid(to_jid)
        return self.client.send_message(target_jid, message)

    def send_video(self, to_jid: JID | str, file_path: str, caption: Optional[str] = None):
        """Send video file to a user/chat JID."""
        if not self.client:
            raise RuntimeError("WhatsApp Client not initialized")
        target_jid = str_to_jid(to_jid)
        return self.client.send_video(target_jid, file_path, caption=caption)

    def send_image(self, to_jid: JID | str, file_path_or_bytes: str | bytes, caption: Optional[str] = None):
        """Send image file to a user/chat JID."""
        if not self.client:
            raise RuntimeError("WhatsApp Client not initialized")
        target_jid = str_to_jid(to_jid)
        return self.client.send_image(target_jid, file_path_or_bytes, caption=caption)

    def start(self, phone_number: str = "", new_device: bool = False):
        """Start the Neonize client in a dedicated daemon thread."""
        if self.worker_thread and self.worker_thread.is_alive():
            return False
        self.connection_error = ""
        self.pairing_code = ""
        self.is_connected = False
        self.is_pairing = False
        self.qr_code_data = ""
        self.qr_code_data_url = ""
        self.phone_number = ""
        self.push_name = ""
        self.connected_jid = ""

        def run():
            logger.info("Initializing Neonize client...")
            self.client = NewClient(self.session_path, new_device=new_device)
            self._setup_events()
            self.bot_handler.set_client(self)
            try:
                if phone_number:
                    from neonize.utils.enum import ClientName
                    self.pairing_code = self.client.PairPhone(
                        phone_number,
                        show_push_notification=True,
                        client_name=ClientName.LINUX,
                    )
                    self.is_pairing = True
                    logger.info("WhatsApp phone-number pairing code generated.")
                self.client.connect()
            except Exception as e:
                self.connection_error = f"{type(e).__name__}: {e}"
                logger.error(f"Client connection error: {e}")

        self.worker_thread = threading.Thread(target=run, daemon=True, name="NeonizeClientThread")
        self.worker_thread.start()
        return True
