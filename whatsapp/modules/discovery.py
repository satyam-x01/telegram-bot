import time
import random
import re
import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

from modules.config import config_manager, user_manager, logger, jid_to_str
from modules.searcher import live_searcher
from modules.gemini_ai import gemini_service
from modules.card_rules import CATEGORY_SYSTEM_PROMPT
from modules.url_sanitizer import sanitize_url, format_clean_link_block, extract_and_clean_all_urls, is_ad_or_tracking_url, get_link_label_for_url

DISCOVERY_CATEGORIES = [
    {
        "id": 1,
        "name": "GAMES",
        "label": "🎮 GAMES",
        "queries": [
            "best open source indie games android pc github",
            "trending free indie games itch io github",
            "open source game engines indie games github"
        ]
    },
    {
        "id": 2,
        "name": "ANDROID APPS",
        "label": "📱 ANDROID APPS",
        "queries": [
            "trending open source android utility apps github",
            "best new android tools privacy productivity github",
            "open source android apps fdroid play store"
        ]
    },
    {
        "id": 3,
        "name": "F-DROID",
        "label": "📦 F-DROID",
        "queries": [
            "trending f-droid apps open source android",
            "best new privacy apps f-droid repo",
            "useful open source f-droid utilities android"
        ]
    },
    {
        "id": 4,
        "name": "GITHUB REPOSITORIES",
        "label": "🐙 GITHUB REPOSITORIES",
        "queries": [
            "trending github repositories python javascript rust",
            "popular new open source developer tools github",
            "top github repositories weekly trending"
        ]
    },
    {
        "id": 5,
        "name": "AI TOOLS",
        "label": "🤖 AI TOOLS",
        "queries": [
            "trending new AI tools productive free tier",
            "open source AI productivity tools github",
            "new AI agents tools platforms 2026"
        ]
    },
    {
        "id": 6,
        "name": "AI APIs / DEVELOPER APIs",
        "label": "🔑 AI APIs / DEVELOPER APIs",
        "queries": [
            "free AI API developer tiers models limits",
            "best free developer APIs AI llm platforms",
            "free API platforms developer free credits 2026"
        ]
    },
    {
        "id": 7,
        "name": "OLLAMA / LOCAL AI",
        "label": "🧠 OLLAMA / LOCAL AI",
        "queries": [
            "best new ollama models quantized local AI",
            "trending local LLM models ollama huggingface",
            "efficient open source reasoning models ollama"
        ]
    },
    {
        "id": 8,
        "name": "TERMUX",
        "label": "⌨️ TERMUX",
        "queries": [
            "best termux tools developer utilities github",
            "termux scripts android developer tools github",
            "termux open source utilities android"
        ]
    },
    {
        "id": 9,
        "name": "COURSES",
        "label": "🎓 COURSES",
        "queries": [
            "best free computer science programming courses certificate",
            "free online tech courses with free certificate",
            "free web development AI courses certification"
        ]
    },
    {
        "id": 10,
        "name": "SCHOLARSHIPS",
        "label": "🎓 SCHOLARSHIPS",
        "queries": [
            "global tech scholarships computer science engineering",
            "student developer scholarships opportunities tech",
            "international technology student scholarships"
        ]
    },
    {
        "id": 11,
        "name": "HACKATHONS / COMPETITIONS",
        "label": "🏆 HACKATHONS / COMPETITIONS",
        "queries": [
            "upcoming global virtual hackathons devpost online",
            "online developer AI hackathons cash prizes",
            "global virtual coding hackathons student competitions"
        ]
    },
    {
        "id": 12,
        "name": "FREE CREDITS / PROMOTIONS",
        "label": "🎁 FREE CREDITS / PROMOTIONS",
        "queries": [
            "free cloud credits developer startup promotion",
            "free AI API credits developer promotional offers",
            "free developer student pack perks cloud credits"
        ]
    },
    {
        "id": 13,
        "name": "HOSTING / CLOUD",
        "label": "☁️ HOSTING / CLOUD",
        "queries": [
            "best free cloud hosting developer tier serverless",
            "free VPS database static hosting developers",
            "free container hosting serverless platforms"
        ]
    },
    {
        "id": 14,
        "name": "PRIVACY / SECURITY",
        "label": "🔐 PRIVACY / SECURITY",
        "queries": [
            "best open source privacy tools security github",
            "self hosted privacy security utilities open source",
            "encrypted open source privacy tools android pc"
        ]
    },
    {
        "id": 15,
        "name": "BROWSER EXTENSIONS",
        "label": "🧩 BROWSER EXTENSIONS",
        "queries": [
            "best open source browser extensions developer productivity",
            "privacy browser extensions open source chrome firefox",
            "useful developer extensions chrome web store"
        ]
    },
    {
        "id": 16,
        "name": "YOUTUBE VIDEOS / CHANNELS",
        "label": "▶️ YOUTUBE VIDEOS / CHANNELS",
        "queries": [
            "best computer science engineering channels youtube",
            "top programming developer education channels youtube",
            "best AI engineering tutorials channels youtube"
        ]
    },
    {
        "id": 17,
        "name": "NEWS / TECHNOLOGY NEWS",
        "label": "📰 NEWS / TECHNOLOGY NEWS",
        "queries": [
            "breaking technology news open source AI breakthroughs",
            "latest tech news computing hardware open source",
            "major AI research tech news updates"
        ]
    },
    {
        "id": 18,
        "name": "ASTRONOMY / SPACE",
        "label": "🚀 ASTRONOMY / SPACE",
        "queries": [
            "latest space discoveries James Webb telescope NASA ESA",
            "astronomy scientific discoveries missions space",
            "breakthrough astronomy telescope discoveries"
        ]
    },
    {
        "id": 19,
        "name": "ANIME",
        "label": "🎌 ANIME",
        "queries": [
            "top rated anime season rankings review legal stream",
            "trending anime open source tracking discovery apps",
            "critically acclaimed anime series reviews ratings"
        ]
    },
    {
        "id": 20,
        "name": "WEB APPS / WEBSITES",
        "label": "🌐 WEB APPS / WEBSITES",
        "queries": [
            "most useful free websites web apps productivity",
            "cool useful developer web utilities online free",
            "underrated productive internet tools websites"
        ]
    },
    {
        "id": 21,
        "name": "SOCIAL MEDIA DISCOVERIES",
        "label": "👤 SOCIAL MEDIA DISCOVERIES",
        "queries": [
            "best tech educators creators accounts learning programming",
            "top open source developer creators insights",
            "notable software engineering creators profiles"
        ]
    },
    {
        "id": 22,
        "name": "DAILY DATA / SIMPLE UPDATES",
        "label": "🪙 DAILY DATA / SIMPLE UPDATES",
        "queries": [
            "gold price today 24k 22k live update",
            "currency exchange rate usd inr live market",
            "crypto bitcoin market price trends today"
        ]
    }
]

