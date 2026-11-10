import io
import re
import math
import json
import random
import asyncio
import urllib.request
import urllib.parse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from services.study_data import (
    EXAMS_CATALOG,
    CLASSES_CATALOG,
    BOARDS_CATALOG,
    CURRICULUM_DATA,
    get_all_exams,
    get_exam_details,
    get_classes,
    get_boards_for_class,
    get_subjects,
    get_chapters
)
from services.ai_service import ai_service

# Short code mapping to guarantee callback_data is well under Telegram's 64-byte limit
CLASS_CODE_MAP = {
    "class_10": "c10",
    "class_12": "c12",
    "class_11": "c11",
    "class_9": "c9",
    "class_8": "c8"
}
CODE_TO_CLASS = {v: k for k, v in CLASS_CODE_MAP.items()}

BOARD_CODE_MAP = {
    "msbshse": "ms",
    "cbse": "cb",
    "icse": "ic",
    "upmsp": "up",
    "bseb": "br",
    "rbse": "rj",
    "mpbse": "mp",
    "gseb": "gj",
    "wbbse": "wb",
    "kseab": "ka",
    "tndge": "tn",
    "apbse": "ap",
    "tsbie": "ts",
    "kbpe": "kl",
    "pseb": "pb",
    "bseh": "hr",
    "chse_od": "od",
    "jac": "jh",
    "cgbse": "cg",
    "seba": "as",
    "nios": "ni"
}
CODE_TO_BOARD = {v: k for k, v in BOARD_CODE_MAP.items()}

SUBJ_CODE_MAP = {
    "english": "eng",
    "science_1": "sc1",
    "science_2": "sc2",
    "maths_1": "m1",
    "maths_2": "m2",
    "history": "his",
    "geography": "geo",
    "marathi": "mar",
    "physics": "phy",
    "chemistry": "chem",
    "mathematics": "mat",
    "biology": "bio",
    "science": "sci",
    "social_science": "ssc"
}
CODE_TO_SUBJ = {v: k for k, v in SUBJ_CODE_MAP.items()}

ITEMS_PER_PAGE = 5


async def study_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point for /study command - Comprehensive AI Study Mode."""
    msg = update.effective_message

    text = (
        "📚 *24/7 AI STUDY & EXAM MENTOR HUB* 🎓\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Welcome to your ultimate academic companion! Master your board exams and crack competitive entrance tests with AI-powered study tools.\n\n"
        "🎯 *What would you like to explore today?*\n\n"
        "• 🏆 *Competitive & Entrance Exams*\n"
        "  _JEE Mains, JEE Advanced, NEET, MHT-CET, UPSC, NDA, GATE, CUET_\n"
        "  _Formula Cheatsheets, Subject Notes, Past Year Questions & Top Apps/Websites_\n\n"
        "• 🏫 *School & College Board Curriculum*\n"
        "  _Class 10 (SSC), Class 12 (HSC), CBSE & ICSE_\n"
        "  _Authentic textbook chapters with ⬅️ ➡️ pagination_\n"
        "  _Complete Chapter Notes, Textbook Exercise Solutions & Important Qs_\n\n"
        "• 🔍 *AI Educational Research*\n"
        "  _Ask any doubt, find best free websites, apps, and video lectures!_\n\n"
        "✨ _Choose an option below to start studying!_"
    )

    keyboard = [
        [
            InlineKeyboardButton("🎯 Competitive Exams", callback_data="st_ex"),
            InlineKeyboardButton("🏫 Classes & Boards", callback_data="st_cl")
        ],
        [
            InlineKeyboardButton("🔍 Research Best Study Apps & Sites", callback_data="st_ea_jee_mains_research"),
            InlineKeyboardButton("❓ Ask Study Doubt", switch_inline_query_current_chat="/search ")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await msg.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)


async def show_study_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main menu dispatcher."""
    query = update.callback_query
    await query.answer()

    text = (
        "📚 *24/7 AI STUDY & EXAM MENTOR HUB* 🎓\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Select your study path:\n\n"
        "• 🎯 *Competitive & Entrance Exams* (JEE, NEET, MHT-CET, UPSC, etc.)\n"
        "• 🏫 *Classes & Boards* (Class 10, 12, Maharashtra Board, CBSE, etc.)"
    )
    keyboard = [
        [
            InlineKeyboardButton("🎯 Competitive Exams", callback_data="st_ex"),
            InlineKeyboardButton("🏫 Classes & Boards", callback_data="st_cl")
        ],
        [
            InlineKeyboardButton("🔍 Research Best Study Apps & Sites", callback_data="st_ea_jee_mains_research")
        ]
    ]
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))


