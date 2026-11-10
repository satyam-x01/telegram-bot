# 🤖 Satyam WhatsApp Automation • Multi-User Dynamic Research Engine (24/7)

A 24/7 Python WhatsApp Automation Bot with a **Localhost Web Dashboard & QR Code Generator**, where **each user sets their own custom topic/prompt and custom timer directly from WhatsApp**. The bot conducts **fresh live web research** specifically on what that user requested (e.g. *"Today's news"*, *"Latest AI tools"*, *"Crypto updates"*, *"Android apps"*), completely avoiding pre-selected or hardcoded messages.

---

## 🌟 Key Features

1. **🎯 100% Dynamic Topic per User (No Hardcoded Categories)**:
   - Koi bhi user apna topic khud type kar sakta hai (jaise: *"I want today news"*, *"Latest AI models"*, *"Tech headlines"*, etc.).
   - Bot internet par **live search & research** karke fresh information bhejta hai.
   - Har user ki sent history alag track hoti hai taaki us user ko duplicate updates na milein.

2. **⏱️ User Sets Their Own Timer (No Forced Default)**:
   - Koi fixed default interval force nahi kiya gaya hai.
   - User khud decide karta hai ki use kitne minute me message chahiye (jaise `5`, `10`, `15`, `30`, ya `60` minutes).
   - User apna timer kabhi bhi WhatsApp se change kar sakta hai: `timer <minutes>`.

3. **📱 Localhost QR Code & Device Link (`http://localhost:5000`)**:
   - Web dashboard par live auto-refreshing QR Code generate hota hai.
   - WhatsApp me **Linked Devices > Link a Device** karke scan kijiye.
   - Session 24/7 active rehta hai.

4. **🔒 Master Password Security (`satyam08052010`)**:
   - Jab koi bhi user **`hillo`** bhejega, bot English me password mangega.
   - Password verify hone ke baad hi user apna custom topic aur timer set kar sakta hai.
   - Bot password kisi ko reveal nahi karta.

5. **🔄 Dynamic On-the-Fly Commands**:
   - **`start`** - User ke liye unka custom research start karta hai.
   - **`stop`** - Updates ko pause/stop karta hai.
   - **`topic <naya topic>`** - Apna topic kabhi bhi badal sakte hain (jaise: `topic cricket scores` ya `topic trending AI tools`).
   - **`timer <minutes>`** - Apna interval kabhi bhi badal sakte hain (jaise: `timer 10`).
   - **`help`** - User guide aur commands ki jankari deta hai.

6. **🎬 YouTube & Instagram Video Downloader**:
   - Koi bhi YouTube (Videos/Shorts) ya Instagram (Reels/Posts) link bhejte hi bot video download karke WhatsApp par bhejta hai.
   - **🧹 24-Hour Auto-Storage Cleaner**: PC/Server disk bhar na jaye, isliye downloaded videos 24 ghante baad bot ke server se auto-delete ho jate hain. User ke WhatsApp me video surakshit rehti hai!

7. **📸 Photo Analysis (No Generation)**:
   - User photo bhejega to Google Gemini Vision se photo ka detailed analysis karega. (Photo generate nahi karega).

8. **👑 Creator Attribution**:
   - *"Yeh bot kisne banaya?"* ya *"Who created this bot?"* puchne par user ki bhasha me javab dega: **Satyam Developer**.

---

## 🚀 Quick Start Guide

### 1. Run the Bot
```bash
python run.py
```

### 2. Connect WhatsApp
1. Open browser at:
   ```
   http://localhost:5000
   ```
2. Scan the QR code using your WhatsApp (**Linked Devices > Link a Device**).

### 3. WhatsApp Conversation Walkthrough
1. Send:
   ```text
   hillo
   ```
2. Enter password:
   ```text
   satyam08052010
   ```
3. Type what topic you want researched:
   ```text
   I want today news
   ```
4. Enter your custom interval in minutes:
   ```text
   10
   ```
5. Send:
   ```text
   start
   ```
   The bot will immediately research your topic live and send updates every 10 minutes!

---

## 🛠️ Summary of User Commands

| Command | Action |
|---|---|
| `hillo` | Starts access & prompts for password |
| `satyam08052010` | Verifies access |
| `<your topic>` | Sets what you want researched (during setup) |
| `<minutes>` | Sets your update interval (during setup) |
| `start` | Begins your recurring live research updates |
| `stop` | Pauses your recurring updates |
| `topic <new topic>` | Changes your research topic anytime |
| `timer <minutes>` | Changes your interval minutes anytime |
| `help` | Shows your current topic, timer, and commands |
| *YouTube / Instagram Link* | Downloads video to chat (purges server in 24h) |
| *Send Photo* | Detailed visual analysis via Gemini Vision |
| *Ask any question* | Mid-automation AI answers & web search |
