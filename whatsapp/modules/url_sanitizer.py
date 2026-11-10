"""URL Sanitizer and Link Cleaner for WhatsApp Bot.
Enforces clean, canonical, official URLs.
Strips tracking query parameters, decodes search/ad redirects (Bing/Google/DDG),
detects and rejects ad/affiliate domains, and formats clean WhatsApp links.
"""

import re
import urllib.parse
from typing import Tuple, Optional

# Known advertising, tracking, or redirector domains to reject or strip
AD_TRACKING_DOMAINS = [
    "bing.com/aclick",
    "bat.bing.com",
    "googleadservices.com",
    "doubleclick.net",
    "ad.doubleclick.net",
    "clickserve.dartsearch.net",
    "adservice.google.",
    "pagead2.googlesyndication.",
    "taboola.com",
    "outbrain.com",
    "adnxs.com",
    "criteo.com",
    "syndication.twitter.com"
]

# Query parameters to completely strip
TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "utm_id",
    "gclid", "fbclid", "msclkid", "mc_cid", "mc_eid", "dclid",
    "ref", "ref_src", "ref_url", "referrer", "aff", "affiliate", "partner",
    "source", "spm", "_hsenc", "_hsmi", "wbraid", "gbraid", "adurl"
}

def unwrap_redirect(url: str) -> str:
    """Unwrap search engine redirect links (Google, Bing, DuckDuckGo)."""
    if not url or not isinstance(url, str):
        return ""
    
    clean = url.strip()
    
    # 1. Google Redirects: https://www.google.com/url?q=https://real.com...
    if "google." in clean and "/url?" in clean:
        try:
            parsed = urllib.parse.urlparse(clean)
            qs = urllib.parse.parse_qs(parsed.query)
            target = qs.get("q", [None])[0] or qs.get("url", [None])[0]
            if target and target.startswith("http"):
                clean = target
        except Exception:
            pass

    # 2. DuckDuckGo Redirects: https://duckduckgo.com/l/?uddg=https%3A%2F%2Freal.com...
    if "duckduckgo.com/l/" in clean:
        try:
            parsed = urllib.parse.urlparse(clean)
            qs = urllib.parse.parse_qs(parsed.query)
            target = qs.get("uddg", [None])[0]
            if target and target.startswith("http"):
                clean = target
        except Exception:
            pass

    # 3. Bing Redirects: check for destination param in bing
    if "bing.com" in clean and ("r=" in clean or "u=" in clean):
        try:
            parsed = urllib.parse.urlparse(clean)
            qs = urllib.parse.parse_qs(parsed.query)
            target = qs.get("u", [None])[0] or qs.get("r", [None])[0]
            if target:
                # Often base64 encoded by Bing if starts with a1
                if target.startswith("http"):
                    clean = target
                elif target.startswith("a1aHR0"):
                    import base64
                    try:
                        decoded = base64.b64decode(target[2:]).decode("utf-8", errors="ignore")
                        if decoded.startswith("http"):
                            clean = decoded
                    except Exception:
                        pass
        except Exception:
            pass

    return clean

def is_ad_or_tracking_url(url: str) -> bool:
    """Check if the URL is an advertising or tracking redirect."""
    if not url:
        return False
    lower_url = url.lower()
    for bad in AD_TRACKING_DOMAINS:
        if bad in lower_url:
            return True
    return False