async def show_exams_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show competitive exams selection menu."""
    query = update.callback_query
    await query.answer()

    exams = get_all_exams()
    text = (
        "🎯 *COMPETITIVE & ENTRANCE EXAMS HUB* 🏆\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Select any national or state-level exam below to access:\n"
        "• ⚡ *Formula Cheatsheets & Mindmaps*\n"
        "• 📚 *Comprehensive Subject Notes*\n"
        "• 📑 *Past Year Questions (PYQs) & Trend Analysis*\n"
        "• 🔍 *Best Recommended Websites, Apps & Books*\n"
        "• 📖 *Syllabus & High-Weightage Topics*"
    )

    keyboard = [
        [
            InlineKeyboardButton("🎯 JEE Mains", callback_data="st_e_jee_mains"),
            InlineKeyboardButton("🚀 JEE Advanced", callback_data="st_e_jee_adv")
        ],
        [
            InlineKeyboardButton("🩺 NEET UG", callback_data="st_e_neet"),
            InlineKeyboardButton("⚡ MHT-CET", callback_data="st_e_mht_cet")
        ],
        [
            InlineKeyboardButton("🏛 UPSC Civil Services", callback_data="st_e_upsc"),
            InlineKeyboardButton("⚔️ NDA / NA", callback_data="st_e_nda")
        ],
        [
            InlineKeyboardButton("💻 GATE Exam", callback_data="st_e_gate"),
            InlineKeyboardButton("🎓 CUET UG", callback_data="st_e_cuet")
        ],
        [
            InlineKeyboardButton("🔙 Back to Main Menu", callback_data="st_m")
        ]
    ]
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))


async def show_exam_details(update: Update, context: ContextTypes.DEFAULT_TYPE, exam_id: str):
    """Show details and action options for a selected competitive exam."""
    query = update.callback_query
    await query.answer()

    exam = get_exam_details(exam_id)
    if not exam:
        await show_exams_menu(update, context)
        return

    subjects_str = ", ".join(exam["subjects"])
    top_apps_str = ", ".join(exam["top_apps"])

    text = (
        f"{exam['name']}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🏛 *Conducted by:* {exam['conducted_by']}\n"
        f"📊 *Level:* {exam['level']}\n"
        f"📚 *Key Subjects:* `{subjects_str}`\n\n"
        f"📝 *About:* {exam['description']}\n\n"
        f"📱 *Top Rated Apps:* {top_apps_str}\n\n"
        f"👇 *What study material do you want for {exam['name']}?*"
    )

    keyboard = [
        [
            InlineKeyboardButton("⚡ Formula Cheatsheet", callback_data=f"st_ea_{exam_id}_cheatsheet"),
            InlineKeyboardButton("📚 Subject Notes", callback_data=f"st_ea_{exam_id}_notes")
        ],
        [
            InlineKeyboardButton("📕 Send PDF Cheatsheet", callback_data=f"st_edoc_{exam_id}_pdf"),
            InlineKeyboardButton("📄 Send TXT Notes", callback_data=f"st_edoc_{exam_id}_txt")
        ],
        [
            InlineKeyboardButton("📑 Past Year Questions (PYQ)", callback_data=f"st_ea_{exam_id}_pyq"),
            InlineKeyboardButton("🌐 Web Research & Portals", callback_data=f"st_ea_{exam_id}_research")
        ],
        [
            InlineKeyboardButton("📖 High-Yield Syllabus Topics", callback_data=f"st_ea_{exam_id}_chapters")
        ],
        [
            InlineKeyboardButton("🔙 Back to Exams", callback_data="st_ex"),
            InlineKeyboardButton("🏠 Study Hub", callback_data="st_m")
        ]
    ]
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))


def build_pdf_document(title: str, subtitle: str, content: str) -> bytes:
    """Generate clean, printable PDF document bytes using fpdf2."""
    from fpdf import FPDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Document Header Title
    pdf.set_font('Helvetica', 'B', 14)
    clean_title = title[:65].encode('latin-1', 'replace').decode('latin-1')
    pdf.cell(0, 9, clean_title, new_x='LMARGIN', new_y='NEXT', align='C')

    # Subtitle / Board / Class
    pdf.set_font('Helvetica', 'I', 10)
    clean_sub = subtitle[:85].encode('latin-1', 'replace').decode('latin-1')
    pdf.cell(0, 6, clean_sub, new_x='LMARGIN', new_y='NEXT', align='C')
    pdf.ln(3)

    # Divider bar
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    # Document Body
    pdf.set_font('Helvetica', size=10)
    # Strip markdown syntax for pristine printable PDF readability
    clean_content = content.replace('**', '').replace('##', '').replace('###', '')
    safe_body = clean_content.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 6, safe_body)

    return bytes(pdf.output())


def fetch_wikipedia_summary(query: str):
    """Fetch live encyclopedia summary and URL from Wikipedia API."""
    clean_q = re.sub(r'^\d+(\.\d+)*\s*', '', query).split('(')[0].strip()
    url = 'https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=' + urllib.parse.quote(clean_q) + '&format=json'
    req = urllib.request.Request(url, headers={'User-Agent': 'TelegramStudyBot/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode())
            results = data.get('query', {}).get('search', [])
            if results:
                first = results[0]
                title = first['title']
                page_url = 'https://en.wikipedia.org/wiki/' + urllib.parse.quote(title.replace(' ', '_'))
                snippet = re.sub(r'<[^>]+>', '', first.get('snippet', ''))
                return {
                    "title": title,
                    "snippet": snippet,
                    "url": page_url
                }
    except Exception:
        pass
    return None


async def safe_edit_study_message(query, text: str, reply_markup=None):
    """Safely edit Telegram message with length capping and markdown parse error fallback."""
    if len(text) > 3900:
        text = text[:3800] + "\n\n⚠️ _[Truncated for Telegram message length]_"

    try:
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
    except Exception as e:
        # Markdown entity error (e.g. unclosed *, _, [ from AI response)
        # Fallback to plain text so the student always gets their study material!
        try:
            await query.edit_message_text(
                text,
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )
        except Exception as e2:
            try:
                await query.message.reply_text(
                    text[:3800],
                    reply_markup=reply_markup,
                    disable_web_page_preview=True
                )
            except Exception:
                pass


async def handle_exam_action(update: Update, context: ContextTypes.DEFAULT_TYPE, exam_id: str, action: str):
    """Generate notes, cheatsheet, PYQs, or research for a competitive exam."""
    query = update.callback_query
    await query.answer()

    exam = get_exam_details(exam_id)
    if not exam:
        await show_exams_menu(update, context)
        return

    if action == "chapters":
        # Show high yield topics directly
        text = (
            f"📖 *{exam['name']} — High-Weightage Chapters & Syllabus*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        )
        for subj, topics in exam["high_yield_topics"].items():
            text += f"🔹 *{subj}:*\n  • {topics}\n\n"
        
        text += "💡 _Focus 80% of your time on these high-yield topics to maximize your score!_"
        
        keyboard = [
            [
                InlineKeyboardButton("⚡ Formula Cheatsheet", callback_data=f"st_ea_{exam_id}_cheatsheet"),
                InlineKeyboardButton("📑 Past Year Qs (PYQ)", callback_data=f"st_ea_{exam_id}_pyq")
            ],
            [
                InlineKeyboardButton("🔙 Back to Exam Options", callback_data=f"st_e_{exam_id}"),
                InlineKeyboardButton("🏠 Study Hub", callback_data="st_m")
            ]
        ]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    wait_text = f"⏳ *Researching & generating high-yield {action.replace('_', ' ')} for {exam['name']} with Gemini AI...*"
    await query.edit_message_text(wait_text, parse_mode="Markdown")

    mode_map = {
        "cheatsheet": "exam_cheatsheet",
        "notes": "notes",
        "pyq": "exam_pyq",
        "research": "exam_research"
    }
    mode = mode_map.get(action, "notes")

    # Call AI generation in a thread
    import asyncio
    context_dict = {
        "mode": mode,
        "exam": exam["full_name"],
        "subject": ", ".join(exam["subjects"]),
        "topic": f"{exam['full_name']} Complete Preparation & Study Material",
        "query": f"{exam['full_name']} {action}"
    }
    content = await asyncio.to_thread(ai_service.generate_study_content, context_dict)

    formatted_response = (
        f"🎯 *{exam['name']} — {action.upper()}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{content}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🌐 _Verified with Toppers' strategy & Official Portals_"
    )

    keyboard = [
        [
            InlineKeyboardButton("⚡ Formula Cheatsheet", callback_data=f"st_ea_{exam_id}_cheatsheet"),
            InlineKeyboardButton("📑 PYQs", callback_data=f"st_ea_{exam_id}_pyq")
        ],
        [
            InlineKeyboardButton("🔍 Best Websites & Apps", callback_data=f"st_ea_{exam_id}_research"),
            InlineKeyboardButton("📚 Notes", callback_data=f"st_ea_{exam_id}_notes")
        ],
        [
            InlineKeyboardButton("🔙 Back to Exam", callback_data=f"st_e_{exam_id}"),
            InlineKeyboardButton("🎯 All Exams", callback_data="st_ex")
        ]
    ]
    await safe_edit_study_message(query, formatted_response, reply_markup=InlineKeyboardMarkup(keyboard))


async def show_classes_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show school / college classes menu."""
    query = update.callback_query
    await query.answer()

    text = (
        "🏫 *SCHOOL & COLLEGE BOARD CURRICULUM* 📖\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Select your Class / Standard:\n\n"
        "• 🔟 *Class 10 (SSC / Matric)* — Complete Balbharati & NCERT\n"
        "• 🎓 *Class 12 (HSC / Inter)* — Science, Maths & English\n"
        "• 🎒 *Class 11 (FYJC)* — Foundation & Core Subjects\n"
        "• 📖 *Class 9 & 8* — Essential Concepts & Language Study\n\n"
        "👇 *Choose your Class below:*"
    )

    keyboard = [
        [
            InlineKeyboardButton("🔟 Class 10 (SSC / 10th)", callback_data="st_b_c10"),
            InlineKeyboardButton("🎓 Class 12 (HSC / 12th)", callback_data="st_b_c12")
        ],
        [
            InlineKeyboardButton("🎒 Class 11 (FYJC / 11th)", callback_data="st_b_c11"),
            InlineKeyboardButton("📖 Class 9 (9th)", callback_data="st_b_c9")
        ],
        [
            InlineKeyboardButton("📚 Class 8 (8th Standard)", callback_data="st_b_c8")
        ],
        [
            InlineKeyboardButton("🔙 Back to Main Menu", callback_data="st_m")
        ]
    ]
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))