# Evergreen mainstream apps that should never be sent as a generic discovery
EVERGREEN_APPS = {
    "whatsapp", "chrome", "google chrome", "facebook", "instagram",
    "tiktok", "twitter", "x.com", "snapchat", "youtube", "gmail"
}

GENERIC_TITLES = {
    "GAME NAME", "APP NAME", "TOOL NAME", "REPOSITORY NAME", "AI TOOL NAME",
    "WEBSITE NAME", "SERVICE NAME", "OFFER NAME", "SCHOLARSHIP NAME", "EVENT NAME",
    "MODEL NAME", "API NAME", "COURSE NAME", "EXTENSION NAME", "VIDEO", "DAILY UPDATE",
    "UNKNOWN", "DISCOVERY NAME", "PROJECT NAME", "NAME", "TITLE"
}

BAD_PLACEHOLDERS = [
    "REPOSITORY NAME", "APP NAME", "GAME NAME", "TOOL NAME", "AI TOOL NAME",
    "WEBSITE NAME", "SERVICE NAME", "OFFER NAME", "SCHOLARSHIP NAME",
    "EVENT NAME", "MODEL NAME", "API NAME", "COURSE NAME", "EXTENSION NAME",
    "OWNER / ORGANIZATION", "WHAT DOES THIS PROJECT DO?", "MAIN FEATURES (→ ...)",
    "WHAT CAN I BUILD / DO?", "WHAT WILL I LEARN? (→ ...)", "WHY WATCH?",
    "DISCOVERY NAME", "ANIME NAME", "PROJECT NAME", "REAL WEBSITE/SERVICE NAME"
]