def sanitize_url(raw_url: str) -> str:
    """Sanitize URL to its clean, canonical, tracking-free form."""
    if not raw_url or not isinstance(raw_url, str):
        return ""

    url = unwrap_redirect(raw_url.strip())
    
    # Check if still an ad URL
    if is_ad_or_tracking_url(url):
        return ""

    try:
        parsed = urllib.parse.urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return url

        # Parse and filter query parameters
        qs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=False)
        clean_qs = [
            (k, v) for k, v in qs
            if k.lower() not in TRACKING_PARAMS and not k.lower().startswith("utm_")
        ]

        netloc = parsed.netloc.lower()
        path = parsed.path

        # Platform specific canonicalization
        # 1. GitHub: https://github.com/owner/repo
        if "github.com" in netloc:
            parts = [p for p in path.split("/") if p]
            if len(parts) >= 2:
                # Keep only /owner/repo (drop extra /issues, /tree, etc. unless needed)
                canonical_path = f"/{parts[0]}/{parts[1]}"
                return f"https://github.com{canonical_path}"

        # 2. Google Play: https://play.google.com/store/apps/details?id=...
        if "play.google.com" in netloc and "/apps/details" in path:
            qs_dict = dict(clean_qs)
            pkg_id = qs_dict.get("id")
            if pkg_id:
                return f"https://play.google.com/store/apps/details?id={pkg_id}"

        # 3. F-Droid: https://f-droid.org/packages/...
        if "f-droid.org" in netloc and "/packages/" in path:
            parts = [p for p in path.split("/") if p]
            if len(parts) >= 2:
                return f"https://f-droid.org/en/packages/{parts[1]}/"

        # 4. YouTube: https://www.youtube.com/watch?v=...
        if "youtube.com" in netloc and "/watch" in path:
            qs_dict = dict(clean_qs)
            vid_id = qs_dict.get("v")
            if vid_id:
                return f"https://www.youtube.com/watch?v={vid_id}"

        # General clean query rebuild
        new_query = urllib.parse.urlencode(clean_qs)
        cleaned = urllib.parse.urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            ""  # Strip fragment
        ))
        return cleaned.rstrip("/")
    except Exception:
        return url

def get_link_label_for_url(url: str, default_label: str = "Open Official Website") -> str:
    """Return an intelligent, friendly label for the link based on its destination."""
    if not url:
        return default_label
    lower = url.lower()
    if "github.com" in lower:
        return "Open GitHub Repository"
    elif "f-droid.org" in lower:
        return "Open on F-Droid"
    elif "play.google.com" in lower:
        return "View on Google Play"
    elif "youtube.com" in lower or "youtu.be" in lower:
        return "Watch on YouTube"
    elif "docs." in lower or "/docs" in lower or "api." in lower:
        return "Open Official Documentation"
    elif "devpost.com" in lower or "hackathon" in lower:
        return "Open Official Hackathon Page"
    elif "scholarship" in lower:
        return "Open Official Application"
    elif "itch.io" in lower or "steampowered.com" in lower:
        return "Open Official Game Page"
    return default_label

def format_clean_link_block(url: str, custom_label: Optional[str] = None) -> str:
    """Format clean link section for WhatsApp with friendly action label and canonical URL.
    
    Produces:
    🔗 OFFICIAL LINK
    👉 [Open Official Website](https://clean-url.org)
    """
    clean = sanitize_url(url)
    if not clean:
        return ""
    
    label = custom_label or get_link_label_for_url(clean)
    return (
        "🔗 OFFICIAL LINK\n"
        f"👉 [{label}]({clean})\n"
        f"{clean}"
    )

def extract_and_clean_all_urls(text: str) -> Tuple[str, Optional[str]]:
    """Find any raw/ugly/tracking URLs in a message, sanitize them, and replace with clean format."""
    if not text:
        return text, None

    primary_clean_url = None

    # Replace markdown links: [Label](http...)
    def md_replacer(match):
        nonlocal primary_clean_url
        label = match.group(1).strip()
        raw_target = match.group(2).strip()
        cleaned = sanitize_url(raw_target)
        if not cleaned:
            return ""
        if not primary_clean_url:
            primary_clean_url = cleaned
        return f"[{label}]({cleaned})"

    text = re.sub(r'\[([^\]]+)\]\((https?://[^\s\)]+)\)', md_replacer, text)

    # Replace standalone raw URLs
    def raw_replacer(match):
        nonlocal primary_clean_url
        raw_u = match.group(0).strip().rstrip('.,;)]>')
        cleaned = sanitize_url(raw_u)
        if not cleaned:
            return ""
        if not primary_clean_url:
            primary_clean_url = cleaned
        return cleaned

    # Only match URLs not inside markdown brackets
    text = re.sub(r'(?<!\()(https?://[^\s\)\<\>]+)', raw_replacer, text)

    # Clean up unwanted advertiser labels
    unwanted_phrases = [
        r"Official Site Reference:?",
        r"Partner Link:?",
        r"Development Tools Partner Link:?",
        r"Wix Dev/Web Tools Alternative Integration:?",
        r"Alternative Integration:?"
    ]
    for p in unwanted_phrases:
        text = re.sub(p, "", text, flags=re.IGNORECASE)

    return text.strip(), primary_clean_url