BOARDS_PER_PAGE = 8


async def show_boards_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, class_code: str, page: int = 0):
    """Show boards for selected class with 2-column layout and pagination."""
    query = update.callback_query
    await query.answer()

    class_id = CODE_TO_CLASS.get(class_code, "class_10")
    class_info = CLASSES_CATALOG.get(class_id, {})
    class_name = class_info.get("name", "Selected Class")

    boards = get_boards_for_class(class_id)
    total_boards = len(boards)
    total_pages = max(1, math.ceil(total_boards / BOARDS_PER_PAGE))
    page = max(0, min(page, total_pages - 1))

    start_idx = page * BOARDS_PER_PAGE
    end_idx = min(start_idx + BOARDS_PER_PAGE, total_boards)
    current_boards = boards[start_idx:end_idx]

    text = (
        f"🏫 *{class_name} — Select Board*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Choose your educational board to get authentic textbooks, chapter lists, and question solutions.\n\n"
        f"📍 *Showing Boards {start_idx + 1}–{end_idx} of {total_boards} (Page {page + 1}/{total_pages})*\n"
        f"Includes all Indian State Boards (Maharashtra, UP, Bihar, Rajasthan, etc.) & National Boards!\n\n"
        f"👇 *Tap your Board below:*"
    )

    keyboard = []
    # 2 columns of board buttons
    row = []
    for b in current_boards:
        b_code = b["code"]
        short_b = BOARD_CODE_MAP.get(b_code, b_code[:3])
        b_meta = BOARDS_CATALOG.get(b_code, {})
        short_name = b_meta.get("short_name", b["name"])
        row.append(InlineKeyboardButton(short_name, callback_data=f"st_s_{class_code}_{short_b}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    # Pagination arrows row
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"st_b_{class_code}_{page - 1}"))
    nav_row.append(InlineKeyboardButton(f"📄 {page + 1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"st_b_{class_code}_{page + 1}"))
    keyboard.append(nav_row)

    keyboard.append([
        InlineKeyboardButton("🔙 Back to Classes", callback_data="st_cl"),
        InlineKeyboardButton("🏠 Study Hub", callback_data="st_m")
    ])
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))


async def show_subjects_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, class_code: str, board_code: str):
    """Show subjects for selected class and board."""
    query = update.callback_query
    await query.answer()

    class_id = CODE_TO_CLASS.get(class_code, "class_10")
    board_id = CODE_TO_BOARD.get(board_code, "msbshse")

    class_name = CLASSES_CATALOG.get(class_id, {}).get("name", "Class 10")
    board_name = BOARDS_CATALOG.get(board_id, {}).get("name", "Board")

    subjects = get_subjects(class_id, board_id)

    text = (
        f"📚 *{class_name} | {board_name}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Select a subject to view all chapters, notes, textbook exercise solutions, and study links:\n"
    )

    keyboard = []
    row = []
    for s in subjects:
        short_s = SUBJ_CODE_MAP.get(s["code"], s["code"][:3])
        btn_text = f"📖 {s['name']}"
        # Make buttons compact
        row.append(InlineKeyboardButton(btn_text, callback_data=f"st_c_{class_code}_{board_code}_{short_s}_0"))
        if len(row) == 1: # 1 button per line for readability of subject names
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([
        InlineKeyboardButton("🔙 Back to Boards", callback_data=f"st_b_{class_code}"),
        InlineKeyboardButton("🏠 Study Hub", callback_data="st_m")
    ])

    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))