def is_invalid_card(text: str) -> Tuple[bool, str]:
    """Detect if card contains unfilled template placeholders, broken syntax, or meta-notes."""
    if not text or len(text.strip()) < 80:
        return True, "Too short or empty"
    
    upper_t = text.upper()
    for bp in BAD_PLACEHOLDERS:
        if bp in upper_t:
            return True, f"Contains unfilled placeholder '{bp}'"
    
    # Check for prompt rule leak or meta-notes
    if re.search(r'\(?\*?Note:\s*(?:Per\s+Rule|WhatsApp|Rule\s*#|As requested)', text, re.IGNORECASE):
        return True, "Contains rule leak or internal meta note"
        
    return False, "Valid"

def clean_meta_notes(card_text: str) -> str:
    """Strip out any AI disclaimers or trailing notes like *(Note: ...)*."""
    if not card_text:
        return ""
    # Remove trailing notes
    cleaned = re.sub(r'[\r\n]+\s*\(\*?Note:.*?\)?\s*$', '', card_text, flags=re.DOTALL | re.IGNORECASE)
    # Remove single lines that start with Note:
    lines = [l for l in cleaned.splitlines() if not re.match(r'^\s*\(?\*?Note:\s*(?:Per\s+Rule|WhatsApp|Rule\s*#)', l, re.IGNORECASE)]
    return "\n".join(lines).strip()

def is_evergreen_app(title: str, text: str) -> bool:
    """Detect if the item is a widely known evergreen app without a brand new update."""
    clean_t = re.sub(r'[^\w\s]', ' ', title.lower()).strip()
    words = clean_t.split()
    for w in words:
        if w in EVERGREEN_APPS:
            if not any(k in text.lower() for k in ["new feature", "v2", "update", "redesign", "library", "open source"]):
                return True
    return False

def extract_discovery_title(card_text: str, default_title: str) -> str:
    """Extract clean title or app name from generated discovery card."""
    if not card_text:
        return default_title

    # 1. Look for category header icons (e.g. 🎮 GAME, 📱 APP, 🐙 REPO, 🌐 WEBSITE)
    icon_pattern = r'(?:🎮|📱|📦|🐙|🤖|🔑|🧠|⌨️|🎓|🏆|🎁|☁️|🔐|🧩|▶️|📰|🚀|🎌|🌐|👤|🪙)\s*([A-Za-z0-9\s\.\-_+]{2,60})'
    m_icon = re.search(icon_pattern, card_text)
    if m_icon:
        candidate = m_icon.group(1).strip()
        clean_upper = re.sub(r'[^\w\s]', '', candidate).strip().upper()
        if clean_upper and clean_upper not in GENERIC_TITLES:
            return candidate

    # 2. Look for Name: or Title:
    m_name = re.search(r'(?:Name|Title|Project)\s*:\s*([^\n\r]+)', card_text, re.IGNORECASE)
    if m_name:
        cand = m_name.group(1).strip().replace("*", "")
        clean_upper = re.sub(r'[^\w\s]', '', cand).strip().upper()
        if clean_upper and clean_upper not in GENERIC_TITLES:
            return cand[:60]

    return default_title

