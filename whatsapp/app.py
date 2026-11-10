import os
from flask import Flask, render_template, jsonify, request, send_file
from modules.config import config_manager, user_manager, logger, get_server_url
from modules.bot_handler import bot_handler
from modules.whatsapp_client import WhatsAppClient
from modules.downloader import media_downloader

app = Flask(__name__)
app.secret_key = "satyam_whatsapp_secret_key"

# Instantiate WhatsApp Client singleton
wa_client = WhatsAppClient(bot_handler)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/watch")
def watch_portal():
    """Web portal where users can select quality (1080p, 720p, 480p, 360p, MP3) and watch or download."""
    url = request.args.get("url", "").strip()
    return render_template("watch.html", initial_url=url, server_url=get_server_url())

@app.route("/api/video_info")
def api_video_info():
    """Extract and return video title, thumbnail, duration, author, and available resolutions."""
    url = request.args.get("url", "").strip()
    if not url:
        return jsonify({"success": False, "error": "Missing video URL"}), 400
    info = media_downloader.get_video_info(url)
    if not info:
        return jsonify({"success": False, "error": "Unable to extract video details. The link may be private or expired."}), 404
    return jsonify({"success": True, "data": info})

@app.route("/api/media_stream")
def api_media_stream():
    """Stream or download video in chosen resolution with HTTP Range support for instant seeking."""
    url = request.args.get("url", "").strip()
    quality = request.args.get("quality", "720p").strip()
    is_download = request.args.get("download", "0") == "1"

    if not url:
        return "Missing video URL", 400

    file_data = media_downloader.download_format(url, quality=quality)
    if not file_data or not file_data.get("path") or not os.path.exists(file_data["path"]):
        return "Failed to prepare video format. Please try another resolution.", 500

    file_path = file_data["path"]
    filename = file_data.get("filename", os.path.basename(file_path))
    content_type = file_data.get("content_type", "video/mp4")

    return send_file(
        file_path,
        mimetype=content_type,
        as_attachment=is_download,
        download_name=filename,
        conditional=True
    )

@app.route("/api/status")
def get_status():
    status = wa_client.get_status()
    all_users = list(user_manager.users.values())
    active_users = user_manager.get_all_active_users()

    from modules.tunnel import tunnel_manager
    status["users_count"] = len(all_users)
    status["active_users_count"] = len(active_users)
    status["users"] = all_users
    status["server_url"] = get_server_url()
    status["tunnel_url"] = tunnel_manager.tunnel_url if tunnel_manager.is_running else None
    status["tunnel_active"] = tunnel_manager.is_running
    status["config"] = {
        "bot_password": config_manager.get("bot_password", "satyam08052010"),
        "interval_minutes": config_manager.get("interval_minutes", 5),
        "gemini_api_key_set": bool(config_manager.get("gemini_api_key", "").strip()),
        "gemini_model": config_manager.get("gemini_model", "gemini-3.8-flash"),
        "video_retention_hours": config_manager.get("video_retention_hours", 24),
        "public_url": config_manager.get("public_url", "")
    }
    return jsonify(status)

@app.route("/api/tunnel_action", methods=["POST"])
def tunnel_action():
    from modules.tunnel import tunnel_manager
    data = request.json or {}
    action = data.get("action", "start")
    port = config_manager.get("port", 5000)

    if action == "start" or action == "restart":
        tunnel_manager.stop_tunnel()
        new_url = tunnel_manager.start_tunnel(port=port, wait_seconds=15)
        return jsonify({"success": bool(new_url), "tunnel_url": new_url})
    elif action == "stop":
        tunnel_manager.stop_tunnel()
        return jsonify({"success": True, "tunnel_url": None})
    return jsonify({"success": False, "error": "Unknown action"}), 400

@app.route("/api/user_action", methods=["POST"])
def user_action():
    data = request.json or {}
    jid = data.get("jid")
    action = data.get("action")

    if not jid or not action:
        return jsonify({"success": False, "error": "Missing jid or action"}), 400

    if action == "start":
        bot_handler.start_user_automation(jid)
        return jsonify({"success": True, "message": f"Started automation for {jid}"})
    elif action == "stop":
        bot_handler.stop_user_automation(jid)
        return jsonify({"success": True, "message": f"Stopped automation for {jid}"})
    elif action == "trigger_now":
        bot_handler._send_user_update(jid)
        return jsonify({"success": True, "message": f"Triggered update now for {jid}"})
    elif action == "select_slot":
        slot_num = int(data.get("slot", 1))
        bot_handler.handle_slot_selection(jid, slot_num)
        return jsonify({"success": True, "message": f"Selected slot #{slot_num} for {jid}"})
    elif action == "delete_slot":
        slot_num = int(data.get("slot", 1))
        bot_handler.handle_slot_deletion(jid, slot_num)
        return jsonify({"success": True, "message": f"Deleted slot #{slot_num} for {jid}"})
    elif action == "set_interval":
        interval = data.get("interval", 1)
        try:
            val = max(1, int(interval))
            user_manager.set_slot_interval(jid, val)
            return jsonify({"success": True, "message": f"Updated timer to {val} min for {jid}"})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 400

    return jsonify({"success": False, "error": "Invalid action"}), 400

@app.route("/api/update_settings", methods=["POST"])
def update_settings():
    data = request.json or {}
    updates = {}
    if "gemini_api_key" in data and data["gemini_api_key"].strip():
        updates["gemini_api_key"] = data["gemini_api_key"].strip()
    if "bot_password" in data and data["bot_password"].strip():
        updates["bot_password"] = data["bot_password"].strip()
    if "public_url" in data:
        updates["public_url"] = data["public_url"].strip()
    if "interval_minutes" in data:
        try:
            updates["interval_minutes"] = max(1, int(data["interval_minutes"]))
        except Exception:
            pass

    if updates:
        config_manager.update(updates)
        return jsonify({"success": True, "message": "Admin settings saved successfully", "updates": list(updates.keys())})
    return jsonify({"success": False, "message": "No valid settings provided"}), 400

@app.route("/api/cleanup_storage", methods=["POST"])
def cleanup_storage():
    media_downloader.cleanup_old_videos()
    return jsonify({"success": True, "message": "Video storage cleanup completed"})

def start_bot_client():
    wa_client.start()

if __name__ == "__main__":
    start_bot_client()
    port = config_manager.get("port", 5000)
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