async def show_chapters_paginated(update: Update, context: ContextTypes.DEFAULT_TYPE, class_code: str, board_code: str, subj_code: str, page: int):
    """Show paginated chapter list with Left (⬅️) and Right (➡️) arrow buttons."""
    query = update.callback_query
    await query.answer()

    class_id = CODE_TO_CLASS.get(class_code, "class_10")
    board_id = CODE_TO_BOARD.get(board_code, "msbshse")
    subj_id = CODE_TO_SUBJ.get(subj_code, "english")

    class_name = CLASSES_CATALOG.get(class_id, {}).get("name", "Class 10")
    board_name = BOARDS_CATALOG.get(board_id, {}).get("name", "Board")
    
    curriculum = CURRICULUM_DATA.get((class_id, board_id), CURRICULUM_DATA.get(("class_10", "msbshse"), {}))
    subj_name = curriculum.get(subj_id, {}).get("name", "Subject")
    chapters = get_chapters(class_id, board_id, subj_id)

    total_chapters = len(chapters)
    if total_chapters == 0:
        await query.edit_message_text("❌ No chapters found for this subject.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data=f"st_s_{class_code}_{board_code}")]]))
        return

    total_pages = math.ceil(total_chapters / ITEMS_PER_PAGE)
    page = max(0, min(page, total_pages - 1))

    start_idx = page * ITEMS_PER_PAGE
    end_idx = min(start_idx + ITEMS_PER_PAGE, total_chapters)
    current_chapters = chapters[start_idx:end_idx]

    text = (
        f"📖 *{subj_name}*\n"
        f"🏫 *{class_name} | {board_name}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📑 *Showing Lessons {start_idx + 1}–{end_idx} of {total_chapters} (Page {page + 1}/{total_pages})*\n\n"
        f"Tap any lesson below to view **Notes, Textbook Solutions, Important Questions & Study Links**:\n"
    )

    keyboard = []
    for idx, chap_name in enumerate(current_chapters):
        actual_idx = start_idx + idx
        # Display chapter number and concise title
        short_title = chap_name[:45] + "..." if len(chap_name) > 45 else chap_name
        keyboard.append([
            InlineKeyboardButton(
                f"🔹 {short_title}",
                callback_data=f"st_ca_{class_code}_{board_code}_{subj_code}_{actual_idx}"
            )
        ])

    # ─── PAGINATION ARROWS (LEFT ⬅️ & RIGHT ➡️) ───
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"st_c_{class_code}_{board_code}_{subj_code}_{page - 1}"))
    
    nav_row.append(InlineKeyboardButton(f"📄 {page + 1}/{total_pages}", callback_data="noop"))

    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"st_c_{class_code}_{board_code}_{subj_code}_{page + 1}"))

    keyboard.append(nav_row)

    # Return buttons
    keyboard.append([
        InlineKeyboardButton("📚 Change Subject", callback_data=f"st_s_{class_code}_{board_code}"),
        InlineKeyboardButton("🏠 Study Hub", callback_data="st_m")
    ])

    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))


async def show_chapter_action_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, class_code: str, board_code: str, subj_code: str, chap_idx: int):
    """Show options for a specific chapter (Notes, Solutions, Important Qs, Web Links)."""
    query = update.callback_query
    await query.answer()

    class_id = CODE_TO_CLASS.get(class_code, "class_10")
    board_id = CODE_TO_BOARD.get(board_code, "msbshse")
    subj_id = CODE_TO_SUBJ.get(subj_code, "english")

    class_name = CLASSES_CATALOG.get(class_id, {}).get("name", "Class 10")
    board_name = BOARDS_CATALOG.get(board_id, {}).get("name", "Board")
    curriculum = CURRICULUM_DATA.get((class_id, board_id), CURRICULUM_DATA.get(("class_10", "msbshse"), {}))
    subj_name = curriculum.get(subj_id, {}).get("name", "Subject")
    chapters = get_chapters(class_id, board_id, subj_id)

    chap_name = chapters[chap_idx] if 0 <= chap_idx < len(chapters) else "Selected Chapter"
    page_of_chapter = chap_idx // ITEMS_PER_PAGE

    text = (
        f"📖 *{chap_name}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📚 *Subject:* {subj_name}\n"
        f"🏫 *Curriculum:* {class_name} | {board_name}\n\n"
        f"👇 *What study assistance do you need for this lesson?*\n\n"
        f"• 📝 *Chapter Notes & Summary:* Key points, central idea, mind map\n"
        f"• ❓ *Textbook Questions & Solutions:* Complete exercise step-by-step solutions\n"
        f"• 🎯 *Important Questions & PYQs:* Board exam high-probability questions\n"
        f"• 🌐 *Top Study Websites & Links:* Best sites offering PDF notes & video lectures"
    )

    keyboard = [
        [
            InlineKeyboardButton("📝 Chapter Notes & Summary", callback_data=f"st_g_{class_code}_{board_code}_{subj_code}_{chap_idx}_notes"),
            InlineKeyboardButton("❓ Questions & Solutions", callback_data=f"st_g_{class_code}_{board_code}_{subj_code}_{chap_idx}_sol")
        ],
        [
            InlineKeyboardButton("📕 Send PDF File to Chat", callback_data=f"st_doc_{class_code}_{board_code}_{subj_code}_{chap_idx}_pdf"),
            InlineKeyboardButton("📄 Send TXT File to Chat", callback_data=f"st_doc_{class_code}_{board_code}_{subj_code}_{chap_idx}_txt")
        ],
        [
            InlineKeyboardButton("🌐 Web & PDF Research Links", callback_data=f"st_g_{class_code}_{board_code}_{subj_code}_{chap_idx}_links"),
            InlineKeyboardButton("🎯 Important Qs", callback_data=f"st_g_{class_code}_{board_code}_{subj_code}_{chap_idx}_imp")
        ],
        [
            InlineKeyboardButton("🔙 Back to Chapters", callback_data=f"st_c_{class_code}_{board_code}_{subj_code}_{page_of_chapter}"),
            InlineKeyboardButton("🏠 Study Hub", callback_data="st_m")
        ]
    ]

    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))