class DynamicResearchEngine:
    """Researches and generates automated updates tailored with Category-Specific Cards,
    strict duplicate checking, link sanitization, and pre-send quality validation.
    """

    def __init__(self):
        pass

    def research_for_user(self, user_jid: str) -> Optional[dict]:
        """Perform live web research for a user's specific custom topic and format with Category-Specific Card."""
        clean_jid = jid_to_str(user_jid)
        slot_num, slot_data = user_manager.get_selected_automation(clean_jid)
        custom_topic = slot_data.get("prompt", "").strip()

        if not custom_topic:
            logger.warning(f"User {clean_jid} has no prompt set in Slot #{slot_num}.")
            return {
                "message": f"⚠️ *Slot #{slot_num} is Empty!*\n\nPlease configure this slot first by sending:\n`/create {slot_num} <your topic>`",
                "skipped": True
            }

        counter = slot_data.get("discovery_count", 0) + 1
        current_date_str = datetime.now().strftime("%d %b %Y")
        history = slot_data.get("history", [])

        # Check if user has personal Gemini API key configured
        user_record = user_manager.get_or_create_user(clean_jid)
        user_api_key = user_record.get("custom_gemini_key", "").strip() or None
        user_name = user_record.get("name", "").strip() or "User"

        is_universal_feed = (
            not custom_topic or
            custom_topic.lower() in ["feed", "all", "discover", "discovery", "anything", "random", "explore"] or
            "DISCOVERY" in custom_topic or
            "Category" in custom_topic or
            "Rotate" in custom_topic
        )

        max_attempts = 4
        for attempt in range(max_attempts):
            cat_idx = (counter - 1 + attempt) % len(DISCOVERY_CATEGORIES)
            current_cat = DISCOVERY_CATEGORIES[cat_idx]

            logger.info(f"Researching for {clean_jid} ({user_name}) [Slot #{slot_num} - Discovery #{counter}] [Attempt {attempt+1}/{max_attempts}]...")

            # 1. Build targeted search queries
            if not is_universal_feed:
                # User set a specific topic (e.g. "best website for web developer")
                # Search strictly for what the user wants!
                search_queries = [
                    f"{custom_topic} best tools resources 2026",
                    f"{custom_topic} trending",
                    f"top {custom_topic} open source",
                    custom_topic
                ]
            else:
                # Universal rotation feed
                search_queries = current_cat["queries"]

            # 2. Perform live search to get clean, verified candidates
            search_results = []
            for q in search_queries:
                res = live_searcher.search(q, max_results=6)
                if res:
                    search_results = res
                    break

            if not search_results:
                logger.warning(f"No search results found on attempt {attempt+1}. Retrying...")
                continue

            # 3. Filter out candidates already in user's history
            fresh_candidates = [
                r for r in search_results
                if not user_manager.is_user_duplicate(clean_jid, r.get("title", ""), r.get("link", ""), slot_num=slot_num)
                and not is_evergreen_app(r.get("title", ""), r.get("snippet", ""))
            ]

            if not fresh_candidates:
                fresh_candidates = search_results

            # Try candidate results
            for cand in fresh_candidates[:3]:
                cand_title = cand.get("title", f"Discovery #{counter}").strip()
                cand_link = sanitize_url(cand.get("link", "")).strip()
                cand_snippet = cand.get("snippet", "").strip()

                if not cand_title or not cand_link:
                    continue

                raw_card = None

                # 4. Synthesize with Gemini using real verified facts
                if gemini_service.is_available(api_key=user_api_key):
                    synthesis_prompt = f"""{CATEGORY_SYSTEM_PROMPT}

CURRENT RESEARCH MISSION:
Write a category-appropriate Discovery Card for:
━━━━━━━━━━━━━━━━━━━━
🔥 DISCOVERY #{counter}
━━━━━━━━━━━━━━━━━━━━

USER TOPIC: {custom_topic}
DATE: {current_date_str}

VERIFIED LIVE WEB DISCOVERY TO WRITE ABOUT:
• Title / Product: {cand_title}
• Official Canonical URL: {cand_link}
• Verified Web Information: {cand_snippet}

MANDATORY RULES:
1. Write a real, comprehensive Discovery Card specifically about '{cand_title}'.
2. Detect the matching category (Web Apps, GitHub Repo, AI Tool, Dev Utility, etc.) and use that style.
3. ABSOLUTE RULE: NEVER output placeholder tokens (such as 'REPOSITORY NAME', 'APP NAME', 'OWNER / ORGANIZATION', etc.). Fill every section with real facts from the finding above!
4. Include visual 5-point rating bars (█████ 5/5) for relevant quality metrics.
5. Provide the clean link:
   🔗 OFFICIAL LINK
   👉 Visit [{cand_title}]({cand_link})
   {cand_link}
6. Tailor relevance for web development, Android, Termux, and {user_name}'s technical interests.
7. NEVER include notes or explanations like '*(Note: ...)*'. Output ONLY the clean WhatsApp card."""

                    try:
                        ai_res = gemini_service.generate_with_fallback(synthesis_prompt, api_key=user_api_key)
                        if ai_res:
                            ai_cleaned = clean_meta_notes(ai_res)
                            is_bad, reason = is_invalid_card(ai_cleaned)
                            if not is_bad:
                                raw_card = ai_cleaned
                            else:
                                logger.warning(f"AI response rejected ({reason}): {ai_cleaned[:120]}...")
                    except Exception as e:
                        logger.warning(f"Gemini synthesis error: {e}")

                # 5. Fallback if AI unavailable or produced invalid card
                if not raw_card:
                    clean_link_formatted = format_clean_link_block(cand_link)
                    raw_card = f"""━━━━━━━━━━━━━━━━━━━━
🔥 DISCOVERY #{counter}
━━━━━━━━━━━━━━━━━━━━

🌐 {cand_title}

💡 What it is:
{cand_snippet[:280]}

📊 Quality Check:
⚡ Utility        █████  5/5
🛠️ Features       ████░  4/5
💰 Free Value     █████  5/5

🎯 Why it's useful for you:
• Directly matches your interest in: {custom_topic[:40]}
• Verified live on {current_date_str}

🏆 VERDICT: 🟢 WORTH TRYING

{clean_link_formatted}
📅 VERIFIED: {current_date_str}"""

                # 6. Post-process & clean URLs
                cleaned_card, found_url = extract_and_clean_all_urls(raw_card)
                cleaned_card = clean_meta_notes(cleaned_card)

                extracted_title = extract_discovery_title(cleaned_card, default_title=cand_title)
                extracted_link = found_url or cand_link

                # Reject if ad or evergreen app
                if extracted_link and is_ad_or_tracking_url(extracted_link):
                    logger.warning(f"Rejected ad link: {extracted_link}")
                    continue

                if is_evergreen_app(extracted_title, cleaned_card):
                    logger.warning(f"Rejected evergreen app: {extracted_title}")
                    continue

                # Ensure official link block is present
                if extracted_link and "🔗 OFFICIAL LINK" not in cleaned_card:
                    clean_block = format_clean_link_block(extracted_link)
                    if "📅 VERIFIED" in cleaned_card:
                        cleaned_card = cleaned_card.replace("📅 VERIFIED", f"{clean_block}\n\n📅 VERIFIED")
                    else:
                        cleaned_card += f"\n\n{clean_block}"

                # Double check against duplicate history
                if user_manager.is_user_duplicate(clean_jid, extracted_title, extracted_link, slot_num=slot_num):
                    logger.warning(f"Duplicate rejected: {extracted_title}")
                    continue

                # Success! Record history and return
                user_manager.add_user_history(clean_jid, {
                    "title": extracted_title,
                    "link": extracted_link,
                    "topic": custom_topic[:60],
                    "number": counter,
                    "slot": slot_num,
                    "timestamp": time.time()
                }, slot_num=slot_num)

                logger.info(f"Successfully generated Discovery #{counter} for {clean_jid}: '{extracted_title}'")

                return {
                    "message": cleaned_card,
                    "title": extracted_title,
                    "link": extracted_link,
                    "topic": custom_topic,
                    "number": counter
                }

        # If all attempts exhausted
        logger.error(f"Failed to find non-duplicate discovery for {clean_jid} after {max_attempts} attempts.")
        return {
            "message": "⚠️ Important:\nCould not find a fresh, non-duplicate discovery this cycle. Will retry in next interval.",
            "skipped": True
        }

discovery_engine = DynamicResearchEngine()