async def show_source_download_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, class_code: str, board_code: str, subj_code: str, chap_idx: int, source: str):
    """Show format selection (PDF / TXT) for the chosen researched source."""
    query = update.callback_query
    await query.answer()

    class_id = CODE_TO_CLASS.get(class_code, "class_10")
    board_id = CODE_TO_BOARD.get(board_code, "msbshse")
    subj_id = CODE_TO_SUBJ.get(subj_code, "english")

    class_name = CLASSES_CATALOG.get(class_id, {}).get("name", "Class 10")
    board_name = BOARDS_CATALOG.get(board_id, {}).get("name", "Board")
    curriculum = CURRICULUM_DATA.get((class_id, board_id), CURRICULUM_DATA.get(("class_10", "msbshse"), {}))
    subj_name = curriculum.get(subj_id, {}).get("name", "Subject")
    chapters = get_chapters(class_id, board_id, subj_id)
    chap_name = chapters[chap_idx] if 0 <= chap_idx < len(chapters) else "Selected Chapter"

    source_meta = {
        "tg": ("✈️ Telegram Community Notes", "Student revision notes, formulas, and PYQs compiled from Telegram study channels."),
        "tw": ("🐦 Twitter / X Educational Threads", "Educator threads, viral study tips, formulas, and memory mnemonics shared on Twitter / X."),
        "wiki": ("📖 Wikipedia Encyclopedia Study", "In-depth literary analysis, author biography, and historical background from Wikipedia."),
        "yt": ("🎥 YouTube Video Lecture Notes", "Core concept breakdown, lecture timestamps, and visual explanations from top educators."),
        "reddit": ("👾 Reddit Student Community Notes", "Peer study notes, tricky exercise explanations, and topper hacks from student subreddits."),
        "board": ("🏛 Official Textbook Guide", "Standard textbook curriculum notes and model guidelines."),
        "shaalaa": ("📑 Shaalaa.com Solutions", "Step-by-step textbook exercise questions, working steps, and grammar.")
    }
    src_title, src_desc = source_meta.get(source, ("Study Material", "Comprehensive educational notes."))

    text = (
        f"{src_title}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📖 *Topic:* {chap_name}\n"
        f"🏫 *Curriculum:* {class_name} | {board_name}\n\n"
        f"📝 *Description:*\n{src_desc}\n\n"
        f"👇 *Choose format to receive this file directly on Telegram:*\n"
        f"• 📕 *PDF Document:* Printable, styled & formatted for offline revision\n"
        f"• 📄 *TXT Document:* Lightweight, fast & easy to copy/forward"
    )

    keyboard = [
        [
            InlineKeyboardButton("📕 Send PDF File to Chat", callback_data=f"st_doc_{class_code}_{board_code}_{subj_code}_{chap_idx}_{source}_pdf"),
            InlineKeyboardButton("📄 Send TXT File to Chat", callback_data=f"st_doc_{class_code}_{board_code}_{subj_code}_{chap_idx}_{source}_txt")
        ],
        [
            InlineKeyboardButton("🔙 Back to Sources", callback_data=f"st_g_{class_code}_{board_code}_{subj_code}_{chap_idx}_links"),
            InlineKeyboardButton("🏠 Study Hub", callback_data="st_m")
        ]
    ]
    await safe_edit_study_message(query, text, reply_markup=InlineKeyboardMarkup(keyboard))


async def send_study_document(update: Update, context: ContextTypes.DEFAULT_TYPE, class_code: str, board_code: str, subj_code: str, chap_idx: int, doc_format: str, source: str = "general"):
    """Generate and directly send authentic PDF or TXT study notes file tailored to chosen source."""
    query = update.callback_query
    await query.answer("Preparing your file...", show_alert=False)

    class_id = CODE_TO_CLASS.get(class_code, "class_10")
    board_id = CODE_TO_BOARD.get(board_code, "msbshse")
    subj_id = CODE_TO_SUBJ.get(subj_code, "english")

    class_name = CLASSES_CATALOG.get(class_id, {}).get("name", "Class 10")
    board_name = BOARDS_CATALOG.get(board_id, {}).get("name", "Board")
    curriculum = CURRICULUM_DATA.get((class_id, board_id), CURRICULUM_DATA.get(("class_10", "msbshse"), {}))
    subj_name = curriculum.get(subj_id, {}).get("name", "Subject")
    chapters = get_chapters(class_id, board_id, subj_id)
    chap_name = chapters[chap_idx] if 0 <= chap_idx < len(chapters) else "Selected Chapter"

    source_titles = {
        "tg": "Telegram Community Notes",
        "tw": "Twitter / X Educational Threads",
        "wiki": "Wikipedia Encyclopedia Study",
        "yt": "YouTube Video Lecture Notes",
        "reddit": "Reddit Student Community Notes",
        "board": "Official State Board Guide",
        "shaalaa": "Shaalaa Textbook Solutions"
    }
    source_label = source_titles.get(source, "Complete Study Notes")

    wait_msg = await query.message.reply_text(
        f"⏳ *Compiling {source_label} and creating {doc_format.upper()} document for:*\n`{chap_name}`\n_Please wait a few seconds..._",
        parse_mode="Markdown"
    )

    if source == "wiki":
        mode = "notes"
        query_text = f"{chap_name} Wikipedia encyclopedia deep analysis background and central theme"
    elif source == "tw":
        mode = "notes"
        query_text = f"{board_name} {class_name} {subj_name} {chap_name} Twitter X educator thread revision notes mnemonics quick summary"
    elif source == "yt":
        mode = "notes"
        query_text = f"{board_name} {class_name} {subj_name} {chap_name} YouTube video lecture core concepts summary and key points"
    elif source == "reddit":
        mode = "notes"
        query_text = f"{board_name} {class_name} {subj_name} {chap_name} Reddit student discussion community notes tricky questions insights"
    elif source == "shaalaa":
        mode = "solutions"
        query_text = f"{board_name} {class_name} {subj_name} {chap_name} Shaalaa step by step exercise solutions and grammar"
    elif source == "tg":
        mode = "notes"
        query_text = f"{board_name} {class_name} {subj_name} {chap_name} Telegram toppers revision notes formula cheatsheet and PYQs"
    else:
        mode = "notes"
        query_text = f"{board_name} {class_name} {subj_name} {chap_name} official textbook study notes"

    context_dict = {
        "mode": mode,
        "board": board_name,
        "standard": class_name,
        "subject": subj_name,
        "topic": f"{chap_name} ({source_label})",
        "query": query_text
    }
    content = await asyncio.to_thread(ai_service.generate_study_content, context_dict)
    clean_title = re.sub(r'[^\w\-_\. ]', '', chap_name).strip().replace(' ', '_')[:30]
    chat_id = update.effective_chat.id

    if doc_format == "pdf":
        try:
            pdf_bytes = build_pdf_document(
                title=f"{chap_name} ({source_label})",
                subtitle=f"{board_name} | {class_name} | {subj_name}",
                content=content
            )
            bio = io.BytesIO(pdf_bytes)
            bio.name = f"{clean_title}_{source.upper()}_Notes.pdf"
            await context.bot.send_document(
                chat_id=chat_id,
                document=bio,
                filename=f"{clean_title}_{source.upper()}_Notes.pdf",
                caption=f"📕 *{chap_name}*\n📚 *Source:* {source_label}\n🏫 *{board_name} | {class_name}*\n\n✅ _Printable PDF document ready! Tap to download & print._",
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"PDF build error: {e}, falling back to TXT")
            doc_format = "txt"

    if doc_format == "txt":
        full_text = (
            f"====================================================\n"
            f"{chap_name}\n"
            f"Source: {source_label}\n"
            f"{board_name} - {class_name} ({subj_name})\n"
            f"====================================================\n\n"
            f"{content}\n\n"
            f"====================================================\n"
            f"Delivered by 24/7 AI Study Hub on Telegram\n"
            f"====================================================\n"
        )
        bio = io.BytesIO(full_text.encode('utf-8'))
        bio.name = f"{clean_title}_{source.upper()}_Notes.txt"
        await context.bot.send_document(
            chat_id=chat_id,
            document=bio,
            filename=f"{clean_title}_{source.upper()}_Notes.txt",
            caption=f"📄 *{chap_name}*\n📚 *Source:* {source_label}\n🏫 *{board_name} | {class_name}*\n\n✅ _Offline TXT document ready! Tap to read & share._",
            parse_mode="Markdown"
        )

    try:
        await wait_msg.delete()
    except Exception:
        pass


async def send_exam_document(update: Update, context: ContextTypes.DEFAULT_TYPE, exam_id: str, doc_format: str):
    """Generate and directly send PDF or TXT file for competitive exam."""
    query = update.callback_query
    await query.answer("Preparing exam material...", show_alert=False)

    exam = get_exam_details(exam_id)
    if not exam:
        return

    exam_name = exam["name"]
    wait_msg = await query.message.reply_text(
        f"⏳ *Compiling {exam_name} High-Yield Formula Cheatsheet & {doc_format.upper()} file...*\n_Please wait a few seconds..._",
        parse_mode="Markdown"
    )

    context_dict = {
        "mode": "exam_cheatsheet",
        "exam": exam["full_name"],
        "subject": ", ".join(exam["subjects"]),
        "topic": f"{exam['full_name']} Formula Cheatsheet & Revision Guide",
        "query": f"{exam['full_name']} formula cheatsheet"
    }
    content = await asyncio.to_thread(ai_service.generate_study_content, context_dict)
    clean_title = re.sub(r'[^\w\-_\. ]', '', exam_id).strip().replace(' ', '_')[:35]
    chat_id = update.effective_chat.id

    if doc_format == "pdf":
        try:
            pdf_bytes = build_pdf_document(
                title=f"{exam_name} Formula Cheatsheet",
                subtitle=f"{exam['full_name']} | {exam['conducted_by']}",
                content=content
            )
            bio = io.BytesIO(pdf_bytes)
            bio.name = f"{clean_title}_Cheatsheet.pdf"
            await context.bot.send_document(
                chat_id=chat_id,
                document=bio,
                filename=f"{clean_title}_Cheatsheet.pdf",
                caption=f"⚡ *{exam_name} Formula Cheatsheet*\n🏛 *Conducted by:* {exam['conducted_by']}\n\n✅ _Printable PDF formula cheatsheet ready! Tap to download & print._",
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Exam PDF error: {e}, falling back to TXT")
            doc_format = "txt"

    if doc_format == "txt":
        full_text = (
            f"====================================================\n"
            f"{exam_name} - {exam['full_name']}\n"
            f"Conducted by: {exam['conducted_by']}\n"
            f"====================================================\n\n"
            f"{content}\n\n"
            f"====================================================\n"
            f"Generated by 24/7 AI Study Hub\n"
            f"====================================================\n"
        )
        bio = io.BytesIO(full_text.encode('utf-8'))
        bio.name = f"{clean_title}_Cheatsheet.txt"
        await context.bot.send_document(
            chat_id=chat_id,
            document=bio,
            filename=f"{clean_title}_Cheatsheet.txt",
            caption=f"📄 *{exam_name} Formula Cheatsheet*\n🏛 *Conducted by:* {exam['conducted_by']}\n\n✅ _Offline TXT formula cheatsheet ready! Tap to read & share._",
            parse_mode="Markdown"
        )

    try:
        await wait_msg.delete()
    except Exception:
        pass


async def generate_chapter_study_content(update: Update, context: ContextTypes.DEFAULT_TYPE, class_code: str, board_code: str, subj_code: str, chap_idx: int, action_type: str):
    """Generate notes, textbook solutions, important questions, or live web research links for the chapter."""
    query = update.callback_query
    await query.answer()

    class_id = CODE_TO_CLASS.get(class_code, "class_10")
    board_id = CODE_TO_BOARD.get(board_code, "msbshse")
    subj_id = CODE_TO_SUBJ.get(subj_code, "english")

    class_name = CLASSES_CATALOG.get(class_id, {}).get("name", "Class 10")
    board_name = BOARDS_CATALOG.get(board_id, {}).get("name", "Board")
    curriculum = CURRICULUM_DATA.get((class_id, board_id), CURRICULUM_DATA.get(("class_10", "msbshse"), {}))
    subj_name = curriculum.get(subj_id, {}).get("name", "Subject")
    chapters = get_chapters(class_id, board_id, subj_id)
    chap_name = chapters[chap_idx] if 0 <= chap_idx < len(chapters) else "Selected Chapter"
    page_of_chapter = chap_idx // ITEMS_PER_PAGE

    # ─── ACTION: LIVE WEB & PDF RESEARCH ───
    if action_type == "links":
        wait_text = f"🌐 *Researching Twitter/X, YouTube, Reddit, Telegram, Wikipedia & Textbook links for '{chap_name}'...*"
        await query.edit_message_text(wait_text, parse_mode="Markdown")

        # Live Wikipedia Search
        wiki_data = await asyncio.to_thread(fetch_wikipedia_summary, chap_name)

        # Twitter / X Search query
        twitter_query = f"{board_name} {class_name} {chap_name} notes"
        twitter_url = f"https://twitter.com/search?q={urllib.parse.quote(twitter_query)}&f=top"

        # YouTube Lecture Search query
        yt_query = f"{board_name} {class_name} {subj_name} {chap_name} full chapter"
        yt_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(yt_query)}"

        # Reddit Community Search query
        reddit_query = f"{class_name} {subj_name} {chap_name} notes"
        reddit_url = f"https://www.reddit.com/search/?q={urllib.parse.quote(reddit_query)}"

        # Google Search query for notes & solutions
        google_query = f"{board_name} {class_name} {subj_name} {chap_name} notes pdf download"
        google_url = f"https://www.google.com/search?q={urllib.parse.quote(google_query)}"

        # Shaalaa Search
        shaalaa_query = f"{board_name} {class_name} {chap_name}"
        shaalaa_url = f"https://www.shaalaa.com/search?q={urllib.parse.quote(shaalaa_query)}"

        # Official Textbook Portal
        if "maharashtra" in board_name.lower():
            portal_name = "Balbharati Books Portal"
            portal_url = "https://cart.ebalbharati.in/balbooks/"
        else:
            portal_name = "NCERT Official Books Portal"
            portal_url = "https://ncert.nic.in/textbook.php"

        wiki_section = ""
        if wiki_data:
            wiki_section = (
                f"📖 *Wikipedia Encyclopedia Entry:*\n"
                f"• *Title:* `{wiki_data['title']}`\n"
                f"• *Extract:* _{wiki_data['snippet']}..._\n\n"
            )

        text = (
            f"🌐 *MULTI-PLATFORM AI STUDY NOTES DISCOVERY* 🔍\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📖 *Topic:* {chap_name}\n"
            f"🏫 *Curriculum:* {class_name} | {board_name}\n\n"
            f"{wiki_section}"
            f"📁 *Discovered Study Materials & Source Files:*\n"
            f"• ✈️ *Telegram Notes:* Revision formulas, student PYQs & toppers' notes\n"
            f"• 🐦 *Twitter / X Threads:* Educator viral threads, mnemonics & quick tips\n"
            f"• 📖 *Wikipedia:* In-depth encyclopedia analysis & literary context\n"
            f"• 🎥 *YouTube Lectures:* Video lecture summaries, key concepts & timestamps\n"
            f"• 👾 *Reddit Community:* Peer discussions, tricky questions & hacks\n"
            f"• 🏛 *{portal_name}:* Official curriculum chapters & model answers\n"
            f"• 📑 *Shaalaa.com:* Complete textbook exercise step-by-step Q&A\n\n"
            f"👇 *Tap any source below to receive its notes file (PDF/TXT) directly on Telegram, or open live web links:*"
        )

        web_btns = [
            [
                InlineKeyboardButton("✈️ Get Telegram Notes File", callback_data=f"st_src_{class_code}_{board_code}_{subj_code}_{chap_idx}_tg"),
                InlineKeyboardButton("🐦 Get Twitter/X Notes File", callback_data=f"st_src_{class_code}_{board_code}_{subj_code}_{chap_idx}_tw")
            ],
            [
                InlineKeyboardButton("📖 Get Wikipedia Study File", callback_data=f"st_src_{class_code}_{board_code}_{subj_code}_{chap_idx}_wiki"),
                InlineKeyboardButton("🎥 Get YouTube Lecture File", callback_data=f"st_src_{class_code}_{board_code}_{subj_code}_{chap_idx}_yt")
            ],
            [
                InlineKeyboardButton("👾 Get Reddit Notes File", callback_data=f"st_src_{class_code}_{board_code}_{subj_code}_{chap_idx}_reddit"),
                InlineKeyboardButton("📑 Get Shaalaa Solutions File", callback_data=f"st_src_{class_code}_{board_code}_{subj_code}_{chap_idx}_shaalaa")
            ],
            [
                InlineKeyboardButton("🏛 Get Official Textbook File", callback_data=f"st_src_{class_code}_{board_code}_{subj_code}_{chap_idx}_board")
            ],
            [
                InlineKeyboardButton("🐦 Search Twitter (X)", url=twitter_url),
                InlineKeyboardButton("🎥 Watch on YouTube", url=yt_url)
            ],
            [
                InlineKeyboardButton("👾 Search Reddit", url=reddit_url),
                InlineKeyboardButton("🔍 Google (PDFs)", url=google_url)
            ],
            [
                InlineKeyboardButton(f"📚 {portal_name}", url=portal_url),
                InlineKeyboardButton("✈️ Search Telegram", url=f"https://t.me/share/url?url=https://t.me&text={urllib.parse.quote(f'{board_name} {class_name} {chap_name} notes pdf')}")
            ],
            [
                InlineKeyboardButton("🔙 Back to Chapter Menu", callback_data=f"st_ca_{class_code}_{board_code}_{subj_code}_{chap_idx}"),
                InlineKeyboardButton("📑 Chapter List", callback_data=f"st_c_{class_code}_{board_code}_{subj_code}_{page_of_chapter}")
            ]
        ]

        await safe_edit_study_message(query, text, reply_markup=InlineKeyboardMarkup(web_btns))
        return

    # ─── ACTION: AI NOTES / SOLUTIONS / IMPORTANT QUESTIONS ───
    action_label = {
        "notes": "Chapter Notes & Summary",
        "sol": "Textbook Questions & Solutions",
        "imp": "Important Board Questions"
    }.get(action_type, "Study Notes")

    wait_text = f"⏳ *Researching & generating {action_label} for '{chap_name}' using Gemini AI...*"
    await query.edit_message_text(wait_text, parse_mode="Markdown")

    mode_map = {
        "notes": "notes",
        "sol": "solutions",
        "imp": "exam_pyq"
    }
    mode = mode_map.get(action_type, "notes")

    context_dict = {
        "mode": mode,
        "board": board_name,
        "standard": class_name,
        "subject": subj_name,
        "topic": chap_name,
        "query": f"{board_name} {class_name} {subj_name} {chap_name} {action_label}"
    }

    content = await asyncio.to_thread(ai_service.generate_study_content, context_dict)

    formatted_response = (
        f"📖 *{chap_name}*\n"
        f"📚 *{subj_name} | {board_name}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{content}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 _Tip: Tap buttons below to download PDF/TXT document directly into Telegram!_"
    )

    keyboard = [
        [
            InlineKeyboardButton("📕 Send PDF File", callback_data=f"st_doc_{class_code}_{board_code}_{subj_code}_{chap_idx}_pdf"),
            InlineKeyboardButton("📄 Send TXT File", callback_data=f"st_doc_{class_code}_{board_code}_{subj_code}_{chap_idx}_txt")
        ],
        [
            InlineKeyboardButton("📝 Notes", callback_data=f"st_g_{class_code}_{board_code}_{subj_code}_{chap_idx}_notes"),
            InlineKeyboardButton("❓ Solutions", callback_data=f"st_g_{class_code}_{board_code}_{subj_code}_{chap_idx}_sol")
        ],
        [
            InlineKeyboardButton("🌐 Web & PDF Research Links", callback_data=f"st_g_{class_code}_{board_code}_{subj_code}_{chap_idx}_links"),
            InlineKeyboardButton("🎯 Important Qs", callback_data=f"st_g_{class_code}_{board_code}_{subj_code}_{chap_idx}_imp")
        ],
        [
            InlineKeyboardButton("🔙 Back to Chapter Menu", callback_data=f"st_ca_{class_code}_{board_code}_{subj_code}_{chap_idx}"),
            InlineKeyboardButton("📑 Chapter List", callback_data=f"st_c_{class_code}_{board_code}_{subj_code}_{page_of_chapter}")
        ]
    ]

    await safe_edit_study_message(query, formatted_response, reply_markup=InlineKeyboardMarkup(keyboard))


async def study_callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Router for all study callbacks."""
    query = update.callback_query
    data = query.data

    if data == "noop":
        await query.answer()
        return

    if data == "st_m":
        await show_study_main(update, context)
    elif data == "st_ex":
        await show_exams_menu(update, context)
    elif data == "st_cl":
        await show_classes_menu(update, context)
    elif data.startswith("st_e_"):
        # e.g. st_e_jee_mains
        exam_id = data.replace("st_e_", "")
        await show_exam_details(update, context, exam_id)
    elif data.startswith("st_ea_"):
        # e.g. st_ea_jee_mains_notes
        parts = data.split("_")
        # st, ea, <exam_id>, <action>
        # exam_id might have underscore like jee_mains, so take action as last item
        action = parts[-1]
        exam_id = "_".join(parts[2:-1])
        await handle_exam_action(update, context, exam_id, action)
    elif data.startswith("st_b_"):
        # e.g. st_b_c10 or st_b_c10_1
        parts = data.split("_")
        class_code = parts[2]
        page = int(parts[3]) if len(parts) > 3 else 0
        await show_boards_menu(update, context, class_code, page)
    elif data.startswith("st_s_"):
        # e.g. st_s_c10_ms
        parts = data.split("_")
        class_code = parts[2]
        board_code = parts[3]
        await show_subjects_menu(update, context, class_code, board_code)
    elif data.startswith("st_c_"):
        # e.g. st_c_c10_ms_eng_0
        parts = data.split("_")
        class_code = parts[2]
        board_code = parts[3]
        subj_code = parts[4]
        page = int(parts[5]) if len(parts) > 5 else 0
        await show_chapters_paginated(update, context, class_code, board_code, subj_code, page)
    elif data.startswith("st_ca_"):
        # e.g. st_ca_c10_ms_eng_0
        parts = data.split("_")
        class_code = parts[2]
        board_code = parts[3]
        subj_code = parts[4]
        chap_idx = int(parts[5]) if len(parts) > 5 else 0
        await show_chapter_action_menu(update, context, class_code, board_code, subj_code, chap_idx)
    elif data.startswith("st_g_"):
        # e.g. st_g_c10_ms_eng_0_notes
        parts = data.split("_")
        class_code = parts[2]
        board_code = parts[3]
        subj_code = parts[4]
        chap_idx = int(parts[5]) if len(parts) > 5 else 0
        action_type = parts[6] if len(parts) > 6 else "notes"
        await generate_chapter_study_content(update, context, class_code, board_code, subj_code, chap_idx, action_type)
    elif data.startswith("st_src_"):
        # e.g. st_src_c10_ms_eng_0_tg
        parts = data.split("_")
        class_code = parts[2]
        board_code = parts[3]
        subj_code = parts[4]
        chap_idx = int(parts[5]) if len(parts) > 5 else 0
        source = parts[6] if len(parts) > 6 else "tg"
        await show_source_download_menu(update, context, class_code, board_code, subj_code, chap_idx, source)
    elif data.startswith("st_doc_"):
        # e.g. st_doc_c10_ms_eng_0_tg_pdf OR st_doc_c10_ms_eng_0_pdf
        parts = data.split("_")
        class_code = parts[2]
        board_code = parts[3]
        subj_code = parts[4]
        chap_idx = int(parts[5]) if len(parts) > 5 else 0
        if len(parts) >= 8:
            source = parts[6]
            doc_format = parts[7]
        elif len(parts) == 7:
            if parts[6] in ["pdf", "txt"]:
                source = "general"
                doc_format = parts[6]
            else:
                source = parts[6]
                doc_format = "pdf"
        else:
            source = "general"
            doc_format = "pdf"
        await send_study_document(update, context, class_code, board_code, subj_code, chap_idx, doc_format, source)
    elif data.startswith("st_edoc_"):
        # e.g. st_edoc_jee_mains_pdf
        parts = data.split("_")
        doc_format = parts[-1]
        exam_id = "_".join(parts[2:-1])
        await send_exam_document(update, context, exam_id, doc_format)
