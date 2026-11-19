import asyncio
import io
import re
import json
import html
import os
import httpx
import random
import string
import time
import struct
import hmac
import hashlib
import base64
from datetime import datetime, timedelta
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton as _PTBInlineButton,
    InlineKeyboardMarkup,
    BotCommand,
)
try:
    from telegram import KeyboardButtonRequestChat, ChatAdministratorRights
except ImportError:      # very old PTB
    KeyboardButtonRequestChat = ChatAdministratorRights = None
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler, ChatMemberHandler
from telegram.ext.filters import MessageFilter

# ==================== LOCAL CONFIGURATION ====================
# This is the complete single-file bot. Replace the two placeholders below.
# Never share this file after putting real credentials in it.
CONFIG_BOT_TOKEN = "9059865948:AAGgIH8jkqMZ0Acl4Cx3xHQ8ACbtbmOHlus"
CONFIG_STEX_API_KEY = "YOUR_STEXSMS_API_KEY"        # <- paste your StexSMS API key (or set it in Admin > STEX CONFIG)
CONFIG_STEX_BASE_URL = "YOUR_STEXSMS_BASE_URL"      # <- paste your StexSMS base URL (or set it in Admin > STEX CONFIG)
CONFIG_ADMIN_ID = 8987847878
# VOLTX SMS panel (second panel, same API style as Stex). Can also be set from Admin > STEX CONFIG > SET VOLT KEY / URL.
CONFIG_VOLT_API_KEY = "MZ806L2CW1P"
CONFIG_VOLT_BASE_URL = "https://api.2oo9.cloud/MZ806L2CW1P/tnevs/@public/api"
CONFIG_OTP_GROUP_ID = -1004483533929
CONFIG_OTP_GROUP_LINK = "https://t.me/Otp_Hub_rcv"
# OTP FORWARDER BOT (@All_otp_rcv_bot): the ONLY bot that posts OTP cards into the OTP group.
# The main number bot sends OTPs to its users only.
CONFIG_FWD_BOT_TOKEN = "9192150713:AAFFh-JuBJAzVeH4PGzjDKReo9a6mrVUZ1g"
CONFIG_FWD_BOT_USERNAME = "All_otp_rcv_bot"
# FORCE JOIN channels (users must join ALL of them). chat_id is filled in by /forcesetup (see below).
CONFIG_FORCE_CHANNELS = []     # add channels from  Admin Panel > Bot Settings > FORCE JOIN SYSTEM


def InlineKeyboardButton(*args, style=None, api_kwargs=None, **kwargs):
    """Accept style=... on any PTB version by routing it through api_kwargs."""
    if style:
        api_kwargs = {**(api_kwargs or {}), "style": style}
    return _PTBInlineButton(*args, api_kwargs=api_kwargs, **kwargs)

def _safe_task(coro):
    """create_task wrapper: log errors instead of failing silently."""
    async def _runner():
        try:
            await coro
        except Exception as e:
            import traceback
            print("TASK ERROR:", e)
            traceback.print_exc()
    return asyncio.create_task(_runner())

# Premium copy button (PTB 21+)
try:
    from telegram import CopyTextButton
    HAS_COPY_BTN = True
except ImportError:
    HAS_COPY_BTN = False

# ==================== CONFIG SECTION ====================

# Credentials are configured above in this same file.
# Environment variables override these values when provided.
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip() or CONFIG_BOT_TOKEN.strip()
USER_DATA_FILE = "users.json"
PAID_SMS_FILE = "paid_sms.json"
STATS_FILE = "user_stats.json"
REFERRAL_DATA_FILE = "referral_data.json"
BANNED_USERS_FILE = "banned_users.json"
WITHDRAW_DATA_FILE = "withdraw_requests.json"
ACTIVITY_LOGS_FILE = "activity_logs.json"
DATA_RANGE_FILE = "datarange.json"
SETTINGS_FILE = "settings.json"

BOT_USERNAME = "topsmsrec_bot"  # confirmed again at start-up via getMe

# ==================== ADMIN CONFIGURATION ====================
# Set the primary admin ID only here.
# Additional admins can still be added from the Bot Settings menu.
ADMIN_ID = int(os.getenv("ADMIN_ID", str(CONFIG_ADMIN_ID or "8987847878")))
ADMINS = [ADMIN_ID]

OTP_GROUP_ID = int(os.getenv("OTP_GROUP_ID", str(CONFIG_OTP_GROUP_ID or "-5535914265")))

# ==================== PREMIUM EMOJI MAPPING ====================

EMOJI_ID_MAP = {
    "telegram": "5271801931814165886", "instagram": "5269682734820777950",
    "facebook": "5269427536453984598", "tiktok": "5271527792641595125",
    "x": "5269500885905468781",        "whatsapp": "5271536803482981220",
    "up": "5244837092042750681",        "down": "5246762912428603768",
    "add": "5397916757333654639",       "setting": "5341715473882955310",
    "1st": "5440539497383087970",       "2st": "5447203607294265305",
    "3rd": "5453902265922376865",       "free": "5406756500108501710",
    "msg": "5253742260054409879",       "link": "5271604874419647061",
    "status": "5231200819986047254",    "home": "5416041192905265756",
    "gift_box": "5970074171449808121",  "delete": "5422557736330106570",
    "number_change": "5267295703666824255", "refer_btn": "5420396762189831222",
    "get_number_btn": "5375338737028841420", "cross": "5420130255174145507",
    "stop": "5956074558044770726",      "ban": "5420323339723881652",
    "loading": "5386367538735104399",   "profile": "5352861489541714456",
    "done": "6298670698948724690",      "otp_success": "5190781475468915802",
    "nagad": "5352985330628730418",     "bkash": "5348469219761626211",
    "rocket": "5346042941196507141",    "binance": "5348212415077064131",
    "live": "5355102594886833928",      "developer": "5267294466716244344",
    "channel": "6215074610845585917",   "copy": "5429483843541284898",
    "admin": "5350396951407895212",     "waiting": "6217721388736712699",
    "back": "5267490665117275176",      "leader_board": "5280769763398671636",
    "money": "6233367447789899509",     "discord": "5807892405306791778",
    "custom_range": "5231012545799666522", "paypal": "5107533253946901363",
    "imo": "5337155807752524558",       "hi": "5353027129250453493",
    "off": "5352974971167611327",       "diamond": "5251562950698759162",
    "broadcast": "5251671501702196837", "key": "5296369303661067030",
    "bot_logo": "4943094697238201446",  "tk": "5201873447554145566",
    "roket": "5188481279963715781",     "all_done": "5859265295113261399",
    "yes": "5875017993909440887",       "no": "5875005555684152921",
    "fire_love": "5864093929275658617",
}

FALLBACK_EMOJI_MAP = {
    "telegram": "\u2708\ufe0f", "instagram": "\U0001f4f7", "facebook": "\U0001f535",
    "tiktok": "\U0001f3b5", "x": "\u274c", "whatsapp": "\U0001f4ac",
    "up": "\U0001f4c8", "down": "\U0001f4c9", "add": "\u2795", "setting": "\u2699\ufe0f",
    "1st": "\U0001f947", "2st": "\U0001f948", "3rd": "\U0001f949", "free": "\U0001f193",
    "msg": "\U0001f4ac", "link": "\U0001f517", "status": "\U0001f4ca", "home": "\U0001f3e0",
    "gift_box": "\U0001f381", "delete": "\U0001f5d1\ufe0f", "number_change": "\U0001f504",
    "get_number_btn": "\U0001f4de", "cross": "\u274c", "stop": "\U0001f6d1",
    "ban": "\U0001f6ab", "loading": "\u23f3", "profile": "\U0001f464", "done": "\u2705",
    "otp_success": "\u2b50", "nagad": "\U0001f7e0", "bkash": "\U0001f496",
    "rocket": "\U0001f680", "binance": "\U0001f7e1", "live": "\U0001f7e2",
    "developer": "\U0001f468\u200d\U0001f4bb", "channel": "\U0001f4e2",
    "copy": "\U0001f4cb", "admin": "\U0001f451", "waiting": "\u23f3", "back": "\U0001f519",
    "leader_board": "\U0001f3c6", "custom_range": "\U0001f3af", "refer_btn": "\U0001f517",
    "paypal": "\U0001f4b3", "imo": "\U0001f4ac", "hi": "\U0001f44b", "off": "\U0001f6d1",
    "diamond": "\U0001f48e", "broadcast": "\U0001f4e2", "key": "\U0001f511", "tk": "\u09f3",
    "roket": "\U0001f680", "all_done": "\u2705", "yes": "\u2714\ufe0f", "no": "\u274c",
    "fire_love": "\u2764\ufe0f",
}

PREMIUM_FLAGS = {
    "\U0001f1fa\U0001f1f8": "5913463998522592692",
    "\U0001f1fa\U0001f1e6": "5911406692007941050",
    "\U0001f1f5\U0001f1f1": "5913550391789752571",
    "\U0001f1f0\U0001f1ff": "5913724621433082323",
    "\U0001f1e6\U0001f1ff": "5911197578640233518",
    "\U0001f1ea\U0001f1fa": "5911106310585193018",
    "\U0001f1e6\U0001f1f2": "5913272455866093666",
    "\U0001f1f7\U0001f1fa": "5913274246867456342",
    "\U0001f1fa\U0001f1ff": "5911051846104912282",
    "\U0001f1e9\U0001f1ea": "5911096835887337583",
    "\U0001f1ef\U0001f1f5": "5913293711659241040",
    "\U0001f1f9\U0001f1f7": "5910995113881901195",
    "\U0001f1e7\U0001f1fe": "5911011185649521599",
    "\U0001f1ec\U0001f1e7": "5913443365499703513",
    "\U0001f1ee\U0001f1f3": "5913754823643107921",
    "\U0001f1e7\U0001f1f7": "5911148568768418614",
    "\U0001f1fe\U0001f1ea": "5913346492512341993",
    "\U0001f1fb\U0001f1f3": "5913428887164949581",
    "\U0001f1e6\U0001f1ea": "5913726554168365343",
    "\U0001f1fa\U0001f1ec": "5913488939397681980",
    "\U0001f1f9\U0001f1f2": "5913315521503170180",
    "\U0001f1f9\U0001f1f3": "5911332947419468671",
    "\U0001f1f9\U0001f1ed": "5913617968805187987",
    "\U0001f1f9\U0001f1ff": "5911418949844603556",
    "\U0001f1f8\U0001f1ea": "5911156510162949403",
    "\U0001f1f8\U0001f1e9": "5911387497799094470",
    "\U0001f1ea\U0001f1f8": "5911193287967904547",
    "\U0001f1f1\U0001f1f0": "5911293163137406640",
    "\U0001f1ff\U0001f1e6": "5911203119148044594",
    "\U0001f1f8\U0001f1ec": "5911531460808051849",
    "\U0001f1f7\U0001f1f8": "5913592598433369871",
    "\U0001f1f8\U0001f1f3": "5910995302860461643",
    "\U0001f1f6\U0001f1e6": "5911260864983339619",
    "\U0001f1f5\U0001f1f9": "5911023653939581472",
    "\U0001f1f5\U0001f1ed": "5911268638874145162",
    "\U0001f1f5\U0001f1ea": "5911207993935925780",
    "\U0001f1f5\U0001f1f0": "5913705895375672082",
    "\U0001f1f4\U0001f1f2": "5913570801474343473",
    "\U0001f1f3\U0001f1f4": "5913617397574537046",
    "\U0001f1f3\U0001f1ec": "5911143844304393105",
    "\U0001f1f3\U0001f1ff": "5913640044937089340",
    "\U0001f1f3\U0001f1f1": "5913367645226275100",
    "\U0001f1f3\U0001f1f5": "5913496520014958723",
    "\U0001f1f2\U0001f1e6": "5911482111633658301",
    "\U0001f1f2\U0001f1f3": "5911041383564580038",
    "\U0001f1f2\U0001f1e9": "5913456847402045950",
    "\U0001f1f2\U0001f1fd": "5913687302462246518",
    "\U0001f1f2\U0001f1fe": "5913654360063087453",
    "\U0001f1f0\U0001f1ea": "5911154710571651231",
    "\U0001f1f1\U0001f1f9": "5911172315642597775",
    "\U0001f1f1\U0001f1fb": "5913738489882480243",
    "\U0001f1f1\U0001f1e7": "5911504273664905447",
    "\U0001f1ee\U0001f1e9": "5913479361620611038",
    "\U0001f1ee\U0001f1f7": "5911308891307643032",
    "\U0001f1ee\U0001f1f6": "5911382442622587735",
    "\U0001f1ee\U0001f1f1": "5911471936856134692",
    "\U0001f1ee\U0001f1f9": "5913688444923547525",
    "\U0001f1ed\U0001f1fa": "5913767635530551104",
    "\U0001f1ec\U0001f1f7": "5911210399117611448",
    "\U0001f1ec\U0001f1ed": "5913391155877252952",
    "\U0001f1ec\U0001f1ea": "5913434771270144023",
    "\U0001f1eb\U0001f1f7": "5913605586414473124",
    "\U0001f1eb\U0001f1ee": "5911041344909873378",
    "\U0001f1ea\U0001f1f9": "5911078333168227043",
    "\U0001f1ea\U0001f1ec": "5913694831539916769",
    "\U0001f1e9\U0001f1f0": "5911206009661034712",
    "\U0001f1e8\U0001f1fe": "5911023550860366409",
    "\U0001f1ed\U0001f1f7": "5913692684056269311",
    "\U0001f1e8\U0001f1f3": "5913779335021466780",
    "\U0001f1e7\U0001f1e9": "5911365056594973179",
    "\U0001f1e7\U0001f1ea": "5913529642802745141",
    "\U0001f1e6\U0001f1fa": "5913632326880858455",
    "\U0001f1e6\U0001f1f9": "5911338831524664592",
    "\U0001f1e6\U0001f1f7": "5913573356979884082",
    "\U0001f1f0\U0001f1f7": "5913371673905598425",
    "\U0001f1f8\U0001f1e6": "4985897134424328239",
    "\U0001f1e8\U0001f1f4": "5913773060074246009",
    "\U0001f1e8\U0001f1f1": "5911470957603592832",
    "\U0001f1ff\U0001f1f2": "5913564754160389778",
}

def get_tg_emoji(key, default_char=""):
    emoji_id = EMOJI_ID_MAP.get(key)
    fallback = default_char or FALLBACK_EMOJI_MAP.get(key, "\u2b50")
    if emoji_id:
        return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'
    return fallback

def get_country_tg_flag(flag_emoji):
    emoji_id = PREMIUM_FLAGS.get(flag_emoji)
    if emoji_id:
        return f'<tg-emoji emoji-id="{emoji_id}">{flag_emoji}</tg-emoji>'
    return f'<tg-emoji emoji-id="5911106310585193018">{flag_emoji}</tg-emoji>'

# ==================== SYSTEM DYNAMIC SETTINGS ====================

_settings_cache = None

def load_settings():
    global _settings_cache
    if _settings_cache is not None:
        return _settings_cache
    default = {
        "active_panel": "stex",
        "stex_api_key": os.getenv("STEX_API_KEY", "").strip() or CONFIG_STEX_API_KEY.strip(),
        "stex_base_url": os.getenv("STEX_BASE_URL", CONFIG_STEX_BASE_URL),
        "volt_enabled": True,
        "volt_api_key": os.getenv("VOLT_API_KEY", "").strip() or CONFIG_VOLT_API_KEY.strip(),
        "volt_base_url": os.getenv("VOLT_BASE_URL", CONFIG_VOLT_BASE_URL),
        "panel_url": "",
        "allowed_services": ["Instagram","Facebook","WhatsApp","TikTok","Telegram","Discord","PayPal","Imo"],
        "otp_group_url": CONFIG_OTP_GROUP_LINK,
        "channel_url": "https://t.me/+L9KgoiXOVZkwMGY1",
        "support_username": "@snotpsupport",
        "maintenance_mode": False,
        "cooldown_time": 1.0,
        "min_withdraw": 50.0,
        "otp_bonus": 0.20,
        "numbers_per_request": 1,
        "referral_bonus": 0.0,
        "admins": [ADMIN_ID],
        "owners": [ADMIN_ID],
        "otp_group_chat_id": None,
        "force_join_channel": None,
        "force_join_enabled": True,
        "force_join_channels": [dict(c) for c in CONFIG_FORCE_CHANNELS],
        "manual_services": [],
    }
    if not os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "w") as f:
            json.dump(default, f, indent=4)
        _settings_cache = default
        return default
    try:
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
        updated = False
        for k, v in default.items():
            if k not in data:
                data[k] = v; updated = True
        if data.get("channel_url") in ("https://t.me/+T9TyROmyaBI0NWRl", "", None):   # old OTP-card channel -> new one
            data["channel_url"] = "https://t.me/+L9KgoiXOVZkwMGY1"; updated = True
        if "force_join_channels" not in data:
            data["force_join_channels"] = []; updated = True
        # drop the two unlinked placeholder entries of the previous version (channels are now picked in the panel)
        _old = [c for c in data["force_join_channels"] if not (not c.get("chat_id") and "t.me/+" in str(c.get("link", "")))]
        if len(_old) != len(data["force_join_channels"]):
            data["force_join_channels"] = _old; updated = True
        if data.get("force_join_channel") and not any(str(c.get("chat_id")) == str(data["force_join_channel"]) for c in data["force_join_channels"]):
            data["force_join_channels"].append({"link": "", "chat_id": data["force_join_channel"], "title": str(data["force_join_channel"])}); updated = True
        data["force_join_channel"] = None
        if data.get("otp_group_chat_id") in (-1004316235028, "-1004316235028"):   # old group id -> new one
            data["otp_group_chat_id"] = CONFIG_OTP_GROUP_ID; updated = True
        if data.get("otp_group_url") in ("https://t.me/+1EyRT1VsqNE4YTk9", "", None):   # old group link -> new one
            data["otp_group_url"] = CONFIG_OTP_GROUP_LINK; updated = True
        if updated:
            with open(SETTINGS_FILE, "w") as f:
                json.dump(data, f, indent=4)
        _settings_cache = data
        return data
    except Exception:
        _settings_cache = default
        return default

def save_settings(settings):
    global _settings_cache
    _settings_cache = settings
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

def clean_base_url(url):
    url = str(url).strip().rstrip('/')
    return url.rstrip('/')


def get_numbers_per_request():
    """How many numbers a user gets per Get Number tap (admin setting, 1-10)."""
    try:
        n = int(load_settings().get("numbers_per_request", 1))
    except Exception:
        n = 1
    return max(1, min(10, n))

def number_card_keyboard():
    # 3 ধরনের কালার এবং ইমোজি যোগ করা হয়েছে
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 SAME RANGE", callback_data="same_range", style="primary")],
        [InlineKeyboardButton("📢 OTP GROUP", url=(load_settings().get("otp_group_url") or CONFIG_OTP_GROUP_LINK), style="success")],
        [InlineKeyboardButton("🔙 BACK", callback_data="back_services", style="danger")],
    ])

# ==================== COLORFUL NUMBER CARDS ====================

CARD_COLOR_EMOJIS = ["🟦", "🟩", "🟥", "🟨", "🟪", "🟧", "🟫", "⬛", "⬜"]


def build_number_card_html(number, country_flag=None, country_name=None,
                           status="WAITING", otp="WAITING...", index=1):
    """Build one Telegram HTML card (Telegram does not support background colors)."""
    num = normalize_number(number)
    if not country_flag or not country_name:
        country_flag, country_name = get_country_info(num)
    flag_tg = get_country_tg_flag(country_flag)
    color = CARD_COLOR_EMOJIS[(index - 1) % len(CARD_COLOR_EMOJIS)]
    has_otp = (str(status).upper() == "RECEIVED" and
               otp and str(otp) not in ("WAITING...", "N/A", "None", ""))
    status_icon = "✅" if has_otp else "📶"
    otp_display = str(otp) if has_otp else "WAITING..."
    return (
        f"<blockquote>{color} <b>CARD {index:02d}</b>\n"
        f"🌍 <b>COUNTRY:</b> {flag_tg} {html.escape(str(country_name))}\n\n"
        f"📱 <b>NUMBER:</b> <code>+{html.escape(num)}</code>\n\n"
        f"{status_icon} <b>STATUS:</b> {html.escape(str(status))}\n\n"
        f"🔑 <b>OTP:</b> <code>{html.escape(otp_display)}</code></blockquote>"
    )


def build_numbers_cards_html(numbers_list):
    if not numbers_list:
        return "⚠️ <i>No numbers available.</i>"
    return "\n\n".join(
        build_number_card_html(
            item.get("number", ""), item.get("country_flag"),
            item.get("country_name"), item.get("status", "WAITING"),
            item.get("otp", "WAITING..."), index
        )
        for index, item in enumerate(numbers_list, 1)
    )


def render_active_number_cards(uid, message_id, range_text=None):
    """Re-render every number belonging to this user in the same Telegram message."""
    records = [
        (num, info) for num, info in active_numbers.items()
        if isinstance(info, dict) and info.get("uid") == uid
        and info.get("message_id") == message_id
    ]
    if not records:
        return "⚠️ <i>Number card data is no longer available.</i>"
    cards = []
    for num, info in records:
        flag, country = get_country_info(num)
        cards.append({
            "number": num, "country_flag": flag, "country_name": country,
            "status": info.get("status", "WAITING"),
            "otp": info.get("otp", "WAITING..."),
        })
    header_range = range_text or records[0][1].get("range", "")
    header = (
        "╭━━━〔 ✅ <b>YOUR NUMBER DETAILS</b> ✅ 〕━━━╮\n"
        f"📶 <b>RANGE:</b> <code>{html.escape(str(header_range))}</code>\n"
        "╰━━━━━━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
    )
    return header + build_numbers_cards_html(cards)


def _unset(v):
    """True for empty values and for the YOUR_... placeholders."""
    v = str(v or "").strip()
    return (not v) or v.upper().startswith("YOUR")

def get_api_credentials():
    """(api_key, base_url) of StexSMS. Admin-panel value first, then env, then the CONFIG constant. '' = not set."""
    settings = load_settings()
    key = next((v for v in (settings.get("stex_api_key"), os.getenv("STEX_API_KEY"), CONFIG_STEX_API_KEY) if not _unset(v)), "")
    base = next((v for v in (settings.get("stex_base_url"), os.getenv("STEX_BASE_URL"), CONFIG_STEX_BASE_URL) if not _unset(v)), "")
    return str(key).strip(), clean_base_url(base) if base else ""

def get_api_urls(base_url):
    base = str(base_url).strip().rstrip('/')
    return {"getnum": f"{base}/getnum",
            "liveaccess": f"{base}/liveaccess",
            "console": f"{base}/console",
            "otp": f"{base}/success-otp"}

def get_api_headers(api_key):
    return {"mauthapi": api_key}

# ---------- Multi panel: Stex + VoltX (same API style, different base URL / key) ----------
range_panels = {}    # RANGE -> set of panel names that list it (so Get Number asks the right panel first)
number_panel = {}    # number -> panel name it came from

def get_panels():
    """Enabled panels as [(name, api_key, base_url)]: Stex first, then VoltX."""
    out = []
    k, b = get_api_credentials()
    if k and b: out.append(("Stex", k, b))      # skipped until the real StexSMS key + URL are set
    st = load_settings()
    if st.get("volt_enabled", True):
        vk = str(st.get("volt_api_key", "")).strip()
        vb = clean_base_url(st.get("volt_base_url", ""))
        if not _unset(vk) and not _unset(vb):
            out.append(("VoltX", vk, vb))
    return out

def _note_range_panel(items, pname):
    for obj in items or []:
        rng = obj if isinstance(obj, str) else (obj.get("range") or obj.get("prefix") or obj.get("range_text") or obj.get("value") or "") if isinstance(obj, dict) else ""
        rng = str(rng).strip().upper()
        if rng and re.search(r"\d", rng):
            range_panels.setdefault(rng, set()).add(pname)
    if len(range_panels) > 20000: range_panels.clear()

async def fetch_all_otps():
    """OTP items of every enabled panel (VoltX ids are prefixed so they never clash with Stex). None = no panel answered."""
    allotps, any_ok = [], False
    for pname, pkey, pbase in get_panels():
        try:
            r = await client_async.get(get_api_urls(pbase)["otp"], headers=get_api_headers(pkey))
            if r.status_code != 200: continue
            items = stex_otp_items(r.json())
        except Exception:
            continue
        any_ok = True
        for d in items:
            d["panel"] = pname
            if pname != "Stex":
                for k in ("nid", "otp_id"):
                    if d.get(k): d[k] = f"{pname[0].lower()}_{d[k]}"
            allotps.append(d)
    return allotps if any_ok else None

# ==================== WELCOME MESSAGE CONFIGURATION ====================
WELCOME_MESSAGE = """✨ <b>𝗪𝗘𝗟𝗖𝗢𝗠𝗘 𝗧𝗢 𝗧𝗢𝗣 𝗛𝗨𝗕 𝗦𝗠𝗦 𝗥𝗖𝗩 🚀</b> ✨ 
━━━━━━━━━━━━━━━━━━━━━━
🚀 আমাদের নাম্বার বট ব্যবহার করার জন্য ধন্যবাদ 🚀"""


# ==================== OTP RATE CONFIGURATION ====================
OTP_RATE = 0.20

# ==================== REFERRAL / WITHDRAW CONFIGURATION ====================
REFERRAL_PRICE = 0
MIN_WITHDRAW = 50
MAX_WITHDRAW = 10000

# ==================== SUPPORT & DEVELOPER LINKS ====================
SUPPORT_LINK = "https://t.me/itznahidzone"      # আপনার সাপোর্ট লিংক দিন
DEVELOPER_LINK = "https://t.me/itznahidzone"          # আপনার ডেভেলপার লিংক দিন

request_queue = asyncio.Queue()
MAX_WORKERS = max(1, int(os.getenv("MAX_WORKERS", "20")))

client_async = httpx.AsyncClient(
    http2=True,
    timeout=httpx.Timeout(8.0, connect=2.0, read=5.0),
    limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
    trust_env=False,
)

active_numbers = {}
last_range = {}
CHECK_INTERVAL = 1.5
number_assignment_lock = asyncio.Lock()

# ==================== STEX RANGES CACHE ====================
_ranges_cache = {"data": None, "updated_at": 0.0, "fetching": False}

def get_app_emoji_id(app_name):
    n = app_name.lower()
    # Ordered: longer/more-specific names first to avoid partial-match errors
    SERVICE_EMOJI_MAP = [
        ("whatsapp business", "5336814486701514414"),
        ("whatsapp",          "5334759662677957452"),
        ("telegram",          "5337010556253543833"),
        ("facebook",          "5334807341109908955"),
        ("instagram",         "5334868205091459431"),
        ("amazon prime",      "6111801057061374810"),
        ("amazon",            "4995019580536524226"),
        ("imo",               "5337155807752524558"),
        ("apple",             "5334637951894722661"),
        ("google",            "5335010201005231986"),
        ("microsoft",         "5334880948259427772"),
        ("teams",             "5334590977837403844"),
        ("tiktok",            "5339213256001102461"),
        ("bkash",             "5348469219761626211"),
        ("bybit",             "5348372939479751825"),
        ("binance",           "5348212415077064131"),
        ("melbet",            "5337102391244263212"),
        ("snapchat",          "5359441366554255082"),
        ("uber",              "5298715455316303708"),
        ("paypal",            "5776103539872896061"),
        ("discord",           "5116246243646898866"),
        ("viber",             "5463060437572528782"),
        ("linkedin",          "6224222994265279792"),
        ("line",              "5399818044866327279"),
        ("wechat",            "5782757599560602950"),
        ("twitter",           "5215726959056662534"),
        ("reddit",            "4992421103847604984"),
        ("pinterest",         "5346103513120258857"),
        ("twitch",            "5233333563306301418"),
        ("zoom",              "5881799193219043268"),
        ("signal",            "5293998404404272267"),
        ("slack",             "4994972469040251302"),
        ("skype",             "4992613535562334989"),
        ("netflix",           "6255738712664050133"),
        ("spotify",           "5411392711146095115"),
        ("hoichoi",           "6104822598493801746"),
        ("daraz",             "5336879280578138635"),
        ("foodpanda",         "5336879280578138635"),
        ("pathao",            "5336879280578138635"),
        ("aliexpress",        "5336879280578138635"),
        ("shopee",            "5336879280578138635"),
        ("payoneer",          "5336879280578138635"),
        ("wise",              "5336879280578138635"),
        ("chatgpt",           "5296516998996445955"),
        ("notion",            "5336879280578138635"),
        ("github",            "5417836094098007862"),
        ("canva",             "5111661409008092227"),
        ("figma",             "5336879280578138635"),
        ("upwork",            "5336879280578138635"),
        ("fiverr",            "5336879280578138635"),
        ("yahoo",             "5336879280578138635"),
        ("dropbox",           "5336879280578138635"),
        ("coursera",          "5336879280578138635"),
        ("duolingo",          "5336879280578138635"),
        ("rocket",            "5346042941196507141"),
    ]
    _PLACEHOLDER_EMOJI = "5336879280578138635"
    for k, v in SERVICE_EMOJI_MAP:
        if k in n:
            return None if v == _PLACEHOLDER_EMOJI else v
    return "5861680977994060034"

def get_platform_icon(platform_name):
    emoji_id = get_app_emoji_id(platform_name)
    return f'<tg-emoji emoji-id="{emoji_id}">📞</tg-emoji>' if emoji_id else "📞"

def get_clean_app_name(raw):
    n = raw.lower().strip()
    for k, v in [("facebook","Facebook"),("instagram","Instagram"),("whatsapp","WhatsApp"),
                  ("tiktok","TikTok"),("paypal","PayPal"),("telegram","Telegram"),
                  ("discord","Discord"),("imo","Imo")]:
        if k in n: return v
    return raw.strip().capitalize()

def make_bold_text(text):
    out = []
    for ch in str(text):
        o = ord(ch)
        if 65 <= o <= 90:    out.append(chr(o - 65 + 0x1D5D4))
        elif 97 <= o <= 122: out.append(chr(o - 97 + 0x1D5EE))
        elif 48 <= o <= 57:  out.append(chr(o - 48 + 0x1D7EC))
        else: out.append(ch)
    return "".join(out)

async def fetch_top55_ranges_by_app():
    settings = load_settings()
    allowed = {s.lower() for s in settings.get("allowed_services",
        ["Instagram","Facebook","WhatsApp","TikTok","Telegram","Discord","PayPal","Imo"])}
    panels = get_panels()
    ranges_list = None
    for attempt in range(2):
        got, any_ok = [], False
        # Live ranges come from console hits ({sid, range, ...}); liveaccess lists services. Stex + VoltX are merged.
        for pname, pkey, pbase in panels:
            urls, headers = get_api_urls(pbase), get_api_headers(pkey)
            for ep in ("console", "liveaccess"):
                try:
                    r = await client_async.get(urls[ep], headers=headers,
                                                timeout=httpx.Timeout(6.0, connect=2.0))
                    items = extract_active_ranges(r.json())
                except Exception:
                    continue
                if items is not None:
                    any_ok = True
                    got.extend(items)
                    _note_range_panel(items, pname)
        if any_ok:
            ranges_list = got
            break
        if attempt == 0: await asyncio.sleep(0.3)
    if ranges_list is None: return None, "Server unreachable or invalid API key."
    if not ranges_list:     return {}, None
    top = {}
    new_services = []
    for obj in ranges_list:
        if isinstance(obj, str):
            # Some API versions return ranges as strings.  Keep them under
            # the generic service instead of silently dropping them.
            rng = obj.strip()
            service = "Unknown"
        elif isinstance(obj, dict):
            rng = (
                obj.get("range") or obj.get("prefix") or
                obj.get("range_text") or obj.get("value") or ""
            )
            service = (
                obj.get("sid") or obj.get("service") or obj.get("app") or
                obj.get("application") or obj.get("service_name") or "Unknown"
            )
        else:
            continue

        rng = str(rng).strip().upper()
        if not rng or not re.search(r"\d", rng):
            continue
        clean = get_clean_app_name(str(service))
        # Unknown is useful for custom ranges, but configured service filters
        # should still hide unrelated named services.
        if clean.lower() not in allowed and clean != "Unknown":
            if not settings.get("auto_add_services", True):
                continue
            # AUTO ADD: new service found in live data -> allow it automatically
            allowed.add(clean.lower())
            new_services.append(clean)
        if clean not in top:
            top[clean] = {"icon": get_platform_icon(clean), "ranges": []}
        if rng not in top[clean]["ranges"]:
            top[clean]["ranges"].append(rng)
    if new_services:
        try:
            st = load_settings()
            cur = list(st.get("allowed_services", []))
            have = {x.lower() for x in cur}
            for n in new_services:
                if n.lower() not in have:
                    cur.append(n); have.add(n.lower())
            st["allowed_services"] = cur
            save_settings(st)
        except Exception as exc:
            print(f"Auto add services failed: {exc}")
    return dict(sorted(top.items(), key=lambda x: len(x[1]["ranges"]), reverse=True)), None


def extract_active_ranges(payload):
    """Read active ranges from all supported API response shapes."""
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return None

    # === VOLTX API SPECIFIC PARSING ===
    data = payload.get("data")
    if isinstance(data, dict):
        # 1. /liveaccess response (data.services)
        if "services" in data and isinstance(data["services"], list):
            grouped = []
            for svc in data["services"]:
                sid = svc.get("sid", "Unknown")
                for rng in svc.get("ranges", []):
                    grouped.append({"service": sid, "range": rng})
            if grouped: return grouped
            
        # 2. /console response (data.hits)
        if "hits" in data and isinstance(data["hits"], list):
            return data["hits"]

    # === STEX / GENERAL API PARSING ===
    for key in (
        "active_ranges", "activeRanges", "available_ranges",
        "availableRanges", "ranges", "range_list",
    ):
        value = payload.get(key)
        if isinstance(value, list):
            return value

    # Newer responses may wrap the same object in data/result/response.
    for key in ("data", "result", "response", "payload"):
        value = payload.get(key)
        if isinstance(value, (dict, list)):
            nested = extract_active_ranges(value)
            if nested is not None:
                return nested

    # A few versions return {"WhatsApp": ["880XXX", ...]}.
    grouped = []
    for service, values in payload.items():
        if not isinstance(values, list):
            continue
        for value in values:
            if isinstance(value, dict):
                item = dict(value)
                item.setdefault("service", service)
            else:
                item = {"service": service, "range": value}
            grouped.append(item)
    return grouped if grouped else None

def build_app_buttons_from_cache(top):
    btns, row, ci = [], [], 0
    clrs = ["primary", "success", "danger"]
    for app_name in top:
        button_kwargs = {"style": clrs[ci % len(clrs)]}
        emoji_id = get_app_emoji_id(app_name)
        if emoji_id:
            button_kwargs["icon_custom_emoji_id"] = emoji_id
        row.append(InlineKeyboardButton(f"📱 {make_bold_text(app_name)}",
            callback_data=f"sel_app_{app_name}", api_kwargs=button_kwargs))
        ci += 1
        if len(row) == 2: btns.append(row); row = []
    if row: btns.append(row)
    return btns

async def _bg_refresh_ranges():
    global _ranges_cache
    while True:
        try:
            if not _ranges_cache["fetching"]:
                _ranges_cache["fetching"] = True
                try:
                    data, _ = await fetch_top55_ranges_by_app()
                    if data:
                        _ranges_cache["data"] = data
                        _ranges_cache["updated_at"] = time.monotonic()
                except Exception: pass
                finally: _ranges_cache["fetching"] = False
        except Exception: pass
        await asyncio.sleep(200)

# ==================== CHECK IF USER IS ADMIN ====================

def is_admin(user_id):
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        return False
    return user_id in get_admin_ids()

def get_admin_ids():
    """Return valid admin IDs, even if settings.json stored them as strings."""
    candidates = [ADMIN_ID, CONFIG_ADMIN_ID]
    try:
        configured = load_settings().get("admins", [])
        if isinstance(configured, list):
            candidates.extend(configured)
    except Exception as exc:
        print(f"Support admin settings could not be loaded: {exc}")

    admin_ids = []
    for candidate in candidates:
        try:
            admin_id = int(candidate)
        except (TypeError, ValueError):
            continue
        if admin_id > 0 and admin_id not in admin_ids:
            admin_ids.append(admin_id)
    return admin_ids

def get_min_withdraw():
    """Read the current minimum withdrawal from persisted bot settings."""
    try:
        return max(0.0, float(load_settings().get("min_withdraw", MIN_WITHDRAW)))
    except (TypeError, ValueError):
        return float(MIN_WITHDRAW)

# ==================== WITHDRAW DATA FUNCTIONS ====================

def load_withdraw_requests():
    if not os.path.exists(WITHDRAW_DATA_FILE):
        with open(WITHDRAW_DATA_FILE, "w") as f:
            json.dump({}, f)
        return {}
    try:
        with open(WITHDRAW_DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_withdraw_requests(data):
    with open(WITHDRAW_DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def generate_payment_id():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))

# ==================== BANNED USERS FUNCTIONS ====================

def load_banned_users():
    if not os.path.exists(BANNED_USERS_FILE):
        with open(BANNED_USERS_FILE, "w") as f:
            json.dump([], f)
        return []
    try:
        with open(BANNED_USERS_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_banned_users(banned_list):
    with open(BANNED_USERS_FILE, "w") as f:
        json.dump(banned_list, f, indent=4)

def is_user_banned(uid):
    banned_list = load_banned_users()
    return str(uid) in banned_list

def ban_user(uid):
    banned_list = load_banned_users()
    uid_str = str(uid)
    if uid_str not in banned_list:
        banned_list.append(uid_str)
        save_banned_users(banned_list)
        return True
    return False

def unban_user(uid):
    banned_list = load_banned_users()
    uid_str = str(uid)
    if uid_str in banned_list:
        banned_list.remove(uid_str)
        save_banned_users(banned_list)
        return True
    return False

# ==================== REFERRAL DATA FUNCTIONS ====================

def load_referral_data():
    if not os.path.exists(REFERRAL_DATA_FILE):
        with open(REFERRAL_DATA_FILE, "w") as f:
            json.dump({}, f)
        return {}
    try:
        with open(REFERRAL_DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_referral_data(data):
    with open(REFERRAL_DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def update_referral_count(uid, count):
    referral_data = load_referral_data()
    uid_str = str(uid)
    if uid_str not in referral_data:
        referral_data[uid_str] = {"referral_count": 0}
    referral_data[uid_str]["referral_count"] = count
    save_referral_data(referral_data)

def get_referral_count(uid):
    referral_data = load_referral_data()
    uid_str = str(uid)
    return referral_data.get(uid_str, {}).get("referral_count", 0)

# ==================== DATA RANGE FILE ====================

def load_range_db():
    if not os.path.exists(DATA_RANGE_FILE):
        return {}
    try:
        with open(DATA_RANGE_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_range_db(data):
    with open(DATA_RANGE_FILE, "w") as f:
        json.dump(data, f, indent=4)

def save_number_range_info(uid, number, range_text):
    db = load_range_db()
    flag, name = get_country_info(number)
    db[normalize_number(number)] = {
        "user_id": str(uid),
        "number": f"+{normalize_number(number)}",
        "range": range_text,
        "country": f"{flag} {name}"
    }
    save_range_db(db)

# ==================== COUNTRY MAPPING SECTION ====================

def get_country_info(number):
    number = str(number).strip()

    country_map = {
        "2376": ("🇨🇲", "Cameroon"),
        "2250": ("🇨🇮", "Ivory Coast"),
        "2613": ("🇲🇬", "Madagascar"),
        "4077": ("🇷🇴", "Romania"),
        "237": ("🇨🇲", "Cameroon"),
        "225": ("🇨🇮", "Ivory Coast"),
        "261": ("🇲🇬", "Madagascar"),
        "20": ("🇪🇬", "Egypt"),
        "27": ("🇿🇦", "South Africa"),
        "234": ("🇳🇬", "Nigeria"),
        "254": ("🇰🇪", "Kenya"),
        "233": ("🇬🇭", "Ghana"),
        "212": ("🇲🇦", "Morocco"),
        "213": ("🇩🇿", "Algeria"),
        "216": ("🇹🇳", "Tunisia"),
        "218": ("🇱🇾", "Libya"),
        "249": ("🇸🇩", "Sudan"),
        "251": ("🇪🇹", "Ethiopia"),
        "252": ("🇸🇴", "Somalia"),
        "253": ("🇩🇯", "Djibouti"),
        "255": ("🇹🇿", "Tanzania"),
        "256": ("🇺🇬", "Uganda"),
        "257": ("🇧🇮", "Burundi"),
        "258": ("🇲🇿", "Mozambique"),
        "260": ("🇿🇲", "Zambia"),
        "263": ("🇿🇼", "Zimbabwe"),
        "264": ("🇳🇦", "Namibia"),
        "265": ("🇲🇼", "Malawi"),
        "266": ("🇱🇸", "Lesotho"),
        "267": ("🇧🇼", "Botswana"),
        "268": ("🇸🇿", "Swaziland"),
        "269": ("🇰🇲", "Comoros"),
        "220": ("🇬🇲", "Gambia"),
        "221": ("🇸🇳", "Senegal"),
        "222": ("🇲🇷", "Mauritania"),
        "223": ("🇲🇱", "Mali"),
        "224": ("🇬🇳", "Guinea"),
        "226": ("🇧🇫", "Burkina Faso"),
        "227": ("🇳🇪", "Niger"),
        "228": ("🇹🇬", "Togo"),
        "229": ("🇧🇯", "Benin"),
        "230": ("🇲🇺", "Mauritius"),
        "231": ("🇱🇷", "Liberia"),
        "232": ("🇸🇱", "Sierra Leone"),
        "235": ("🇹🇩", "Chad"),
        "236": ("🇨🇫", "Central African Republic"),
        "238": ("🇨🇻", "Cape Verde"),
        "239": ("🇸🇹", "Sao Tome and Principe"),
        "240": ("🇬🇶", "Equatorial Guinea"),
        "241": ("🇬🇦", "Gabon"),
        "242": ("🇨🇬", "Congo"),
        "243": ("🇨🇩", "DR Congo"),
        "244": ("🇦🇴", "Angola"),
        "245": ("🇬🇼", "Guinea-Bissau"),
        "247": ("🇸🇭", "Saint Helena"),
        "248": ("🇸🇨", "Seychelles"),
        "250": ("🇷🇼", "Rwanda"),
        "290": ("🇸🇭", "Saint Helena"),
        "291": ("🇪🇷", "Eritrea"),
        "40": ("🇷🇴", "Romania"),
        "44": ("🇬🇧", "United Kingdom"),
        "33": ("🇫🇷", "France"),
        "49": ("🇩🇪", "Germany"),
        "39": ("🇮🇹", "Italy"),
        "34": ("🇪🇸", "Spain"),
        "31": ("🇳🇱", "Netherlands"),
        "32": ("🇧🇪", "Belgium"),
        "41": ("🇨🇭", "Switzerland"),
        "43": ("🇦🇹", "Austria"),
        "46": ("🇸🇪", "Sweden"),
        "47": ("🇳🇴", "Norway"),
        "45": ("🇩🇰", "Denmark"),
        "358": ("🇫🇮", "Finland"),
        "351": ("🇵🇹", "Portugal"),
        "353": ("🇮🇪", "Ireland"),
        "36": ("🇭🇺", "Hungary"),
        "48": ("🇵🇱", "Poland"),
        "380": ("🇺🇦", "Ukraine"),
        "370": ("🇱🇹", "Lithuania"),
        "371": ("🇱🇻", "Latvia"),
        "372": ("🇪🇪", "Estonia"),
        "373": ("🇲🇩", "Moldova"),
        "374": ("🇦🇲", "Armenia"),
        "375": ("🇧🇾", "Belarus"),
        "376": ("🇦🇩", "Andorra"),
        "377": ("🇲🇨", "Monaco"),
        "381": ("🇷🇸", "Serbia"),
        "382": ("🇲🇪", "Montenegro"),
        "385": ("🇭🇷", "Croatia"),
        "386": ("🇸🇮", "Slovenia"),
        "387": ("🇧🇦", "Bosnia and Herzegovina"),
        "389": ("🇲🇰", "North Macedonia"),
        "350": ("🇬🇮", "Gibraltar"),
        "352": ("🇱🇺", "Luxembourg"),
        "354": ("🇮🇸", "Iceland"),
        "355": ("🇦🇱", "Albania"),
        "356": ("🇲🇹", "Malta"),
        "357": ("🇨🇾", "Cyprus"),
        "359": ("🇧🇬", "Bulgaria"),
        "421": ("🇸🇰", "Slovakia"),
        "420": ("🇨🇿", "Czech Republic"),
        "298": ("🇫🇴", "Faroe Islands"),
        "299": ("🇬🇱", "Greenland"),
        "1": ("🇺🇸", "United States"),
        "7": ("🇷🇺", "Russia"),
        "91": ("🇮🇳", "India"),
        "92": ("🇵🇰", "Pakistan"),
        "880": ("🇧🇩", "Bangladesh"),
        "86": ("🇨🇳", "China"),
        "81": ("🇯🇵", "Japan"),
        "82": ("🇰🇷", "South Korea"),
        "84": ("🇻🇳", "Vietnam"),
        "66": ("🇹🇭", "Thailand"),
        "62": ("🇮🇩", "Indonesia"),
        "60": ("🇲🇾", "Malaysia"),
        "65": ("🇸🇬", "Singapore"),
        "63": ("🇵🇭", "Philippines"),
        "95": ("🇲🇲", "Myanmar"),
        "94": ("🇱🇰", "Sri Lanka"),
        "977": ("🇳🇵", "Nepal"),
        "93": ("🇦🇫", "Afghanistan"),
        "98": ("🇮🇷", "Iran"),
        "90": ("🇹🇷", "Turkey"),
        "964": ("🇮🇶", "Iraq"),
        "963": ("🇸🇾", "Syria"),
        "961": ("🇱🇧", "Lebanon"),
        "962": ("🇯🇴", "Jordan"),
        "965": ("🇰🇼", "Kuwait"),
        "966": ("🇸🇦", "Saudi Arabia"),
        "967": ("🇾🇲", "Yemen"),
        "968": ("🇴🇲", "Oman"),
        "971": ("🇦🇪", "United Arab Emirates"),
        "972": ("🇮🇱", "Israel"),
        "973": ("🇧🇭", "Bahrain"),
        "974": ("🇶🇦", "Qatar"),
        "994": ("🇦🇿", "Azerbaijan"),
        "995": ("🇬🇪", "Georgia"),
        "996": ("🇰🇬", "Kyrgyzstan"),
        "992": ("🇹🇯", "Tajikistan"),
        "993": ("🇹🇲", "Turkmenistan"),
        "998": ("🇺🇿", "Uzbekistan"),
        "855": ("🇰🇭", "Cambodia"),
        "856": ("🇱🇦", "Laos"),
        "976": ("🇲🇳", "Mongolia"),
        "850": ("🇰🇵", "North Korea"),
        "55": ("🇧🇷", "Brazil"),
        "52": ("🇲🇽", "Mexico"),
        "54": ("🇦🇷", "Argentina"),
        "57": ("🇨🇴", "Colombia"),
        "51": ("🇵🇪", "Peru"),
        "58": ("🇻🇪", "Venezuela"),
        "56": ("🇨🇱", "Chile"),
        "593": ("🇪🇨", "Ecuador"),
        "591": ("🇧🇴", "Bolivia"),
        "595": ("🇵🇾", "Paraguay"),
        "598": ("🇺🇾", "Uruguay"),
        "502": ("🇬🇹", "Guatemala"),
        "503": ("🇸🇻", "El Salvador"),
        "504": ("🇭🇳", "Honduras"),
        "506": ("🇨🇷", "Costa Rica"),
        "507": ("🇵🇦", "Panama"),
        "509": ("🇭🇹", "Haiti"),
        "501": ("🇧🇿", "Belize"),
        "61": ("🇦🇺", "Australia"),
        "64": ("🇳🇿", "New Zealand"),
        "675": ("🇵🇬", "Papua New Guinea"),
        "679": ("🇫🇯", "Fiji"),
        "1246": ("🇧🇧", "Barbados"),
        "1876": ("🇯🇲", "Jamaica"),
        "53": ("🇨🇺", "Cuba"),
        "592": ("🇬🇾", "Guyana"),
    }

    clean_num = str(number).replace('+', '').replace(' ', '').replace('-', '').strip()
    sorted_prefixes = sorted(country_map.keys(), key=len, reverse=True)

    for prefix in sorted_prefixes:
        if clean_num.startswith(prefix):
            return country_map[prefix]

    return ("🌍", "Unknown")

# ==================== SERVICE DETECTION SECTION ====================

def detect_service(full_sms):
    if not full_sms:
        return "SMS SERVICE"

    sms_lower = full_sms.lower()

    service_keywords = {
        "facebook": "FACEBOOK", "fb": "FACEBOOK",
        "instagram": "INSTAGRAM", "insta": "INSTAGRAM",
        "tiktok": "TIKTOK",
        "twitter": "TWITTER", "x.com": "TWITTER",
        "snapchat": "SNAPCHAT", "snap": "SNAPCHAT",
        "whatsapp": "WHATSAPP",
        "telegram": "TELEGRAM",
        "discord": "DISCORD",
        "messenger": "MESSENGER",
        "linkedin": "LINKEDIN",
        "google": "GOOGLE", "gmail": "GOOGLE",
        "amazon": "AMAZON",
        "microsoft": "MICROSOFT", "outlook": "MICROSOFT",
        "yahoo": "YAHOO",
        "paypal": "PAYPAL",
        "binance": "BINANCE",
        "coinbase": "COINBASE",
        "spotify": "SPOTIFY",
        "netflix": "NETFLIX",
        "uber": "UBER",
        "apple": "APPLE", "icloud": "APPLE",
        "bkash": "BKASH",
        "nagad": "NAGAD",
        "stripe": "STRIPE",
        "line": "LINE",
        "wechat": "WECHAT",
        "viber": "VIBER",
        "signal": "SIGNAL",
        "pubg": "PUBG",
        "free fire": "FREE FIRE",
    }

    for keyword, service_name in sorted(service_keywords.items(), key=lambda x: len(x[0]), reverse=True):
        if keyword in sms_lower:
            return service_name

    return "SMS SERVICE"

# ==================== KEYBOARDS SECTION ====================
# Main user menu keyboard

from telegram import KeyboardButton, ReplyKeyboardMarkup

def make_reply_btn(text, emoji_id=None, style=None):
    api_kwargs = {}
    if emoji_id:
        api_kwargs['icon_custom_emoji_id'] = str(emoji_id)
    if style:
        api_kwargs['style'] = style
    return KeyboardButton(
        text=text,
        api_kwargs=api_kwargs if api_kwargs else None
    )

def main_keyboard(user_id):
    keyboard = [
        [
            make_reply_btn("📞 GET NUMBER",     emoji_id="5228843986747147814", style="success"),
            make_reply_btn("🔑 GET 2FA",        emoji_id="5296369303661067030", style="primary")
        ],
        [
            make_reply_btn("👤 PROFILE",        emoji_id="5422444280473998663", style="primary"),
            make_reply_btn("🏆 LEADERBOARD",    emoji_id="5228875876879318811", style="danger")
        ],
        [
            make_reply_btn("📊 LIVE TRAFFIC",   emoji_id="5355102594886833928", style="success"),
            make_reply_btn("💬 SUPPORT",        emoji_id="5267294466716244344", style="danger")
        ],
    ]

    if is_admin(user_id):
        keyboard.append([
            make_reply_btn("👑 ADMIN PANEL", emoji_id="5350396951407895212", style="primary")
        ])

    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def account_keyboard():
    """Keyboard for account-related actions grouped under one main-menu button."""
    keyboard = [
        [
            make_reply_btn("💰 BALANCE",        emoji_id="6233367447789899509", style="success"),
            make_reply_btn("🎁 REFER AND EARN", emoji_id="5420396762189831222", style="primary")
        ],
        [
            make_reply_btn("👤 VIEW PROFILE",   emoji_id="5422444280473998663", style="primary")
            ,make_reply_btn("🔙 BACK TO MAIN",  emoji_id="5267490665117275176", style="danger")
        ],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def cancel_keyboard():
    keyboard = [[make_reply_btn("❌ CANCEL", emoji_id="5420130255174145507", style="danger")]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def admin_main_keyboard():
    keyboard = [
        [make_reply_btn("👥 USER MANAGEMENT",      emoji_id="5193063022226086560", style="primary"),
         make_reply_btn("⚙️ SYSTEM CONFIGURATION", emoji_id="5341715473882955310", style="success")],
        [make_reply_btn("🤖 BOT SETTINGS",         emoji_id="5282843764451195532", style="primary"),
         make_reply_btn("🛠️ SERVICE MANAGEMENT",   emoji_id="5375338737028841420", style="success")],
        [make_reply_btn("💸 WITHDRAWAL MANAGEMENT", emoji_id="6233367447789899509", style="danger"),
         make_reply_btn("💬 SUPPORT CHAT",           emoji_id="5267294466716244344", style="primary")],
        [make_reply_btn("⏳ PENDING WITHDRAWALS", emoji_id="6217721388736712699", style="danger")],
        [make_reply_btn("🔙 BACK TO MAIN",         emoji_id="5267490665117275176", style="primary")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def user_management_keyboard():
    keyboard = [
        [make_reply_btn("📢 SEND MESSAGE TO ALL USERS", emoji_id="5251671733630431622", style="primary"),
         make_reply_btn("🆔 ALL USER ID",               emoji_id="5352861489541714456", style="success")],
        [make_reply_btn("🚫 BAN USER LIST",             emoji_id="5420323339723881652", style="danger"),
         make_reply_btn("💰 ALL USER BALANCE",          emoji_id="6233367447789899509", style="primary")],
        [make_reply_btn("🔙 BACK TO ADMIN",             emoji_id="5267490665117275176", style="danger")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def system_config_keyboard():
    keyboard = [
        [make_reply_btn("📊 TODAY ALL STATUS",  emoji_id="5231200819986047254", style="primary"),
         make_reply_btn("🔍 USER STATUS CHECK", emoji_id="5352861489541714456", style="success")],
        [make_reply_btn("🚫 BAN USER",          emoji_id="5420323339723881652", style="danger"),
         make_reply_btn("✅ UNBAN USER",        emoji_id="5875017993909440887", style="success")],
        [make_reply_btn("📜 BAN USER LIST",     emoji_id="5956074558044770726", style="danger"),
         make_reply_btn("➖ REMOVE BALANCE",    emoji_id="5244837092042750681", style="danger")],
        [make_reply_btn("➕ ADD BALANCE",       emoji_id="5397916757333654639", style="success"),
         make_reply_btn("🔙 BACK TO ADMIN",     emoji_id="5267490665117275176", style="primary")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def bot_settings_keyboard():
    keyboard = [
        [make_reply_btn("➕ ADD ADMIN",          emoji_id="5397916757333654639", style="success"),
         make_reply_btn("➖ REMOVE ADMIN",       emoji_id="5244837092042750681", style="danger")],
        [make_reply_btn("🔗 SET OTP GROUP LINK", emoji_id="5253742260054409879", style="primary"),
         make_reply_btn("📢 FORCE JOIN SYSTEM", emoji_id="5282843764451195532", style="success")],
        [make_reply_btn("🆔 SET OTP CHAT ID",    emoji_id="5231200819986047254", style="primary"),
         make_reply_btn("⚙️ STEX CONFIG",       emoji_id="5350396951407895212", style="success")],
        [make_reply_btn("🔢 SET NUMBER COUNT",   emoji_id="5341715473882955310", style="primary")],
        [make_reply_btn("🔙 BACK TO ADMIN",      emoji_id="5267490665117275176", style="danger")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def stex_config_keyboard():
    keyboard = [
        [make_reply_btn("🔑 SET API KEY",          emoji_id="5397916757333654639", style="primary"),
         make_reply_btn("🌐 SET BASE URL",         emoji_id="5253742260054409879", style="success")],
        [make_reply_btn("📋 SET ALLOWED SERVICES", emoji_id="5341715473882955310", style="primary"),
         make_reply_btn("📊 VIEW STEX CONFIG",    emoji_id="5231200819986047254", style="success")],
        [make_reply_btn("🔑 SET VOLT KEY",         emoji_id="5397916757333654639", style="success"),
         make_reply_btn("🌐 SET VOLT URL",         emoji_id="5253742260054409879", style="primary")],
        [make_reply_btn("⚡ VOLT PANEL: " + ("ON" if load_settings().get("volt_enabled", True) else "OFF"),
                        emoji_id="5341715473882955310", style="success" if load_settings().get("volt_enabled", True) else "danger")],
        [make_reply_btn("🔄 AUTO ADD SERVICES: " + ("ON" if load_settings().get("auto_add_services", True) else "OFF"),
                        emoji_id="5341715473882955310", style="primary")],
        [make_reply_btn("🔙 BACK TO BOT SETTINGS", emoji_id="5267490665117275176", style="danger")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def service_management_keyboard():
    keyboard = [
        [make_reply_btn("➕ ADD SERVICE",    emoji_id="5397916757333654639", style="success"),
         make_reply_btn("➖ REMOVE SERVICE", emoji_id="5244837092042750681", style="danger")],
        [make_reply_btn("📋 LIST SERVICES",  emoji_id="5352861489541714456", style="primary"),
         make_reply_btn("🔙 BACK TO ADMIN",  emoji_id="5267490665117275176", style="danger")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def withdrawal_management_keyboard():
    keyboard = [
        [
            make_reply_btn("⏳ PENDING WITHDRAWALS", emoji_id="6217721388736712699", style="primary"),
            make_reply_btn("📉 SET MINIMUM WITHDRAW", emoji_id="5397916757333654639", style="success"),
        ],
        [
            make_reply_btn("🔙 BACK TO ADMIN", emoji_id="5267490665117275176", style="danger"),
        ],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def withdraw_method_keyboard():
    keyboard = ReplyKeyboardMarkup([
        [make_reply_btn("💳 BKASH",  emoji_id="5348469219761626211", style="primary"),
         make_reply_btn("💳 NAGAD",  emoji_id="5352985330628730418", style="success")],
        [make_reply_btn("🚀 ROCKET", emoji_id="5346042941196507141", style="danger"),
         make_reply_btn("🟡 BINANCE",emoji_id="5348212415077064131", style="primary")],
        [make_reply_btn("❌ CANCEL", emoji_id="5420130255174145507", style="danger")]
    ], resize_keyboard=True)
    return keyboard

# ==================== HELPER FUNCTIONS SECTION ====================

def format_balance(balance):
    return f"{balance:.2f}"

def extract_otp(text):
    if not text or text == "No Content":
        return "N/A"
    spaced_otp = re.search(r'\b(\d{3}[\s\-]\d{3})\b', text)      # "123 456" and WhatsApp style "123-456"
    if spaced_otp:
        return re.sub(r"[\s\-]", "", spaced_otp.group(1))
    match = re.search(r'\b(\d{4,8})\b', text)
    return match.group(1) if match else "N/A"

def normalize_number(num):
    return re.sub(r'\D', '', str(num))

def mask_number(num):
    if len(num) > 6:
        return f"{num[:4]}****{num[-6:]}"
    return num

def get_date_reset_time():
    now = datetime.now()
    today_midnight = datetime(now.year, now.month, now.day, 0, 0, 0)
    return today_midnight

def is_valid_bangladesh_number(number):
    number = re.sub(r'\D', '', str(number))
    return len(number) == 11 and number.startswith('01')

def is_range_request(param):
    return 'X' in param.upper()

def is_referral_request(param):
    return param.isdigit()

# ==================== DATABASE FUNCTIONS SECTION ====================

def load_data(filename=USER_DATA_FILE):
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            json.dump({}, f)
        return {}
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data, filename=USER_DATA_FILE):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

def get_user(uid):
    uid = str(uid)
    data = load_data()
    if uid not in data:
        data[uid] = {"user_id": uid, "balance": 0.0, "total_numbers": 0, "referral_count": 0}
        save_data(data)
    return data[uid]

async def update_db_balance(uid, amount):
    uid = str(uid)
    data = load_data()
    if uid in data:
        data[uid]["balance"] = round(data[uid].get("balance", 0.0) + amount, 2)
        save_data(data)
        return data[uid]["balance"]
    return 0.0

def get_all_users():
    data = load_data(USER_DATA_FILE)
    return list(data.keys()) if data else []

def user_exists(uid):
    data = load_data(USER_DATA_FILE)
    return str(uid) in data

# ==================== STATS FUNCTIONS SECTION ====================

def load_stats():
    if not os.path.exists(STATS_FILE):
        with open(STATS_FILE, "w") as f:
            json.dump({}, f)
        return {}
    try:
        with open(STATS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_stats(stats):
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=4)

def add_number_taken(uid, count=1, service=None, country=None):
    uid = str(uid)
    stats = load_stats()
    if uid not in stats:
        stats[uid] = {"numbers_taken": [], "otps_received": []}
    now = datetime.now().isoformat()
    for _ in range(count):
        stats[uid]["numbers_taken"].append(now)
    activity_details = {"count": count}
    if service:
        activity_details["service"] = str(service)
    if country:
        activity_details["country"] = str(country)
    log_global_activity(uid, "NUMBER_TAKEN", activity_details)
    save_stats(stats)

def add_otp_received(uid):
    uid = str(uid)
    stats = load_stats()
    if uid not in stats:
        stats[uid] = {"numbers_taken": [], "otps_received": []}
    stats[uid]["otps_received"].append(datetime.now().isoformat())
    save_stats(stats)

def get_user_stats(uid):
    uid = str(uid)
    stats = load_stats()
    user_stats = stats.get(uid, {"numbers_taken": [], "otps_received": []})

    now = datetime.now()
    today_midnight = get_date_reset_time()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)

    numbers_taken = user_stats.get("numbers_taken", [])
    otps_received = user_stats.get("otps_received", [])

    today_numbers = sum(1 for t in numbers_taken if datetime.fromisoformat(t) >= today_midnight)
    today_otps = sum(1 for t in otps_received if datetime.fromisoformat(t) >= today_midnight)
    last24h_numbers = sum(1 for t in numbers_taken if datetime.fromisoformat(t) > last_24h)
    last24h_otps = sum(1 for t in otps_received if datetime.fromisoformat(t) > last_24h)
    last7d_numbers = sum(1 for t in numbers_taken if datetime.fromisoformat(t) > last_7d)
    last7d_otps = sum(1 for t in otps_received if datetime.fromisoformat(t) > last_7d)
    total_numbers = len(numbers_taken)
    total_otps = len(otps_received)

    return {
        "total_numbers": total_numbers, "total_otps": total_otps,
        "today_numbers": today_numbers, "today_otps": today_otps,
        "last24h_numbers": last24h_numbers, "last24h_otps": last24h_otps,
        "last7d_numbers": last7d_numbers, "last7d_otps": last7d_otps
    }

def log_global_activity(uid, action, details):
    if not os.path.exists(ACTIVITY_LOGS_FILE):
        with open(ACTIVITY_LOGS_FILE, "w") as f:
            json.dump([], f)
    try:
        with open(ACTIVITY_LOGS_FILE, "r") as f:
            logs = json.load(f)
    except:
        logs = []
    now = datetime.now()
    logs.append({
        "uid": str(uid), "action": action, "details": details,
        "timestamp": now.isoformat(),
        "date": now.strftime("%d/%m/%Y"),
        "time": now.strftime("%H:%M:%S")
    })
    with open(ACTIVITY_LOGS_FILE, "w") as f:
        json.dump(logs, f, indent=4)

def get_global_system_stats():
    stats = load_stats()
    now = datetime.now()
    today_midnight = datetime(now.year, now.month, now.day)
    last_7d = now - timedelta(days=7)
    total_n = total_o = today_n = today_o = seven_n = seven_o = 0
    for uid in stats:
        u = stats[uid]
        n_list = u.get("numbers_taken", [])
        o_list = u.get("otps_received", [])
        total_n += len(n_list)
        total_o += len(o_list)
        for t in n_list:
            dt = datetime.fromisoformat(t)
            if dt >= today_midnight: today_n += 1
            if dt >= last_7d: seven_n += 1
        for t in o_list:
            dt = datetime.fromisoformat(t)
            if dt >= today_midnight: today_o += 1
            if dt >= last_7d: seven_o += 1
    return today_n, today_o, seven_n, seven_o, total_n, total_o

# ==================== LEADERBOARD SECTION ====================

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_user_banned(uid):
        await update.message.reply_text("🚫 YOU ARE BANNED 🚫", reply_markup=main_keyboard(uid))
        return

    stats_data = load_stats()
    today_midnight = get_date_reset_time()
    user_data_all = load_data(USER_DATA_FILE)

    user_today_counts = []

    for uid_str, user_stats in stats_data.items():
        otps_received = user_stats.get("otps_received", [])
        today_count = 0
        for ts in otps_received:
            try:
                dt = datetime.fromisoformat(ts)
                if dt >= today_midnight:
                    today_count += 1
            except:
                continue
        if today_count > 0:
            name = user_data_all.get(uid_str, {}).get("full_name")
            if not name:
                name = user_data_all.get(uid_str, {}).get("username")
            if not name:
                name = f"User {uid_str}"
            user_today_counts.append((uid_str, today_count, html.escape(name)))

    user_today_counts.sort(key=lambda x: x[1], reverse=True)
    top10 = user_today_counts[:10]

    if not top10:
        msg = (
            "<b>🏆 TOP 10 OTP LEADERBOARD 🏆</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "❌ আজ পর্যন্ত কেউ OTP পায়নি।\n"
        )
    else:
        msg = (
            "<b>🏆 TOP 10 OTP RECEIVERS (TODAY) 🏆</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
        )
        for idx, (uid_str, count, name) in enumerate(top10, 1):
            if idx == 1:
                medal = "🥇"
            elif idx == 2:
                medal = "🥈"
            elif idx == 3:
                medal = "🥉"
            else:
                medal = f"{idx}️⃣"
            msg += f"{medal} <b>{name}</b>\n   🔑 <code>{count}</code> OTPs\n\n"
        msg += (
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📊 <i>প্রতিদিন রাত ১২টায় রিসেট হয়</i>"
        )

    await update.message.reply_text(msg, parse_mode="HTML", reply_markup=main_keyboard(uid))

# ==================== 2FA CODE GENERATOR SECTION ====================

def generate_2fa_code(secret_key):
    try:
        clean_secret = secret_key.replace(" ", "").upper().strip()
        key = base64.b32decode(clean_secret, casefold=True)
        t = int(time.time()) // 30
        msg_bytes = struct.pack(">Q", t)
        h = hmac.new(key, msg_bytes, hashlib.sha1).digest()
        o = h[-1] & 0xf
        code = (struct.unpack(">I", h[o:o+4])[0] & 0x7fffffff) % 1_000_000
        return f"{code:06d}", clean_secret
    except:
        return None, None

async def get_2fa_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_user_banned(uid):
        await update.message.reply_text("🚫 YOU ARE BANNED 🚫", reply_markup=main_keyboard(uid))
        return
    context.user_data["mode"] = "get_2fa"
    await update.message.reply_text(
        "╭━━━〔 ⚡ <b>𝗚𝗘𝗧 𝟮𝗙𝗔 𝗖𝗢𝗗𝗘</b> ⚡ 〕━━━╮\n\n"
        "<blockquote>🔑 <b>ENTER YOUR 2FA SECRET KEY:</b></blockquote>",
        parse_mode="HTML"
    )

async def process_2fa_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    secret_key = update.message.text.strip()
    context.user_data["mode"] = None

    otp_code, clean_key = generate_2fa_code(secret_key)

    if otp_code is None:
        await update.message.reply_text(
            "❌ <b>INVALID 2FA SECRET KEY</b>\n\n⚠️ Please send a valid base32 key.",
            parse_mode="HTML",
            reply_markup=main_keyboard(uid)
        )
        return

    now = datetime.now()
    final_msg = (
        f"╭━━━〔 ✅ <b>𝟮𝗙𝗔 𝗖𝗢𝗗𝗘 𝗚𝗘𝗡𝗘𝗥𝗔𝗧𝗘𝗗</b> ✅ 〕━━━╮\n"
        f"┃ 🔑 <b>Key:</b> <code>{clean_key}</code>\n"
        f"┃ 🔢 <b>Code:</b> <code>{otp_code}</code>\n"
        f"╰━━━━━━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
        f"<blockquote>⏳ <b>Expires in:</b> 30 Seconds\n"
        f"📅 {now.strftime('%d %B, %Y')} | {now.strftime('%I:%M %p')}</blockquote>"
    )
    await update.message.reply_text(final_msg, parse_mode="HTML")


def build_manual_service_buttons():
    """Build inline buttons for manually added services."""
    s = load_settings()
    manual = s.get("manual_services", [])
    btns = []
    clrs = ["primary", "success", "danger"]
    for i, svc in enumerate(manual):
        button_kwargs = {"style": clrs[i % len(clrs)]}
        emoji_id = get_app_emoji_id(svc['name'])
        if emoji_id:
            button_kwargs["icon_custom_emoji_id"] = emoji_id
        btns.append(InlineKeyboardButton(
            f"🔧 {make_bold_text(svc['name'])}",
            callback_data=f"manual_svc_{i}",
            api_kwargs=button_kwargs
        ))
    rows = [btns[j:j+2] for j in range(0, len(btns), 2)]
    return rows

async def show_app_selection(update, context):
    uid = update.effective_user.id
    if is_user_banned(uid):
        await update.message.reply_text("🚫 YOU ARE BANNED 🚫", reply_markup=main_keyboard(uid))
        return
    context.user_data.pop("top_ranges_by_app", None)

    # Build combined keyboard: Stex apps + manual services
    async def _build_full_keyboard(top):
        stex_rows = build_app_buttons_from_cache(top)
        manual_rows = build_manual_service_buttons()
        all_rows = stex_rows + manual_rows
        if not all_rows:
            all_rows = []
        all_rows.append([InlineKeyboardButton("⚙️ CUSTOM RANGE", callback_data="custom_range",
                                               api_kwargs={"style": "danger"})])
        return all_rows

    cache_age = time.monotonic() - _ranges_cache["updated_at"]
    if _ranges_cache["data"] and cache_age < 300:
        top = _ranges_cache["data"]
        context.user_data["top_ranges_by_app"] = top
        msg = f'╭━━━〔 📞 <b>𝗦𝗘𝗟𝗘𝗖𝗧 𝗔𝗣𝗣</b> 〕━━━╮\n<blockquote>Select an app to get numbers</blockquote>'
        kb = await _build_full_keyboard(top)
        await update.message.reply_text(msg, parse_mode="HTML",
                                         reply_markup=InlineKeyboardMarkup(kb))
        return
    status = await update.message.reply_text(
        f'{get_tg_emoji("loading")} <b>Loading ranges...</b>', parse_mode="HTML")
    top, err = await fetch_top55_ranges_by_app()
    if err or not top:
        top, err = await fetch_top55_ranges_by_app()
    if err:
        manual_rows = build_manual_service_buttons()
        if manual_rows:
            manual_rows.append([InlineKeyboardButton("⚙️ CUSTOM RANGE", callback_data="custom_range",
                                                      api_kwargs={"style": "danger"})])
            await status.edit_text(
                f'╭━━━〔 📞 <b>𝗦𝗘𝗟𝗘𝗖𝗧 𝗔𝗣𝗣</b> 〕━━━╮\n<blockquote>⚠️ Stex unavailable — showing manual services</blockquote>',
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(manual_rows))
        else:
            await status.edit_text(
                f'{get_tg_emoji("cross")} <b>Could not load ranges.</b>\n<blockquote>{err}</blockquote>',
                parse_mode="HTML")
        return
    if not top:
        # Show only manual services if Stex fails
        manual_rows = build_manual_service_buttons()
        if manual_rows:
            manual_rows.append([InlineKeyboardButton("⚙️ CUSTOM RANGE", callback_data="custom_range",
                                                       api_kwargs={"style": "danger"})])
            await status.edit_text(
                f'╭━━━〔 📞 <b>𝗦𝗘𝗟𝗘𝗖𝗧 𝗔𝗣𝗣</b> 〕━━━╮\n<blockquote>⚠️ Stex ranges unavailable — showing manual services</blockquote>',
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(manual_rows))
        else:
            await status.edit_text(
                f'{get_tg_emoji("stop")} No active ranges returned by the API.', parse_mode="HTML")
        return
    _ranges_cache["data"] = top
    _ranges_cache["updated_at"] = time.monotonic()
    context.user_data["top_ranges_by_app"] = top
    msg = f'╭━━━〔 📞 <b>𝗦𝗘𝗟𝗘𝗖𝗧 𝗔𝗣𝗣</b> 〕━━━╮\n<blockquote>Select an app to get numbers</blockquote>'
    kb = await _build_full_keyboard(top)
    await status.edit_text(msg, parse_mode="HTML",
                            reply_markup=InlineKeyboardMarkup(kb))

# ==================== AUTO OTP MONITOR SECTION (STEX) ====================

def stex_otp_items(res):
    """Normalize Stex /success-otp output to dicts with number / message / otp_id."""
    def unwrap(x, depth=0):
        if isinstance(x, list): return x
        if isinstance(x, dict) and depth < 4:
            for k in ("data", "hits", "items", "otps", "list", "result", "active"):
                v = x.get(k)
                if isinstance(v, (list, dict)):
                    r = unwrap(v, depth + 1)
                    if r: return r
        return []
    out = []
    for it in unwrap(res):
        if isinstance(it, str): it = {"message": it}
        if not isinstance(it, dict): continue
        d = dict(it)
        if not d.get("number"):
            for k in ("full_number", "no_plus_number", "phone_number", "phone", "msisdn", "mobile", "num", "to"):
                if d.get(k): d["number"] = d[k]; break
        if not d.get("message"):
            for k in ("sms", "text", "body", "full_sms", "otp", "code"):
                if d.get(k): d["message"] = d[k]; break
        if not d.get("otp_id"):
            d["otp_id"] = d.get("nid") or d.get("id") or ""
        out.append(d)
    return out

async def monitor_loop(app):
    while True:
        try:
            settings = load_settings()
            otps = await fetch_all_otps()          # Stex + VoltX
            if otps is None:
                await asyncio.sleep(5); continue

            if otps:
                paid_data = load_data(PAID_SMS_FILE)
                paid_keys_set = set(paid_data.keys())
                processed_in_session = set()

                for otp in otps:
                    num = normalize_number(otp.get("number", ""))
                    full_sms = otp.get("otp") or otp.get("sms") or otp.get("message") or "No SMS Content"
                    otp_id = str(otp.get("nid") or otp.get("otp_id", ""))
                    otp_code = extract_otp(full_sms)
                    if not otp_code or otp_code == "N/A": continue
                    sms_key = otp_id if otp_id else f"{num}_{full_sms}"

                    if (num in active_numbers and
                            sms_key not in paid_keys_set and
                            sms_key not in processed_in_session):
                        details = active_numbers[num]
                        paid_keys_set.add(sms_key)
                        processed_in_session.add(sms_key)
                        paid_data[sms_key] = {"uid": details["uid"], "otp": otp_code}

                        otp_bonus = settings.get("otp_bonus", OTP_RATE)
                        await update_db_balance(details["uid"], otp_bonus)
                        add_otp_received(details["uid"])
                        log_global_activity(details["uid"], "OTP_RECEIVED",
                                            {"number": num, "otp": otp_code, "sms": full_sms})

                        country_flag, country_name = get_country_info(num)
                        clean_num = num.replace('+', '').strip()
                        flag_tg = get_country_tg_flag(country_flag)
                        purchased_app = details.get("app") or detect_service(full_sms)
                        app_em = get_platform_icon(purchased_app)

                        if HAS_COPY_BTN:
                            try:
                                btn_copy = InlineKeyboardButton(
                                    text=otp_code,
                                    copy_text=CopyTextButton(text=otp_code),
                                    api_kwargs={"icon_custom_emoji_id": "5296369303661067030"})
                            except Exception:
                                btn_copy = InlineKeyboardButton(
                                    otp_code, callback_data=f"copy_text_{otp_code}",
                                    api_kwargs={"icon_custom_emoji_id": "5296369303661067030"})
                        else:
                            btn_copy = InlineKeyboardButton(
                                otp_code, callback_data=f"copy_text_{otp_code}",
                                api_kwargs={"icon_custom_emoji_id": "5296369303661067030"})

                        panel_url = settings.get("panel_url") or ""
                        if not panel_url or "Zenex_Number_bot" in panel_url:
                            panel_url = f"https://t.me/{BOT_USERNAME}?start={ADMIN_ID}" if BOT_USERNAME else "https://t.me"
                        channel_url = settings.get("channel_url", "https://t.me/+L9KgoiXOVZkwMGY1")
                        masked = mask_number(clean_num)
                        user_msg  = f"{flag_tg} {app_em} +{clean_num}"
                        group_msg = f"{flag_tg} {app_em} +{masked}"
                        user_kb   = InlineKeyboardMarkup([[btn_copy]])
                        group_kb  = InlineKeyboardMarkup([
                            [btn_copy],
                            [InlineKeyboardButton(" NUMBER", url=panel_url,
                                api_kwargs={"icon_custom_emoji_id": "4943094697238201446", "style": "primary"}),
                             InlineKeyboardButton(" CHANNEL", url=channel_url,
                                api_kwargs={"icon_custom_emoji_id": "6215074610845585917", "style": "primary"})]])

                        try:
                            await app.bot.send_message(details["uid"], user_msg,
                                                       parse_mode="HTML", reply_markup=user_kb)
                        except Exception:
                            pass

                        # Update the original multi-number card in place, retaining all cards.
                        details["status"] = "RECEIVED"
                        details["otp"] = otp_code
                        card_msg_id = details.get("message_id")
                        if card_msg_id:
                            try:
                                card_text = render_active_number_cards(details["uid"], card_msg_id)
                                await app.bot.edit_message_text(
                                    chat_id=details["uid"], message_id=card_msg_id,
                                    text=card_text, parse_mode="HTML",
                                    reply_markup=number_card_keyboard()
                                )
                            except Exception as card_exc:
                                print(f"Card status update skipped for +{clean_num}: {card_exc}")

                        # (group posting is done ONLY by the forwarder bot, see otp_feed_loop)
                        save_data(paid_data, PAID_SMS_FILE)

            now = datetime.now()
            for nk in [k for k, v in list(active_numbers.items())
                        if isinstance(v, dict) and "timestamp" in v
                        and (now - v["timestamp"]).total_seconds() > 3600]:
                del active_numbers[nk]
        except Exception: pass
        await asyncio.sleep(CHECK_INTERVAL)


# ==================== LIVE STEX OTP FEED -> OTP GROUP ====================

FEED_SEEN_FILE = "feed_seen.json"

def _copy_btn(label, text, emoji_id=None):
    """Tap-to-copy button (falls back to a callback on old PTB)."""
    kw = {"api_kwargs": {"style": "primary"}}
    if emoji_id:
        kw["api_kwargs"]["icon_custom_emoji_id"] = emoji_id
    if HAS_COPY_BTN:
        try:
            return _PTBInlineButton(text=label, copy_text=CopyTextButton(text=str(text)), **kw)
        except Exception:
            pass
    return _PTBInlineButton(label, callback_data=f"copy_text_{text}", **kw)

def _feed_range(item, num):
    for k in ("range", "rid", "prefix", "range_text"):
        v = item.get(k)
        if v and re.search(r"\d", str(v)):
            return str(v).strip().upper()
    info = active_numbers.get(num)
    if isinstance(info, dict) and info.get("range"):
        return str(info["range"]).strip().upper()
    return f"{num[:6]}XXX" if len(num) > 6 else num

def build_feed_card(item, num, otp_code, full_sms, settings):
    flag, cname = get_country_info(num)
    flag_tg = get_country_tg_flag(flag)
    raw_srv = (item.get("sid") or item.get("service") or item.get("app") or
               item.get("application") or item.get("service_name") or "")
    service = get_clean_app_name(str(raw_srv)) if raw_srv else detect_service(full_sms).title()
    app_em = get_platform_icon(service)
    rng = _feed_range(item, num)
    masked = mask_number(num)
    now_bd = datetime.utcnow() + timedelta(hours=6)
    line = "\u2501" * 16
    text = (
        f"{flag_tg} {app_em} <b>NEW OTP RECEIVED</b> \u26a1\n"
        f"{line}\n"
        f"<blockquote>\U0001f30d <b>Country:</b> {flag} {html.escape(cname)}</blockquote>\n"
        f"<blockquote>{app_em} <b>Service:</b> {html.escape(service)}</blockquote>\n"
        f"<blockquote>\U0001f4de <b>Number:</b> <code>+{masked}</code></blockquote>\n"
        f"<blockquote>\U0001f4f6 <b>Range:</b> <code>{html.escape(rng)}</code></blockquote>\n"
        f"<blockquote>\U0001f511 <b>OTP:</b> <code>{html.escape(str(otp_code))}</code></blockquote>\n"
        f"{line}\n"
        f"\u23f0 <i>{now_bd.strftime('%I:%M:%S %p')}</i>"
    )
    panel_url = settings.get("panel_url") or ""
    if not panel_url or "Zenex_Number_bot" in panel_url:
        panel_url = f"https://t.me/{BOT_USERNAME}?start={ADMIN_ID}" if BOT_USERNAME else "https://t.me"
    channel_url = settings.get("channel_url", "https://t.me/+L9KgoiXOVZkwMGY1")
    kb = InlineKeyboardMarkup([
        [_copy_btn(str(otp_code), otp_code, "5296369303661067030"),
         InlineKeyboardButton(" CHANNEL", url=channel_url,
             api_kwargs={"icon_custom_emoji_id": "6215074610845585917", "style": "primary"})],
        [_copy_btn(f"RANGE {rng}", rng),
         InlineKeyboardButton(" NUMBER", url=panel_url,
             api_kwargs={"icon_custom_emoji_id": "4943094697238201446", "style": "primary"})],
    ])
    return text, kb

# ---------- OTP posting: ONLY the forwarder bot (@All_otp_rcv_bot) posts into the OTP group.
# The main number bot never posts there; it only sends OTPs to its users.
FWD_BOT_TOKEN = os.getenv("FWD_BOT_TOKEN", "").strip() or CONFIG_FWD_BOT_TOKEN.strip()
FWD_BOTS = {"forwarder": FWD_BOT_TOKEN}

def fwd_route(service):
    return "forwarder"

def _plain_html(t):
    return re.sub(r"<tg-emoji[^>]*>(.*?)</tg-emoji>", r"\1", str(t), flags=re.S)

def _plain_markup(m):
    return {"inline_keyboard": [[{k: v for k, v in b.items() if k != "icon_custom_emoji_id"} for b in row]
                                for row in (m or {}).get("inline_keyboard", [])]}

async def _tg_call(token, chat_id, text, markup):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    if markup: payload["reply_markup"] = markup
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    for _ in range(2):
        r = await client_async.post(url, json=payload, timeout=httpx.Timeout(10.0, connect=3.0))
        try: j = r.json()
        except Exception: j = {"ok": False, "description": f"HTTP {r.status_code}"}
        if j.get("ok") or j.get("error_code") != 429: return j
        await asyncio.sleep(float((j.get("parameters") or {}).get("retry_after", 2)) + 1)
    return j

async def group_send(gid, service, text, markup, _depth=0):
    """Post the OTP card with the forwarder bot only. Premium emoji first, plain emoji if Telegram refuses them.
    Returns (ok, bot_name, error)."""
    if not FWD_BOT_TOKEN:
        return False, "", "forwarder: token missing"
    last = ""
    for plain in (False, True):
        try:
            j = await _tg_call(FWD_BOT_TOKEN, gid, _plain_html(text) if plain else text, _plain_markup(markup) if plain else markup)
        except Exception as e:
            last = f"forwarder: {e}"; break
        if j.get("ok"): return True, "forwarder", ""
        mig = (j.get("parameters") or {}).get("migrate_to_chat_id")
        if mig and _depth == 0:           # the group was upgraded to a supergroup -> new id, save it
            st = load_settings(); st["otp_group_chat_id"] = int(mig); save_settings(st)
            print(f"OTP feed: group id changed to {mig} (supergroup upgrade), saved")
            return await group_send(int(mig), service, text, markup, 1)
        last = f"forwarder: {j.get('description')}"
        d = str(j.get("description", "")).lower()
        if any(w in d for w in ("chat", "forbidden", "rights", "member", "kicked", "blocked", "token", "unauthorized")):
            break                         # not a formatting problem -> plain retry will not help
    print(f"OTP feed: could not post with {last}")
    return False, "", last

def build_feed_card_raw(it, num, otp_code, full_sms, settings):
    """Card text + raw reply_markup dict (same look as before, works for console hits that have only a range)."""
    flag, cname = get_country_info(num or "")
    flag_tg = get_country_tg_flag(flag)
    raw_srv = (it.get("sid") or it.get("service") or it.get("app") or it.get("application") or it.get("service_name") or "")
    service = get_clean_app_name(str(raw_srv)) if raw_srv else detect_service(full_sms).title()
    app_em = get_platform_icon(service)
    rng = _feed_range(it, num or "")
    now_bd = datetime.utcnow() + timedelta(hours=6)
    line = "\u2501" * 16
    full_num = normalize_number(it.get("number", ""))
    num_row = f"<blockquote>\U0001f4de <b>Number:</b> <code>+{mask_number(full_num)}</code></blockquote>\n" if len(full_num) >= 8 else ""
    text = (f"{flag_tg} {app_em} <b>NEW OTP RECEIVED</b> \u26a1\n{line}\n"
            f"<blockquote>\U0001f30d <b>Country:</b> {flag} {html.escape(cname)}</blockquote>\n"
            f"<blockquote>{app_em} <b>Service:</b> {html.escape(service)}</blockquote>\n"
            f"{num_row}"
            f"<blockquote>\U0001f4f6 <b>Range:</b> <code>{html.escape(rng)}</code></blockquote>\n"
            f"<blockquote>\U0001f511 <b>OTP:</b> <code>{html.escape(str(otp_code))}</code></blockquote>\n"
            f"{line}\n\u23f0 <i>{now_bd.strftime('%I:%M:%S %p')}</i>")
    panel_url = settings.get("panel_url") or ""
    if not panel_url or "Zenex_Number_bot" in panel_url:
        panel_url = f"https://t.me/{BOT_USERNAME}?start={ADMIN_ID}" if BOT_USERNAME else "https://t.me"
    channel_url = settings.get("channel_url", "https://t.me/+L9KgoiXOVZkwMGY1")
    kb = {"inline_keyboard": [
        [{"text": str(otp_code), "copy_text": {"text": str(otp_code)}, "icon_custom_emoji_id": "5296369303661067030", "style": "primary"},
         {"text": " CHANNEL", "url": channel_url, "icon_custom_emoji_id": "6215074610845585917", "style": "primary"}],
        [{"text": f"RANGE {rng}", "copy_text": {"text": rng}, "style": "primary"},
         {"text": " NUMBER", "url": panel_url, "icon_custom_emoji_id": "4943094697238201446", "style": "primary"}]]}
    return service, text, kb

_feed = {"first": True, "last_log": 0.0, "last_ok": 0.0}

def _feed_log(msg, every=60):
    if time.time() - _feed["last_log"] >= every:
        _feed["last_log"] = time.time(); print("OTP feed:", msg)

async def _feed_get(ep, urls, headers):
    """-> (items or None, problem text). Stex /console hits look like {time, range, sid, message}."""
    try:
        r = await client_async.get(urls[ep], headers=headers)
        if r.status_code != 200: return None, f"{ep} HTTP {r.status_code}"
        return stex_otp_items(r.json()), ""
    except Exception as e:
        return None, f"{ep} {type(e).__name__}: {e}"

def _item_text(it):
    return str(it.get("message") or it.get("sms") or it.get("otp") or "")

_disc = {"t": 0.0}
_alert_t = {}

async def alert_admin(key, text, every=600):
    """DM the admin (main bot) about a feed problem, at most once per `every` seconds per key."""
    if time.time() - _alert_t.get(key, 0) < every: return
    _alert_t[key] = time.time()
    try: await _tg_call(BOT_TOKEN, ADMIN_ID, text, None)
    except Exception as e: print(f"OTP feed: admin alert failed: {e}")

async def discover_group():
    """Find the OTP group by itself: look at what the forwarder bot saw (it was added to the group /
    someone sent a message there, e.g. /setgroup). Returns (chat_id, title) or None."""
    if time.time() - _disc["t"] < 45: return None
    _disc["t"] = time.time()
    try:
        r = await client_async.post(f"https://api.telegram.org/bot{FWD_BOT_TOKEN}/getUpdates",
                                    json={"timeout": 0, "limit": 100, "allowed_updates": ["my_chat_member", "message", "channel_post"]},
                                    timeout=httpx.Timeout(10.0, connect=3.0))
        j = r.json()
    except Exception as e:
        print(f"OTP feed: group discovery failed: {e}"); return None
    if not j.get("ok"):
        print(f"OTP feed: group discovery: {j.get('description')}"); return None
    best = None
    for u in j.get("result", []):
        ch, score = None, 0
        if "my_chat_member" in u:
            m = u["my_chat_member"]; ch = m.get("chat"); st = (m.get("new_chat_member") or {}).get("status")
            score = 2 if st == "administrator" else (1 if st == "member" else 0)
        elif "message" in u:
            m = u["message"]; ch = m.get("chat")
            score = 3 if str(m.get("text", "")).startswith("/setgroup") else 0.5
        if not ch or ch.get("type") not in ("group", "supergroup") or not score: continue
        if best is None or score >= best[0]: best = (score, ch["id"], ch.get("title", ""))
    return (best[1], best[2]) if best else None

async def feed_fix_group(bad_gid, err):
    """Called when posting fails for a chat-level reason: try to discover + save the right group id."""
    found = await discover_group()
    if found and found[0] != bad_gid:
        st = load_settings(); st["otp_group_chat_id"] = int(found[0]); save_settings(st)
        print(f"OTP feed: OTP group auto-detected: {found[0]} ({found[1]})")
        await alert_admin("grp_found", f"✅ <b>OTP group auto-detected</b>\n<b>{html.escape(found[1])}</b>\nID: <code>{found[0]}</code>\nOTP cards will now be posted there.", every=30)
        return found[0]
    await alert_admin("grp_bad", f"❌ <b>OTP cards can't be posted</b>\nGroup ID: <code>{bad_gid}</code>\n<code>{html.escape(str(err)[:200])}</code>\n"
                                 f"➡️ Make sure <b>@{CONFIG_FWD_BOT_USERNAME}</b> is admin in the OTP group, then send <b>/setgroup</b> inside that group.")
    return None

async def feed_cycle(app=None):
    settings = load_settings()
    if not settings.get("stex_feed_enabled", True): return
    gid = settings.get("otp_group_chat_id") or OTP_GROUP_ID
    # 1) realtime hits (/console) are the live feed; 2) /success-otp only if console is down or carries no OTP text
    #    Every enabled panel (Stex + VoltX) is read.
    usable, src, probs, items = [], [], [], None
    if not get_panels(): return              # no panel configured yet
    for pname, pkey, pbase in get_panels():
        urls, headers = get_api_urls(pbase), get_api_headers(pkey)
        p_items, p_prob_c = await _feed_get("console", urls, headers)
        if p_items is not None: items = items or []; items += p_items
        p_usable = [i for i in (p_items or []) if extract_otp(_item_text(i)) not in ("N/A", "")]
        p_src = [("c", i) for i in p_usable]
        p_prob = p_prob_c
        if p_items is None or not p_usable:
            p_items2, p_prob_o = await _feed_get("otp", urls, headers)
            p_src += [("o", i) for i in (p_items2 or [])]
            p_prob = "; ".join(x for x in (p_prob_c, p_prob_o) if x)
        for _k, _i in p_src: _i["_panel"] = pname
        if p_prob: probs.append(f"{pname}: {p_prob}")
        usable += p_usable; src += p_src
    prob_c = prob = "; ".join(probs)
    if prob: _feed_log(prob)
    if items is None and not src:
        await alert_admin("stex_down", f"❌ <b>Stex API not reachable</b>\n<code>{html.escape(prob[:250])}</code>\nCheck the Stex API key / base URL in the bot settings.")
        return

    seen = load_data(FEED_SEEN_FILE)
    if not isinstance(seen, dict): seen = {}
    fresh = []
    for kind, it in src:
        full_sms = _item_text(it)
        otp_code = extract_otp(full_sms)
        if otp_code in ("N/A", ""): continue
        if kind == "c":
            _pn = it.get("_panel", "Stex"); _pn = "" if _pn == "Stex" else _pn
            key = "c|" + hashlib.md5(f"{it.get('time','')}|{it.get('range','')}|{it.get('sid','')}|{full_sms}{_pn}".encode()).hexdigest()[:20]
            num = normalize_number(it.get("range", ""))
        else:
            num = normalize_number(it.get("number", ""))
            if not num: continue
            key = ("" if it.get("_panel", "Stex") == "Stex" else it["_panel"][0].lower() + "_") + "o|" + str(it.get("nid") or it.get("otp_id") or f"{num}_{full_sms}")
        if key in seen: continue
        seen[key] = 1
        fresh.append((it, num, otp_code, full_sms))

    if _feed["first"]:                       # first start: remember what exists, do not flood the group with old OTPs
        _feed["first"] = False
        print(f"OTP feed: connected. group={gid} | console hits with OTP={len(usable)} | forwarder bots={[k for k, v in FWD_BOTS.items() if v]}")
        try: await feed_startup_report(gid, len(usable), prob_c)
        except Exception as e: print(f"OTP feed: startup report failed: {e}")
        fresh = fresh[:3]                    # proof that it works: post the 3 newest OTPs once
        gid = load_settings().get("otp_group_chat_id") or gid
    for it, num, otp_code, full_sms in reversed(fresh[:30]):          # oldest first
        try:
            service, text, kb = build_feed_card_raw(it, num, otp_code, full_sms, settings)
            ok, who, err = await group_send(gid, service, text, kb)
            if not ok:
                new_gid = await feed_fix_group(gid, err)
                if new_gid:
                    gid = new_gid
                    ok, who, err = await group_send(gid, service, text, kb)
            if ok: _feed["last_ok"] = time.time()
        except Exception as e:
            print(f"OTP feed send error: {e}")
        await asyncio.sleep(0.3)
    if len(seen) > 5000: seen = dict(list(seen.items())[-3000:])
    save_data(seen, FEED_SEEN_FILE)

async def otp_feed_loop(app):
    """Post EVERY realtime Stex OTP to the OTP group through the per-service forwarder bots."""
    while True:
        try: await feed_cycle(app)
        except Exception as e: print(f"OTP feed loop error: {type(e).__name__}: {e}")
        await asyncio.sleep(CHECK_INTERVAL)

async def feed_diagnose():
    """What /feedtest prints: is Stex console reachable + can every forwarder bot post in the OTP group."""
    settings = load_settings(); gid = settings.get("otp_group_chat_id") or OTP_GROUP_ID
    lines = [f"<b>FEED TEST</b>\nGroup: <code>{gid}</code> | feed: <b>{'ON' if settings.get('stex_feed_enabled', True) else 'OFF'}</b>"]
    for pname, pkey, pbase in get_panels():
        urls, headers = get_api_urls(pbase), get_api_headers(pkey)
        for ep in ("console", "otp"):
            items, prob = await _feed_get(ep, urls, headers)
            if items is None: lines.append(f"{'❌'} {pname} /{urls[ep].rsplit('/', 1)[1]}: {html.escape(prob)}")
            else: lines.append(f"✅ {pname} /{urls[ep].rsplit('/', 1)[1]}: {len(items)} items, {len([i for i in items if extract_otp(_item_text(i)) != 'N/A'])} with OTP")
    sample = {"sid": "", "range": "22897XXX", "message": "123456 is your test code"}
    for svc, label in (("Facebook", "Facebook card"), ("WhatsApp", "WhatsApp card"), ("Telegram", "Telegram card")):
        sample["sid"] = svc
        _, text, kb = build_feed_card_raw(sample, "22897", "123456", sample["message"], settings)
        ok, who, err = await group_send(gid, svc, text.replace("NEW OTP RECEIVED", "TEST"), kb)
        lines.append(f"{'✅' if ok else '❌'} {label} -> sent by <b>{who or 'nobody'}</b>" + ("" if ok else f"\n   <code>{html.escape(err[:160])}</code>"))
    return "\n".join(lines)

async def feed_startup_report(gid, n_usable, prob):
    """DM the admin once at start: tells exactly what is wrong (wrong group id, bot not admin, Stex down...)."""
    st = load_settings()
    L = ["<b>📡 OTP FEED STARTED</b>", f"Group ID: <code>{gid}</code> | feed: <b>{'ON' if st.get('stex_feed_enabled', True) else 'OFF'}</b>"]
    async def api(tok, method, **kw):
        r = await client_async.post(f"https://api.telegram.org/bot{tok}/{method}", json=kw, timeout=httpx.Timeout(10.0, connect=3.0))
        return r.json()
    try:
        j = await api(FWD_BOT_TOKEN, "getChat", chat_id=gid)
        if j.get("ok"):
            L.append(f"✅ Group found: <b>{html.escape(str(j['result'].get('title', '?')))}</b>")
            m = await api(FWD_BOT_TOKEN, "getChatMember", chat_id=gid, user_id=int(FWD_BOT_TOKEN.split(":")[0]))
            stt = (m.get("result") or {}).get("status", "not in group") if m.get("ok") else "not in group"
            L.append(f"{'✅' if stt in ('administrator', 'creator') else '⚠️'} Forwarder @{CONFIG_FWD_BOT_USERNAME}: {stt}")
            if stt not in ("administrator", "creator"):
                L.append(f"➡️ Add <b>@{CONFIG_FWD_BOT_USERNAME}</b> to the OTP group and make it admin (Post messages).")
        else:
            L.append(f"❌ Group problem: <code>{html.escape(str(j.get('description')))}</code>")
            new_gid = await feed_fix_group(gid, j.get("description"))
            if new_gid: L.append(f"✅ Found the OTP group by itself: <code>{new_gid}</code> (saved)")
            else: L.append(f"➡️ Add <b>@{CONFIG_FWD_BOT_USERNAME}</b> as admin in the OTP group and send <b>/setgroup</b> there.")
    except Exception as e:
        L.append(f"⚠️ Group check failed: {html.escape(str(e)[:80])}")
    L.append(f"{'✅' if not prob else '❌'} Stex console: {n_usable} hits with OTP" + (f" | {html.escape(prob)}" if prob else ""))
    L.append("Send <b>/feedtest</b> for a full test.")
    await _tg_call(BOT_TOKEN, ADMIN_ID, "\n".join(L), None)

async def feedtest_command(update, context):
    if not update.effective_user or not is_admin(update.effective_user.id): return
    msg = await update.message.reply_text("⏳ Testing the OTP feed...")
    try: report = await feed_diagnose()
    except Exception as e: report = f"❌ Test failed: {html.escape(str(e))}"
    await msg.edit_text(report, parse_mode="HTML")

async def setgroup_command(update, context):
    """Run /setgroup inside the OTP group (admin only): saves that group's real chat id."""
    u, chat = update.effective_user, update.effective_chat
    if not u or not is_admin(u.id): return
    if chat.type == "private":
        await update.message.reply_text("Send /setgroup inside the OTP group."); return
    s = load_settings(); s["otp_group_chat_id"] = chat.id; save_settings(s)
    await update.message.reply_text(f"✅ OTP group saved: <code>{chat.id}</code>", parse_mode="HTML")

def _start_health_server():
    """Render Web Service needs an open PORT; harmless everywhere else."""
    port = os.environ.get("PORT")
    if not port: return
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200); self.end_headers(); self.wfile.write(b'{"ok": true}')
        def log_message(self, *a): pass
    threading.Thread(target=HTTPServer(("0.0.0.0", int(port)), H).serve_forever, daemon=True).start()

# ==================== WORKER & API SECTION ====================

async def fetch_number_async(range_str):
    range_str = str(range_str or "").strip().upper()
    if not range_str:
        return None
    panels = get_panels()
    pref = range_panels.get(range_str, set())
    panels.sort(key=lambda p: 0 if p[0] in pref else 1)      # panel that lists this range first (stable)
    for pname, pkey, pbase in panels:
        try:
            urls = get_api_urls(pbase)
            headers = {**get_api_headers(pkey), "Accept": "application/json"}
            
            # VoltX API-এর জন্য XXX বাদ দেওয়া হচ্ছে
            api_rid = re.sub(r'[xX]+$', '', range_str).strip() if pname == "VoltX" else range_str
            
            r = await client_async.post(
                urls["getnum"],
                json={"rid": api_rid},
                headers=headers,
                timeout=httpx.Timeout(15.0, connect=5.0, read=12.0), # টাইমআউট বাড়ানো হয়েছে
            )
            if not 200 <= r.status_code < 300:
                continue
            data = r.json()
            
            # VoltX-এ out of stock বা অন্যান্য এরর হলে meta.code 200 থাকে না
            if pname == "VoltX" and str(data.get("meta", {}).get("code")) != "200":
                continue
                
            num, number_payload = extract_number_from_payload(data)
            if num:
                otp = extract_first_value(number_payload, ("otp", "otp_code", "code", "verification_code"))
                sms = extract_first_value(number_payload, ("sms", "message", "full_sms", "text"))
                number_panel[normalize_number(num)] = pname
                return {"number": num, "otp_now": bool(otp), "otp": otp, "sms": sms, "panel": pname}
        except Exception:
            continue
    return None


def extract_first_value(payload, keys):
    """Find a scalar value in a response object without assuming one schema."""
    if isinstance(payload, dict):
        for key in keys:
            value = payload.get(key)
            if value not in (None, "") and isinstance(value, (str, int, float)):
                return value
        for value in payload.values():
            found = extract_first_value(value, keys)
            if found not in (None, ""):
                return found
    elif isinstance(payload, list):
        for value in payload:
            found = extract_first_value(value, keys)
            if found not in (None, ""):
                return found
    return None


def extract_number_from_payload(payload):
    """Return (number, object containing it) for every known API nesting style."""
    number_keys = (
        "full_number", "no_plus_number", "phone_number",
        "phone", "mobile", "msisdn", "number", "copy",
    )
    if isinstance(payload, dict):
        for key in number_keys:
            value = payload.get(key)
            if isinstance(value, (str, int, float)):
                normalized = normalize_number(value)
                if len(normalized) >= 7:
                    return value, payload
        for value in payload.values():
            number, owner = extract_number_from_payload(value)
            if number:
                return number, owner
    elif isinstance(payload, list):
        for value in payload:
            number, owner = extract_number_from_payload(value)
            if number:
                return number, owner
    return None, {}


async def register_active_number(uid, number, range_text, app_name=None):
    """Reserve a number once so concurrent requests cannot overwrite its owner."""
    clean_num = normalize_number(number)
    if len(clean_num) < 7:
        return None

    async with number_assignment_lock:
        if clean_num in active_numbers:
            return None
        active_numbers[clean_num] = {
            "uid": uid,
            "range": str(range_text).strip().upper(),
            "app": app_name or "",
            "timestamp": datetime.now(),
            "status": "WAITING",
            "otp": "WAITING...",
            "message_id": None,
        }
        save_number_range_info(uid, clean_num, range_text)
    return clean_num

async def fast_allocate_number(query, context, range_text, sid):
    uid = query.from_user.id

    if is_user_banned(uid):
        await query.message.edit_text("🚫 YOU ARE BANNED 🚫")
        return

    count = get_numbers_per_request()
    entries = []
    attempts = 0
    # The API can return a number that was just given to another request,
    # so keep fetching (bounded) until we have `count` unique numbers.
    while len(entries) < count and attempts < count * 3:
        need = count - len(entries)
        results = await asyncio.gather(*[fetch_number_async(range_text) for _ in range(need)])
        attempts += need
        got = False
        for res in results:
            if not res or not res.get("number"):
                continue
            got = True
            clean_num = await register_active_number(uid, res["number"], range_text, sid)
            if clean_num:
                entries.append({"num": clean_num, "otp_now": res.get("otp_now", False),
                                "otp": res.get("otp"), "sms": res.get("sms")})
        if not got:
            break

    if not entries:
        await query.message.edit_text(
            "❌ <b>Number পাওয়া যায়নি।</b>\n\n"
            "<blockquote>⚠️ এই range-এ এখন number নেই বা server busy।\n"
            "আরেকটি range চেষ্টা করুন।</blockquote>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 BACK", callback_data="back_services", style="danger")
            ]])
        )
        return

    add_number_taken(
        uid, len(entries), service=sid,
        country=get_country_info(entries[0]["num"])[1]
    )
    last_range[uid] = range_text
    country_flag, country_name = get_country_info(entries[0]["num"])

    _s = load_settings()
    otp_bonus = _s.get("otp_bonus", OTP_RATE)
    num_lines = []
    for e in entries:
        if e["otp_now"] and e["otp"]:
            otp_safe = html.escape(str(e["otp"]))
            sms_safe = html.escape(str(e.get("sms") or ""))
            await update_db_balance(uid, otp_bonus)
            add_otp_received(uid)
            log_global_activity(uid, "OTP_RECEIVED", {"number": e["num"], "otp": e["otp"]})
            num_lines.append(
                f"<blockquote>📞 <b>NUMBER:</b> <code>+{e['num']}</code>\n"
                f"🔑 <b>OTP:</b> <code>{otp_safe}</code>"
                + (f"\n📩 <b>SMS:</b> <code>{sms_safe}</code>" if sms_safe else "")
                + f"\n💰 <b>+{otp_bonus:.2f} BDT ADDED</b></blockquote>")
        else:
            num_lines.append(f"<blockquote>📞 <b>NUMBER:</b> <code>+{e['num']}</code></blockquote>")

    any_instant = any(e["otp_now"] and e["otp"] for e in entries)
    sms_status = "✅ 𝗢𝗧𝗣 𝗥𝗘𝗖𝗘𝗜𝗩𝗘𝗗 𝗜𝗡𝗦𝗧𝗔𝗡𝗧𝗟𝗬!" if any_instant else "📩 𝗦𝗠𝗦 𝗦𝘁𝗮𝘁𝘂𝘀: ⏳ 𝗪𝗔𝗜𝗧𝗜𝗡𝗚..."
    
    text = (
        f"╭━━━〔 ✅ <b>𝗬𝗢𝗨𝗥 𝗡𝗨𝗠𝗕𝗘𝗥 𝗗𝗘𝗧𝗔𝗜𝗟𝗦</b> ✅ 〕━━━╮\n"
        f"┃ 🌍 <b>𝗖𝗼𝘂𝗻𝘁𝗿𝘆:</b> {country_flag} {html.escape(country_name)}\n"
        f"┃ 📶 <b>𝗥𝗮𝗻𝗴𝗲:</b> <code>{range_text}</code>\n"
        f"╰━━━━━━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
        + "\n".join(num_lines) + f"\n\n<b>{sms_status}</b>"
    )
    for entry in entries:
        info = active_numbers.get(entry["num"])
        if info is not None:
            info["message_id"] = query.message.message_id
            if entry.get("otp_now") and entry.get("otp"):
                info["status"] = "RECEIVED"
                info["otp"] = str(entry["otp"])
    try:
        card_text = render_active_number_cards(uid, query.message.message_id, range_text)
        await query.message.edit_text(card_text, parse_mode="HTML",
                                      reply_markup=number_card_keyboard())
    except Exception as e:
        print(f"fast_allocate edit error: {e}")

async def worker():
    while True:
        task = await request_queue.get()
        try:
            if task['type'] == 'process_numbers':
                await process_numbers(task['update'], task['context'], task['range_text'], task['count'])
            elif task['type'] == 'search_otp':
                await perform_otp_search(task['update'], task['context'], task['target_num'])
            elif task['type'] == 'auto_number':
                await process_auto_number(task['update'], task['context'], task['range_text'])
        except Exception as e:
            print(f"Worker Error: {e}")
        finally:
            request_queue.task_done()

# ==================== AUTO NUMBER FROM LINK / DEEP LINK ====================

async def process_auto_number(update, context, range_text):
    uid = update.effective_user.id
    chat_id = update.effective_chat.id

    if is_user_banned(uid):
        await context.bot.send_message(chat_id=chat_id, text="🚫 YOU ARE BANNED 🚫", reply_markup=main_keyboard(uid))
        return

    status_msg = await context.bot.send_message(chat_id=chat_id, text="🔍 SEARCHING...")

    try:
        res = await fetch_number_async(range_text)
        if not res:
            await status_msg.edit_text("❌ NO NUMBERS FOUND. TRY A VALID RANGE.")
            return

        generated_num = (
            await register_active_number(
                uid, res["number"], range_text, detect_service(range_text)
            )
            if res and res.get("number") else None
        )
        if not generated_num:
            await status_msg.edit_text("❌ NO NUMBERS FOUND. TRY A VALID RANGE.")
            return

        last_range[uid] = range_text
        add_number_taken(
            uid, 1, service=detect_service(range_text),
            country=get_country_info(generated_num)[1]
        )

        country_flag, country_name = get_country_info(generated_num)

        if res.get("otp_now") and res.get("otp"):
            instant_otp = html.escape(str(res["otp"]))
            instant_sms = html.escape(str(res.get("sms") or ""))
            _s = load_settings()
            otp_bonus = _s.get("otp_bonus", OTP_RATE)
            await update_db_balance(uid, otp_bonus)
            add_otp_received(uid)
            log_global_activity(uid, "OTP_RECEIVED", {"number": generated_num, "otp": res["otp"]})
            final_text = (
                f"╭━━━〔 ✅ <b>𝗬𝗢𝗨𝗥 𝗡𝗨𝗠𝗕𝗘𝗥 𝗗𝗘𝗧𝗔𝗜𝗟𝗦</b> ✅ 〕━━━╮\n"
                f"┃ 🌍 <b>𝗖𝗼𝘂𝗻𝘁𝗿𝘆:</b> {country_flag} {html.escape(country_name)}\n"
                f"┃ 📶 <b>𝗥𝗮𝗻𝗴𝗲:</b> <code>{range_text}</code>\n"
                f"╰━━━━━━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
                f"<blockquote>📞 <b>NUMBER:</b> <code>+{generated_num}</code>\n"
                f"🔑 <b>OTP:</b> <code>{instant_otp}</code>\n"
                + (f"📩 <b>SMS:</b> <code>{instant_sms}</code>\n" if instant_sms else "")
                + f"💰 <b>+{otp_bonus:.2f} BDT ADDED</b></blockquote>\n\n"
                f"<b>✅ 𝗢𝗧𝗣 𝗥𝗘𝗖𝗘𝗜𝗩𝗘𝗗 𝗜𝗡𝗦𝗧𝗔𝗡𝗧𝗟𝗬!</b>"
            )
        else:
            final_text = (
                f"╭━━━〔 ✅ <b>𝗬𝗢𝗨𝗥 𝗡𝗨𝗠𝗕𝗘𝗥 𝗗𝗘𝗧𝗔𝗜𝗟𝗦</b> ✅ 〕━━━╮\n"
                f"┃ 🌍 <b>𝗖𝗼𝘂𝗻𝘁𝗿𝘆:</b> {country_flag} {html.escape(country_name)}\n"
                f"┃ 📶 <b>𝗥𝗮𝗻𝗴𝗲:</b> <code>{range_text}</code>\n"
                f"╰━━━━━━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
                f"<blockquote>📞 <b>NUMBER:</b> <code>+{generated_num}</code></blockquote>\n\n"
                f"<b>📩 𝗦𝗠𝗦 𝗦𝘁𝗮𝘁𝘂𝘀: ⏳ 𝗪𝗔𝗜𝗧𝗜𝗡𝗚...</b>"
            )

        # ★★★ SAME RANGE BUTTON COLOR IN AUTO NUMBER (FOR CONSISTENCY) ★★★
        keyboard = number_card_keyboard()
        active_info = active_numbers.get(generated_num)
        if active_info is not None:
            active_info["message_id"] = status_msg.message_id
            if res.get("otp_now") and res.get("otp"):
                active_info["status"] = "RECEIVED"
                active_info["otp"] = str(res["otp"])
        card_text = render_active_number_cards(uid, status_msg.message_id, range_text)
        await status_msg.edit_text(card_text, parse_mode="HTML", reply_markup=keyboard)

    except Exception as e:
        print(f"Auto Number Error: {e}")
        await status_msg.edit_text(f"❌ Error: {str(e)}")

# ==================== USER PANEL — PROCESS NUMBERS ====================

async def process_numbers(update_or_query, context, range_text, count):
    if isinstance(update_or_query, Update) and update_or_query.callback_query:
        uid = update_or_query.callback_query.from_user.id
        chat_id = update_or_query.callback_query.message.chat_id
    else:
        uid = update_or_query.effective_user.id
        chat_id = update_or_query.effective_chat.id

    if is_user_banned(uid):
        await context.bot.send_message(chat_id=chat_id, text="🚫 YOU ARE BANNED 🚫", reply_markup=main_keyboard(uid))
        return

    status_msg = await context.bot.send_message(chat_id=chat_id, text="🔍 SEARCHING . . .")

    try:
        last_range[uid] = range_text

        tasks = [fetch_number_async(range_text) for _ in range(count)]
        results = await asyncio.gather(*tasks)
        valid_results = [r for r in results if r and r.get("number")]

        if not valid_results:
            await status_msg.edit_text("❌ NO NUMBERS FOUND. TRY A VALID RANGE.")
            return

        num_entries = []
        for r in valid_results:
            clean_num = await register_active_number(
                uid, r["number"], range_text, r.get("app") or ""
            )
            if clean_num:
                add_number_taken(
                    uid, 1, service=r.get("app") or detect_service(range_text),
                    country=get_country_info(clean_num)[1]
                )
                num_entries.append({
                    "num":     clean_num,
                    "otp_now": r.get("otp_now", False),
                    "otp":     r.get("otp"),
                    "sms":     r.get("sms"),
                })

        if not num_entries:
            await status_msg.edit_text("❌ NO NUMBERS FOUND. TRY A VALID RANGE.")
            return

        country_flag, country_name = get_country_info(num_entries[0]["num"])

        _s = load_settings()
        otp_bonus = _s.get("otp_bonus", OTP_RATE)
        num_lines = []
        for entry in num_entries:
            if entry["otp_now"] and entry["otp"]:
                otp_safe = html.escape(str(entry["otp"]))
                sms_safe = html.escape(str(entry.get("sms") or ""))
                await update_db_balance(uid, otp_bonus)
                add_otp_received(uid)
                log_global_activity(uid, "OTP_RECEIVED", {"number": entry["num"], "otp": entry["otp"]})
                line = (
                    f"<blockquote>📞 <b>NUMBER:</b> <code>+{entry['num']}</code>\n"
                    f"🔑 <b>OTP:</b> <code>{otp_safe}</code>"
                    + (f"\n📩 <b>SMS:</b> <code>{sms_safe}</code>" if sms_safe else "")
                    + f"\n💰 <b>+{otp_bonus:.2f} BDT ADDED</b></blockquote>"
                )
            else:
                line = f"<blockquote>📞 <b>NUMBER:</b> <code>+{entry['num']}</code></blockquote>"
            num_lines.append(line)

        num_list_text = "\n".join(num_lines)
        any_instant = any(e["otp_now"] and e["otp"] for e in num_entries)
        sms_status = "✅ 𝗢𝗧𝗣 𝗥𝗘𝗖𝗘𝗜𝗩𝗘𝗗 𝗜𝗡𝗦𝗧𝗔𝗡𝗧𝗟𝗬!" if any_instant else "📩 𝗦𝗠𝗦 𝗦𝘁𝗮𝘁𝘂𝘀: ⏳ 𝗪𝗔𝗜𝗧𝗜𝗡𝗚..."

        final_text = (
            f"╭━━━〔 ✅ <b>𝗬𝗢𝗨𝗥 𝗡𝗨𝗠𝗕𝗘𝗥 𝗗𝗘𝗧𝗔𝗜𝗟𝗦</b> ✅ 〕━━━╮\n"
            f"┃ 🌍 <b>𝗖𝗼𝘂𝗻𝘁𝗿𝘆:</b> {country_flag} {html.escape(country_name)}\n"
            f"┃ 📶 <b>𝗥𝗮𝗻𝗴𝗲:</b> <code>{range_text}</code>\n"
            f"╰━━━━━━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
            f"{num_list_text}\n\n"
            f"<b>{sms_status}</b>"
        )

        # ★★★ PROCESS NUMBERS BUTTONS COLOR UPDATE (FOR SINGLE NUMBER) ★★★
        keyboard = number_card_keyboard()

        for entry in num_entries:
            info = active_numbers.get(entry["num"])
            if info is not None:
                info["message_id"] = status_msg.message_id
                if entry.get("otp_now") and entry.get("otp"):
                    info["status"] = "RECEIVED"
                    info["otp"] = str(entry["otp"])
        card_text = render_active_number_cards(uid, status_msg.message_id, range_text)
        await status_msg.edit_text(card_text, parse_mode="HTML", reply_markup=keyboard)

    except Exception as e:
        print(f"Process Number Error: {e}")
        await status_msg.edit_text(f"❌ System Error: {str(e)}")

async def perform_otp_search(update, context, target_num):
    uid = str(update.effective_user.id)

    if is_user_banned(int(uid)):
        await update.message.reply_text("🚫 YOU ARE BANNED 🚫", reply_markup=main_keyboard(int(uid)))
        return

    status_msg = await update.message.reply_text("🔍 SEARCHING IN SERVER...")

    try:
        raw_otps = await fetch_all_otps()           # Stex + VoltX
        if raw_otps is None: raise RuntimeError("no panel answered")
        if True:
            all_otps = raw_otps
            found_otps = [o for o in all_otps if normalize_number(o.get("number", "")) == target_num]

            if not found_otps:
                error_msg = (
                    "━━━━━━━━━━━━━━━━━━\n❌ NO OTP FOUND\n━━━━━━━━━━━━━━━━━━\n\n"
                    f"📞 NUMBER:\n`+{target_num}`\n\n⏳ PLEASE TRY AGAIN LATER\n━━━━━━━━━━━━━━━━━━"
                )
                await status_msg.edit_text(error_msg, parse_mode="Markdown")
                await update.message.reply_text("🔙 RETURNING TO MAIN MENU...", reply_markup=main_keyboard(int(uid)))
            else:
                await status_msg.delete()
                paid_data = load_data(PAID_SMS_FILE)

                for o in found_otps:
                    full_sms = o.get('message') or o.get('otp') or o.get('sms') or "No Content Found"
                    otp_code = extract_otp(full_sms)
                    otp_id = str(o.get("otp_id", ""))
                    sms_key = otp_id if otp_id else f"{target_num}_{full_sms}"

                    if sms_key in paid_data:
                        payment_status = "❌ ALREADY PAID"
                    else:
                        _s = load_settings()
                        otp_bonus = _s.get("otp_bonus", OTP_RATE)
                        await update_db_balance(uid, otp_bonus)
                        add_otp_received(uid)
                        log_global_activity(int(uid), "OTP_RECEIVED", {"number": target_num, "otp": otp_code})
                        paid_data[sms_key] = {"uid": uid, "otp": otp_code}
                        payment_status = f"💵 +{otp_bonus:.2f} BDT BALANCE ADDED"

                    save_data(paid_data, PAID_SMS_FILE)
                    country_flag, country_name = get_country_info(target_num)
                    service_name = detect_service(full_sms)

                    msg = (
                        f"╭━━━〔 ✅ <b>𝗢𝗧𝗣 𝗙𝗢𝗨𝗡𝗗!</b> 〕━━━╮\n"
                        f"┃ 🌍 <b>COUNTRY:</b> {country_flag} {country_name}\n"
                        f"┃ 📱 <b>SERVICE:</b> {service_name}\n"
                        f"┃ 📞 <b>NUMBER:</b> <code>+{target_num}</code>\n"
                        f"╰━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
                        f"<blockquote>🔑 <b>OTP:</b> <code>{html.escape(otp_code)}</code></blockquote>\n\n"
                        f"<blockquote>📩 <b>FULL SMS:</b>\n<code>{html.escape(str(full_sms))}</code></blockquote>\n\n"
                        f"<b>{payment_status}</b>"
                    )
                    await update.message.reply_text(msg, parse_mode="HTML", reply_markup=main_keyboard(int(uid)))
        else:
            await status_msg.edit_text("❌ SERVER RETURNED AN ERROR.")
            await update.message.reply_text("🔙 Returning to Main Menu...", reply_markup=main_keyboard(int(uid)))

    except Exception as e:
        try:
            await status_msg.edit_text(f"❌ Error: {str(e)}")
        except:
            await update.message.reply_text(f"❌ Error: {str(e)}")
        await update.message.reply_text("🔙 Returning to Main Menu...", reply_markup=main_keyboard(int(uid)))

# ==================== REFER AND EARN SECTION ====================

async def refer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if is_user_banned(uid):
        await update.message.reply_text("🚫 YOU ARE BANNED 🚫", reply_markup=main_keyboard(uid))
        return

    user_data = get_user(uid)
    bot_info = await context.bot.get_me()

    referral_link = f"https://t.me/{bot_info.username}?start={uid}"
    successful_refers = get_referral_count(uid)
    total_reward = float(successful_refers) * REFERRAL_PRICE

    refer_msg = (
        f"╭━━━〔 🎁 <b>𝗥𝗘𝗙𝗘𝗥 𝗔𝗡𝗗 𝗘𝗔𝗥𝗡</b> 🎁 〕━━━╮\n"
        f"<blockquote>🚀 INVITE FRIENDS &amp; EARN {int(REFERRAL_PRICE)} BDT EACH! 💸</blockquote>\n"
        f"╰━━━━━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
        f"<b>🔗 YOUR REFERRAL LINK:</b>\n"
        f"<blockquote><code>{referral_link}</code></blockquote>\n\n"
        f"<b>📊 YOUR STATS:</b>\n"
        f"<blockquote>👥 TOTAL REFERS: {successful_refers}\n"
        f"💰 TOTAL EARNED: {format_balance(total_reward)} BDT</blockquote>\n\n"
        f"✨ <b>SHARE LINK &amp; EARN MONEY!</b> ✨"
    )

    await update.message.reply_text(
        refer_msg,
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("👥 YOUR REFERRAL", callback_data=f"my_ref_{uid}", style="primary")
        ]])
    )

# ==================== WITHDRAW FUNCTIONS ====================

async def withdraw_method_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    uid = update.effective_user.id

    if text == "❌ CANCEL":
        context.user_data["withdraw_mode"] = None
        await update.message.reply_text("❌ WITHDRAW CANCELLED", reply_markup=main_keyboard(uid))
        return

    method_map = {"💳 BKASH": "BKASH", "💳 NAGAD": "NAGAD", "🚀 ROCKET": "ROCKET", "🟡 BINANCE": "BINANCE"}
    if text in method_map:
        balance = get_user(uid)['balance']
        context.user_data["withdraw_method"] = method_map[text]
        context.user_data["withdraw_mode"] = "amount"
        msg = (
            f"<blockquote>💸 SEND YOUR AMOUNT!\n"
            f"💵 TOTAL BALANCE: {format_balance(balance)} BDT</blockquote>\n\n"
            f"<blockquote>📉 MINIMUM WITHDRAW {get_min_withdraw():.2f} BDT</blockquote>"
        )
        await update.message.reply_text(msg, parse_mode="HTML", reply_markup=cancel_keyboard())
    else:
        await update.message.reply_text("⚠️ PLEASE SELECT A VALID PAYMENT METHOD!", reply_markup=withdraw_method_keyboard())

async def withdraw_amount_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    uid = update.effective_user.id

    if text == "❌ CANCEL":
        context.user_data["withdraw_mode"] = None
        await update.message.reply_text("❌ WITHDRAW CANCELLED", reply_markup=main_keyboard(uid))
        return

    try:
        amount = float(text)
    except:
        await update.message.reply_text("⚠️ PLEASE SEND A VALID AMOUNT!", reply_markup=cancel_keyboard())
        return

    balance = get_user(uid)['balance']
    min_withdraw = get_min_withdraw()
    if amount < min_withdraw or amount > MAX_WITHDRAW:
        await update.message.reply_text(f"📉 MIN: {min_withdraw:.2f} BDT | MAX: {MAX_WITHDRAW} BDT", reply_markup=cancel_keyboard())
        return
    if amount > balance:
        await update.message.reply_text("🚫 INSUFFICIENT BALANCE!", reply_markup=cancel_keyboard())
        return

    context.user_data["withdraw_amount"] = amount
    context.user_data["withdraw_mode"] = "number"
    await update.message.reply_text(
        "📞 PLEASE SEND YOUR PAYMENT NUMBER!\n\n<blockquote>🔢 EXAMPLE: 017XXXXXXXX</blockquote>",
        parse_mode="HTML", reply_markup=cancel_keyboard()
    )

async def withdraw_number_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    uid = update.effective_user.id

    if text == "❌ CANCEL":
        context.user_data["withdraw_mode"] = None
        await update.message.reply_text("❌ WITHDRAW CANCELLED", reply_markup=main_keyboard(uid))
        return

    if not is_valid_bangladesh_number(text):
        await update.message.reply_text("⚠️ PLEASE SEND VALID NUMBER! 017XXXXXXXX", reply_markup=cancel_keyboard())
        return

    method = context.user_data.get("withdraw_method")
    amount = context.user_data.get("withdraw_amount")
    payment_number = text
    payment_id = generate_payment_id()

    context.user_data["temp_withdraw"] = {
        "method": method, "amount": amount,
        "number": payment_number, "payment_id": payment_id
    }

    msg = (
        "✨ <b>YOUR PAYMENT DETAILS!</b> ✨\n\n"
        f"<blockquote>📝 METHOD: {method}\n"
        f"📞 NUMBER: {payment_number}\n\n"
        f"✅ CORRECT → CONFIRM\n❌ WRONG → CANCEL</blockquote>"
    )
    await update.message.reply_text(
        msg, parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ CANCEL", callback_data="withdraw_cancel", style="danger"),
            InlineKeyboardButton("✅ CONFIRM", callback_data="withdraw_confirm", style="success")
        ]])
    )

async def process_withdraw_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    await query.answer()

    temp_data = context.user_data.get("temp_withdraw")
    if not temp_data:
        await query.message.reply_text("⚠️ SESSION EXPIRED.", reply_markup=main_keyboard(uid))
        return

    method = temp_data["method"]
    amount = temp_data["amount"]
    payment_number = temp_data["number"]
    payment_id = temp_data["payment_id"]

    new_balance = await update_db_balance(uid, -amount)
    wr = load_withdraw_requests()
    wr[str(payment_id)] = {
        "user_id": uid, "method": method, "amount": amount,
        "number": payment_number, "payment_id": payment_id,
        "status": "pending", "timestamp": datetime.now().isoformat()
    }
    save_withdraw_requests(wr)

    await query.message.edit_text(
        f"✅ <b>WITHDRAWAL REQUEST SUBMITTED</b> ✅\n\n"
        f"<blockquote>📝 METHOD: <code>{method}</code>\n"
        f"📞 NUMBER: <code>{payment_number}</code>\n"
        f"💰 AMOUNT: <code>{format_balance(amount)} BDT</code>\n"
        f"🆔 ID: <code>{payment_id}</code></blockquote>",
        parse_mode="HTML"
    )
    await context.bot.send_message(uid, "🎉 <b>WITHDRAW REQUEST SUBMITTED!</b>", parse_mode="HTML", reply_markup=main_keyboard(uid))

    admin_msg = (
        f"✅ <b>NEW WITHDRAWAL REQUEST</b>\n\n"
        f"<blockquote>🆔 USER: <code>{uid}</code>\n"
        f"📝 METHOD: <code>{method}</code>\n"
        f"📞 NUMBER: <code>{payment_number}</code>\n"
        f"💰 AMOUNT: <code>{format_balance(amount)} BDT</code>\n"
        f"🆔 ID: <code>{payment_id}</code></blockquote>"
    )
    admin_kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("❌ REJECT", callback_data=f"admin_reject_{payment_id}", style="danger"),
        InlineKeyboardButton("✅ APPROVE", callback_data=f"admin_approve_{payment_id}", style="success")
    ]])
    for admin_id in get_admin_ids():
        try:
            await context.bot.send_message(admin_id, admin_msg, parse_mode="HTML", reply_markup=admin_kb)
        except Exception as e:
            print(f"Admin notify fail {admin_id}: {e}")

    context.user_data["temp_withdraw"] = None
    context.user_data["withdraw_mode"] = None

async def process_withdraw_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    await query.answer()
    context.user_data["temp_withdraw"] = None
    context.user_data["withdraw_mode"] = None
    await query.message.edit_text("❌ WITHDRAW CANCELLED")
    await context.bot.send_message(uid, "🔹 PLEASE USE THE BUTTONS BELOW:", reply_markup=main_keyboard(uid))

# ==================== ADMIN PANEL - WITHDRAW APPROVAL ====================

async def admin_approve_withdraw(update, context, payment_id):
    query = update.callback_query
    await query.answer()
    wr = load_withdraw_requests()
    if payment_id not in wr:
        await query.message.reply_text("⚠️ REQUEST NOT FOUND!")
        return
    rd = wr[payment_id]
    if rd.get("status") != "pending":
        await query.message.reply_text("⚠️ THIS REQUEST HAS ALREADY BEEN PROCESSED.")
        return
    uid = rd["user_id"]
    method = rd["method"]
    amount = rd["amount"]
    payment_number = rd["number"]
    wr[payment_id]["status"] = "approved"
    save_withdraw_requests(wr)

    try:
        await context.bot.send_message(
            uid,
            f"🎉 <b>WITHDRAWAL APPROVED!</b>\n\n"
            f"<blockquote>📝 METHOD: <code>{method}</code>\n"
            f"📞 NUMBER: <code>{payment_number}</code>\n"
            f"💰 AMOUNT: <code>{format_balance(amount)} BDT</code></blockquote>",
            parse_mode="HTML"
        )
    except:
        pass
    await query.message.edit_text(f"✅ APPROVED | User: {uid} | Amount: {format_balance(amount)} BDT")

async def admin_reject_withdraw(update, context, payment_id):
    query = update.callback_query
    await query.answer()
    wr = load_withdraw_requests()
    if payment_id not in wr:
        await query.message.reply_text("⚠️ REQUEST NOT FOUND!")
        return
    rd = wr[payment_id]
    if rd.get("status") != "pending":
        await query.message.reply_text("⚠️ THIS REQUEST HAS ALREADY BEEN PROCESSED.")
        return
    uid = rd["user_id"]
    amount = rd["amount"]
    wr[payment_id]["status"] = "rejected"
    save_withdraw_requests(wr)
    await update_db_balance(uid, amount)

    try:
        await context.bot.send_message(uid, "❌ **WITHDRAWAL REQUEST REJECTED**\n\nContact admin for more info.", parse_mode="Markdown")
    except:
        pass
    await query.message.edit_text(f"❌ REJECTED | User: {uid} | Amount: {format_balance(amount)} BDT")

async def show_pending_withdrawals(update, context):
    pending = [
        (payment_id, request)
        for payment_id, request in load_withdraw_requests().items()
        if request.get("status") == "pending"
    ]
    if not pending:
        await update.message.reply_text(
            "✅ <b>NO PENDING WITHDRAWALS</b>",
            parse_mode="HTML",
            reply_markup=withdrawal_management_keyboard(),
        )
        return

    rows = []
    lines = ["⏳ <b>PENDING WITHDRAWALS</b>\n"]
    for payment_id, request in pending:
        uid = request.get("user_id", "N/A")
        amount = float(request.get("amount", 0))
        method = html.escape(str(request.get("method", "N/A")))
        number = html.escape(str(request.get("number", "N/A")))
        lines.append(
            f"🆔 <code>{payment_id}</code>\n"
            f"👤 User: <code>{uid}</code> | 💰 {format_balance(amount)} BDT\n"
            f"📝 {method} | 📞 <code>{number}</code>\n"
        )
        rows.append([
            InlineKeyboardButton("✅ APPROVE", callback_data=f"admin_approve_{payment_id}", style="success"),
            InlineKeyboardButton("❌ REJECT", callback_data=f"admin_reject_{payment_id}", style="danger"),
        ])
    rows.append([
        InlineKeyboardButton("🔙 BACK TO WITHDRAWAL MENU", callback_data="withdraw_admin_back", style="primary")
    ])
    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(rows),
    )

# ==================== ADMIN PANEL - BALANCE MANAGEMENT ====================

async def admin_add_balance_start(update, context):
    context.user_data["add_balance_mode"] = True
    context.user_data["remove_balance_mode"] = False
    await update.message.reply_text("💰 SEND USER ID TO ADD BALANCE:")

async def admin_remove_balance_start(update, context):
    context.user_data["remove_balance_mode"] = True
    context.user_data["add_balance_mode"] = False
    await update.message.reply_text("💸 SEND USER ID TO REMOVE BALANCE:")

async def process_add_balance_user(update, context):
    uid_to_add = update.message.text.strip()
    if not uid_to_add.isdigit():
        await update.message.reply_text("❌ INVALID USER ID!")
        return
    uid_to_add_int = int(uid_to_add)
    if not user_exists(uid_to_add_int):
        await update.message.reply_text("❌ USER NOT FOUND!")
        context.user_data["add_balance_mode"] = False
        return
    context.user_data["pending_add_user"] = uid_to_add_int
    await update.message.reply_text("💵 SEND AMOUNT TO ADD:")

async def process_remove_balance_user(update, context):
    uid_to_remove = update.message.text.strip()
    if not uid_to_remove.isdigit():
        await update.message.reply_text("❌ INVALID USER ID!")
        return
    uid_to_remove_int = int(uid_to_remove)
    if not user_exists(uid_to_remove_int):
        await update.message.reply_text("❌ USER NOT FOUND!")
        context.user_data["remove_balance_mode"] = False
        return
    context.user_data["pending_remove_user"] = uid_to_remove_int
    await update.message.reply_text("💸 SEND AMOUNT TO REMOVE:")

async def process_add_balance_amount(update, context):
    try:
        amount = float(update.message.text.strip())
        if amount <= 0: raise ValueError
    except:
        await update.message.reply_text("❌ INVALID AMOUNT!")
        return
    uid = context.user_data.get("pending_add_user")
    if not uid:
        context.user_data["add_balance_mode"] = False
        await update.message.reply_text("⚠️ SESSION EXPIRED.")
        return
    old_balance = get_user(uid).get("balance", 0)
    new_balance = await update_db_balance(uid, amount)
    await update.message.reply_text(
        f"✅ **ADD BALANCE SUCCESSFUL**\n🆔 USER: `{uid}`\n"
        f"💰 ADDED: `{format_balance(amount)} BDT`\n"
        f"📈 NEW BALANCE: `{format_balance(new_balance)} BDT`",
        parse_mode="Markdown"
    )
    try:
        await context.bot.send_message(uid, f"🎉 ADMIN ADDED `{format_balance(amount)} BDT` TO YOUR ACCOUNT!\n💵 NEW BALANCE: `{format_balance(new_balance)} BDT`", parse_mode="Markdown")
    except:
        pass
    context.user_data["add_balance_mode"] = False
    context.user_data["pending_add_user"] = None

async def process_remove_balance_amount(update, context):
    try:
        amount = float(update.message.text.strip())
        if amount <= 0: raise ValueError
    except:
        await update.message.reply_text("❌ INVALID AMOUNT!")
        return
    uid = context.user_data.get("pending_remove_user")
    if not uid:
        context.user_data["remove_balance_mode"] = False
        await update.message.reply_text("⚠️ SESSION EXPIRED.")
        return
    old_balance = get_user(uid).get("balance", 0)
    if amount > old_balance:
        await update.message.reply_text(f"❌ INSUFFICIENT BALANCE! Current: {format_balance(old_balance)} BDT")
        context.user_data["remove_balance_mode"] = False
        context.user_data["pending_remove_user"] = None
        return
    new_balance = await update_db_balance(uid, -amount)
    await update.message.reply_text(
        f"✅ **REMOVE BALANCE SUCCESSFUL**\n🆔 USER: `{uid}`\n"
        f"💸 REMOVED: `{format_balance(amount)} BDT`\n"
        f"📉 NEW BALANCE: `{format_balance(new_balance)} BDT`",
        parse_mode="Markdown"
    )
    try:
        await context.bot.send_message(uid, f"⚠️ ADMIN REMOVED `{format_balance(amount)} BDT` FROM YOUR ACCOUNT!\n💵 NEW BALANCE: `{format_balance(new_balance)} BDT`", parse_mode="Markdown")
    except:
        pass
    context.user_data["remove_balance_mode"] = False
    context.user_data["pending_remove_user"] = None

# ==================== ADMIN PANEL - BAN/UNBAN ====================

async def admin_ban_user_start(update, context):
    context.user_data["admin_ban_mode"] = True
    context.user_data["admin_unban_mode"] = False
    await update.message.reply_text("🚫 SEND TELEGRAM ID TO BAN USER:")

async def admin_unban_user_start(update, context):
    context.user_data["admin_unban_mode"] = True
    context.user_data["admin_ban_mode"] = False
    await update.message.reply_text("🔓 SEND TELEGRAM ID TO UNBAN USER:")

async def process_ban_user(update, context):
    uid_to_ban = update.message.text.strip()
    if not uid_to_ban.isdigit():
        await update.message.reply_text("❌ INVALID USER ID!")
        return
    uid_to_ban_int = int(uid_to_ban)
    if not user_exists(uid_to_ban_int):
        await update.message.reply_text("❌ USER NOT FOUND!")
        context.user_data["admin_ban_mode"] = False
        return
    if is_user_banned(uid_to_ban_int):
        await update.message.reply_text("⚠️ USER IS ALREADY BANNED!")
        context.user_data["admin_ban_mode"] = False
        return
    ban_user(uid_to_ban_int)
    try:
        await context.bot.send_message(uid_to_ban_int, "🚫 **YOU HAVE BEEN BANNED**\n📞 Contact support.", parse_mode="Markdown")
    except:
        pass
    await update.message.reply_text(f"✅ USER `{uid_to_ban}` BANNED!", parse_mode="Markdown", reply_markup=system_config_keyboard())
    context.user_data["admin_ban_mode"] = False

async def process_unban_user(update, context):
    uid_to_unban = update.message.text.strip()
    if not uid_to_unban.isdigit():
        await update.message.reply_text("❌ INVALID USER ID!")
        return
    uid_to_unban_int = int(uid_to_unban)
    if not is_user_banned(uid_to_unban_int):
        await update.message.reply_text("⚠️ THIS USER IS NOT BANNED!")
        context.user_data["admin_unban_mode"] = False
        return
    unban_user(uid_to_unban_int)
    try:
        await context.bot.send_message(uid_to_unban_int, "✅ **YOU HAVE BEEN UNBANNED!** Use /start", parse_mode="Markdown")
    except:
        pass
    await update.message.reply_text(f"✅ USER `{uid_to_unban}` UNBANNED!", parse_mode="Markdown", reply_markup=system_config_keyboard())
    context.user_data["admin_unban_mode"] = False

async def show_banned_users_list(update, context):
    banned_list = load_banned_users()
    if not banned_list:
        await update.message.reply_text("📜 NO BANNED USERS.", reply_markup=system_config_keyboard())
        return
    text = "📜 **BANNED USER LIST**\n━━━━━━━━━━━━━━━━━━━━\n\n"
    for i, uid in enumerate(banned_list, 1):
        text += f"{i}. `{uid}`\n"
    text += f"\n📊 Total: {len(banned_list)}"
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=system_config_keyboard())

# ==================== LIVE TRAFFIC SECTION ====================

def get_live_traffic_stats(minutes=5):
    from collections import Counter
    if not os.path.exists(ACTIVITY_LOGS_FILE):
        return None
    cutoff = datetime.now() - timedelta(minutes=minutes)
    total_numbers = total_otps = 0
    by_app, by_country = Counter(), Counter()
    latest_ts = None
    try:
        with open(ACTIVITY_LOGS_FILE, "r", encoding="utf-8") as f:
            logs = json.load(f)
        if not isinstance(logs, list):
            return None
    except Exception:
        return None

    for entry in logs:
        try:
            ts = datetime.fromisoformat(entry.get("timestamp", ""))
        except Exception:
            continue
        if ts < cutoff:
            continue
        latest_ts = max(latest_ts, ts) if latest_ts else ts
        action = entry.get("action", "")
        details = entry.get("details", {}) or {}
        if action == "NUMBER_TAKEN":
            try:
                count = max(0, int(details.get("count", 1)))
            except (TypeError, ValueError):
                count = 1
            total_numbers += count
            app_name = (details.get("service") or details.get("app") or
                        details.get("sid") or details.get("application"))
            if app_name:
                by_app[str(app_name)] += count
            country = details.get("country")
            if country:
                by_country[str(country)] += count
        elif action == "OTP_RECEIVED":
            total_otps += 1
            sms_text = details.get("sms", "")
            service = detect_service(sms_text) if sms_text else ""
            if service and service != "SMS SERVICE":
                by_app[service] += 1
            number = details.get("number", "")
            if number:
                _, country_name = get_country_info(number)
                if country_name != "Unknown":
                    by_country[country_name] += 1

    return {
        "total_numbers": total_numbers, "total_otps": total_otps,
        "by_app": by_app, "by_country": by_country,
        "latest": latest_ts, "window": minutes,
    }


def build_live_traffic_message(data):
    line = "━" * 20
    if data is None:
        return f"📊 <b>LIVE TRAFFIC</b>\n{line}\n\n⚠️ <i>Activity data unavailable.</i>"
    lines = [
        "📊 <b>LIVE TRAFFIC</b>", line,
        f"⏱ <b>Window:</b> last <b>{data['window']}</b> minutes",
        f"📞 <b>Number Requests:</b> <code>{data['total_numbers']}</code>",
        f"🔑 <b>OTPs Received:</b> <code>{data['total_otps']}</code>", "",
        "📱 <b>By App / Service:</b>",
    ]
    if data["by_app"]:
        lines.extend(f"   • {html.escape(str(k))}: <code>{v}</code>"
                     for k, v in data["by_app"].most_common(10))
    else:
        lines.append("   <i>no data</i>")
    lines.extend(["", "🌍 <b>By Country:</b>"])
    if data["by_country"]:
        lines.extend(f"   • {html.escape(str(k))}: <code>{v}</code>"
                     for k, v in data["by_country"].most_common(10))
    else:
        lines.append("   <i>no data</i>")
    latest = data.get("latest")
    latest_str = latest.strftime("%d %b %Y, %I:%M:%S %p") if latest else "—"
    lines.extend(["", f"🕐 <b>Last update:</b> {latest_str}", line])
    return "\n".join(lines)


def live_traffic_keyboard():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🔄 REFRESH", callback_data="refresh_traffic", style="primary")
    ]])


async def show_live_traffic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_user_banned(uid):
        await update.message.reply_text("🚫 YOU ARE BANNED 🚫",
                                        reply_markup=main_keyboard(uid))
        return
    await update.message.reply_text(
        build_live_traffic_message(get_live_traffic_stats(5)),
        parse_mode="HTML", reply_markup=live_traffic_keyboard()
    )


async def refresh_traffic_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Refreshing...")
    await query.edit_message_text(
        build_live_traffic_message(get_live_traffic_stats(5)),
        parse_mode="HTML", reply_markup=live_traffic_keyboard()
    )


# ==================== MESSAGE HANDLER SECTION ====================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    uid = update.effective_user.id
    text = update.message.text.strip()

    # Admin support reply started from the inline REPLY USER button.
    if is_admin(uid) and context.user_data.get("support_reply_uid"):
        target_uid = int(context.user_data["support_reply_uid"])
        if text == "❌ CANCEL":
            context.user_data.pop("support_reply_uid", None)
            await update.message.reply_text(
                "❌ Support reply cancelled.",
                reply_markup=admin_main_keyboard(),
            )
            return

        context.user_data.pop("support_reply_uid", None)
        try:
            await context.bot.send_message(
                chat_id=target_uid,
                text=(
                    "💬 <b>ADMIN REPLY</b>\n\n"
                    f"{html.escape(text)}"
                ),
                parse_mode="HTML",
                reply_markup=main_keyboard(target_uid),
            )
            await update.message.reply_text(
                f"✅ Reply sent to user <code>{target_uid}</code>.",
                parse_mode="HTML",
                reply_markup=admin_main_keyboard(),
            )
        except Exception:
            await update.message.reply_text(
                "❌ Could not send the reply. The user may have blocked the bot.",
                reply_markup=admin_main_keyboard(),
            )
        return

    # Admin reply by Telegram's native reply action remains supported.
    if is_admin(uid) and update.message.reply_to_message:
        replied_text = update.message.reply_to_message.text or ""
        match = re.search(r"SUPPORT_USER_ID:(\d+)", replied_text)
        if match:
            target_uid = int(match.group(1))
            try:
                await context.bot.send_message(
                    chat_id=target_uid,
                    text=(
                        "💬 <b>ADMIN REPLY</b>\n\n"
                        f"{html.escape(text)}"
                    ),
                    parse_mode="HTML",
                    reply_markup=main_keyboard(target_uid),
                )
                await update.message.reply_text(
                    f"✅ Reply sent to user <code>{target_uid}</code>.",
                    parse_mode="HTML",
                )
            except Exception:
                await update.message.reply_text(
                    "❌ Could not send the reply. The user may have blocked the bot."
                )
            return

    # User support message: send one message to every configured admin.
    if context.user_data.get("support_mode") and not is_admin(uid):
        context.user_data["support_mode"] = False
        user = update.effective_user
        user_name = html.escape(user.full_name or "Unknown")
        username = html.escape(f"@{user.username}" if user.username else "No username")
        support_message = (
            "📩 <b>NEW SUPPORT MESSAGE</b>\n\n"
            f"👤 <b>User:</b> {user_name}\n"
            f"🔗 <b>Username:</b> {username}\n"
            f"🆔 <b>User ID:</b> <code>{uid}</code>\n"
            f"🔐 <code>SUPPORT_USER_ID:{uid}</code>\n\n"
            f"💬 <b>Message:</b>\n{html.escape(text)}"
        )
        sent_count = 0
        admin_ids = get_admin_ids()
        if not admin_ids:
            print(f"Support delivery failed: no valid admin IDs configured for user {uid}")

        delivery_errors = []
        for admin_id in admin_ids:
            if admin_id == uid:
                continue
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=support_message,
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton(
                            "↩️ REPLY USER",
                            callback_data=f"support_reply_{uid}",
                            style="primary",
                        )
                    ]]),
                )
                sent_count += 1
            except Exception as exc:
                error_text = f"{type(exc).__name__}: {exc}"
                delivery_errors.append(f"{admin_id} -> {error_text}")
                print(f"Support delivery failed for user {uid} to admin {admin_id}: {error_text}")

        if delivery_errors and not sent_count:
            print(
                "Support delivery hint: the admin must open the bot and send "
                "/start once before the bot can send private messages."
            )

        if sent_count:
            await update.message.reply_text(
                f"✅ আপনার message {sent_count} জন admin-এর কাছে পাঠানো হয়েছে।\n"
                "Admin reply করলে আপনি এই bot-এ উত্তর পাবেন।",
                reply_markup=main_keyboard(uid),
            )
        else:
            await update.message.reply_text(
                "❌ এখন কোনো admin-এর কাছে message পৌঁছানো যায়নি।\n\n"
                "Admin-কে আগে এই bot খুলে /start দিতে হবে। "
                "তারপর Support থেকে আবার message পাঠান।",
                reply_markup=main_keyboard(uid),
            )
        return

    # Withdraw flow
    if context.user_data.get("withdraw_mode") == "select_method":
        await withdraw_method_selected(update, context)
        return
    if context.user_data.get("withdraw_mode") == "amount":
        await withdraw_amount_received(update, context)
        return
    if context.user_data.get("withdraw_mode") == "number":
        await withdraw_number_received(update, context)
        return

    # Admin balance
    if context.user_data.get("add_balance_mode") and is_admin(uid):
        if context.user_data.get("pending_add_user"):
            await process_add_balance_amount(update, context)
        else:
            await process_add_balance_user(update, context)
        return
    if context.user_data.get("remove_balance_mode") and is_admin(uid):
        if context.user_data.get("pending_remove_user"):
            await process_remove_balance_amount(update, context)
        else:
            await process_remove_balance_user(update, context)
        return

    # Admin ban/unban
    if context.user_data.get("admin_ban_mode") and is_admin(uid):
        await process_ban_user(update, context)
        return
    if context.user_data.get("admin_unban_mode") and is_admin(uid):
        await process_unban_user(update, context)
        return

    # CUSTOM RANGE — user sent a range text
    if context.user_data.get("mode") == "custom_range":
        context.user_data["mode"] = None
        range_text = text.strip().upper()
        if not re.search(r'\d', range_text):
            await update.message.reply_text(
                "❌ <b>INVALID RANGE!</b>\n\n"
                "<blockquote>সঠিক উদাহরণ: <code>234XXX</code></blockquote>",
                parse_mode="HTML",
                reply_markup=main_keyboard(uid)
            )
            return
        await request_queue.put({
            'type': 'process_numbers',
            'update': update,
            'context': context,
            'range_text': range_text,
            'count': get_numbers_per_request()
        })
        return

    # Ban check
    if not is_admin(uid) and is_user_banned(uid):
        await update.message.reply_text("🚫 YOU ARE BANNED 🚫", reply_markup=main_keyboard(uid))
        return

    # Cancel
    if text == "❌ CANCEL":
        context.user_data.clear()
        await update.message.reply_text("❌ CANCELLED", reply_markup=main_keyboard(uid))
        return

    # Main menu buttons
    if text == "👤 PROFILE":
        # Clear any lingering mode so sub-buttons work cleanly
        context.user_data["mode"] = None
        context.user_data["account_menu"] = True
        await update.message.reply_text(
            "👤 <b>PROFILE MENU</b>\n\nSELECT AN OPTION:",
            parse_mode="HTML",
            reply_markup=account_keyboard()
        )
        return

    if text == "🔙 BACK TO MAIN" and context.user_data.get("account_menu"):
        context.user_data["account_menu"] = None
        context.user_data["mode"] = None
        await update.message.reply_text(
            "🔙 Back to main menu.",
            reply_markup=main_keyboard(uid)
        )
        return

    if text == "👤 VIEW PROFILE" and context.user_data.get("account_menu"):
        user_data = get_user(uid)
        stats = get_user_stats(uid)
        user = update.effective_user
        full_name = html.escape(user.full_name)
        username = html.escape(user.username or "No username")
        profile_text = (
            f"👤 <b>YOUR PROFILE</b>\n\n"
            f"<blockquote>🏷️ NAME: <b>{full_name}</b></blockquote>\n"
            f"<blockquote>🆔 USERNAME: @{username}</blockquote>\n"
            f"<blockquote>🗝️ TELEGRAM ID: <code>{uid}</code></blockquote>\n\n"
            f"<blockquote>💵 BALANCE: <b>{format_balance(user_data.get('balance', 0))} BDT</b></blockquote>\n\n"
            f"✨ <b>TODAY</b>\n"
            f"<blockquote>📱 NUMBERS: {stats['today_numbers']}\n🔑 OTPS: {stats['today_otps']}</blockquote>\n\n"
            f"🔥 <b>LAST 7 DAYS</b>\n"
            f"<blockquote>📱 NUMBERS: {stats['last7d_numbers']}\n🔑 OTPS: {stats['last7d_otps']}</blockquote>\n\n"
            f"🌐 <b>ALL TIME</b>\n"
            f"<blockquote>📱 NUMBERS: {stats['total_numbers']}\n🔑 OTPS: {stats['total_otps']}</blockquote>"
        )
        await update.message.reply_text(profile_text, parse_mode="HTML",
                                         reply_markup=account_keyboard())
        return

    if text == "💰 BALANCE" and context.user_data.get("account_menu"):
        balance = get_user(uid)['balance']
        await update.message.reply_text(
            f"💰 <b>YOUR CURRENT BALANCE</b>\n\n"
            f"<blockquote>💵 TOTAL: <b>{format_balance(balance)} BDT</b></blockquote>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("💸 WITHDRAW", callback_data="withdraw_start", style="success")
            ]])
        )
        return

    if text == "🎁 REFER AND EARN" and context.user_data.get("account_menu"):
        await refer_command(update, context)
        return

    # SEARCH OTP
    if text == "SEARCH OTP":
        context.user_data["mode"] = "search_otp"
        await update.message.reply_text("🔍 **ENTER THE NUMBER TO SEARCH OTP:**", parse_mode="Markdown")
        return

    if context.user_data.get("mode") == "search_otp":
        context.user_data["mode"] = None
        await request_queue.put({'type': 'search_otp', 'update': update, 'context': context, 'target_num': normalize_number(text)})
        return

    # GET 2FA
    if text == "🔑 GET 2FA":
        await get_2fa_code(update, context)
        return

    # LIVE TRAFFIC
    if text == "📊 LIVE TRAFFIC":
        await show_live_traffic(update, context)
        return

    # GET NUMBER
    if text == "📞 GET NUMBER":
        await show_app_selection(update, context)
        return

    if context.user_data.get("mode") == "get_2fa":
        await process_2fa_key(update, context)
        return

    # LEADERBOARD
    if text == "🏆 LEADERBOARD":
        await leaderboard_command(update, context)
        return

    # SUPPORT BUTTON HANDLER
    if text == "💬 SUPPORT":
        if is_admin(uid):
            await update.message.reply_text(
                "💬 <b>SUPPORT CHAT</b>\n\n"
                "User-এর message-এর উপর সরাসরি Reply করলে উত্তরটি সেই user-এর কাছে যাবে।",
                parse_mode="HTML",
                reply_markup=main_keyboard(uid),
            )
            return
        context.user_data["support_mode"] = True
        await update.message.reply_text(
            "💬 <b>SUPPORT CHAT</b>\n\n"
            "আপনার সমস্যা বা message লিখে পাঠান। "
            "আমি সেটি admin-এর কাছে পাঠিয়ে দেব।",
            parse_mode="HTML",
            reply_markup=cancel_keyboard(),
        )
        return

    # Admin panel
    if text == "👑 ADMIN PANEL" and is_admin(uid):
        context.user_data["admin_mode"] = "main"
        await update.message.reply_text(
            "⌬━━━━━━━━━━━━━━━━━━━━⌬\n   👑 WELCOME ADMIN PANEL 👑\n⌬━━━━━━━━━━━━━━━━━━━━⌬",
            reply_markup=admin_main_keyboard()
        )
        return

    if text == "🔙 BACK TO MAIN" and context.user_data.get("admin_mode"):
        context.user_data["admin_mode"] = None
        await update.message.reply_text("🔙 Back to main menu.", reply_markup=main_keyboard(uid))
        return

    if text == "🔙 BACK TO ADMIN":
        context.user_data["user_management_mode"] = None
        context.user_data["system_config_mode"] = None
        context.user_data["bot_settings_mode"] = None
        context.user_data["stex_config_mode"] = None
        context.user_data["service_mgmt_mode"] = None
        context.user_data["withdrawal_admin_mode"] = None
        context.user_data["admin_mode"] = "main"
        await update.message.reply_text("🔙 Back to admin panel.", reply_markup=admin_main_keyboard())
        return

    if text == "💬 SUPPORT CHAT" and context.user_data.get("admin_mode") == "main" and is_admin(uid):
        await update.message.reply_text(
            "💬 <b>SUPPORT CHAT</b>\n\n"
            "User-এর message-এর উপর সরাসরি Reply করুন। "
            "আপনার reply automatically সেই user-এর কাছে চলে যাবে।",
            parse_mode="HTML",
            reply_markup=admin_main_keyboard(),
        )
        return

    if text == "💸 WITHDRAWAL MANAGEMENT" and context.user_data.get("admin_mode") == "main" and is_admin(uid):
        context.user_data["withdrawal_admin_mode"] = "main"
        await update.message.reply_text(
            "💸 <b>WITHDRAWAL MANAGEMENT</b>\n\n"
            f"📉 Current minimum: <code>{get_min_withdraw():.2f} BDT</code>",
            parse_mode="HTML",
            reply_markup=withdrawal_management_keyboard(),
        )
        return

    # Direct PENDING WITHDRAWALS from admin_main_keyboard (no sub-mode required)
    if text == "⏳ PENDING WITHDRAWALS" and is_admin(uid):
        await show_pending_withdrawals(update, context)
        return

    if text == "⏳ PENDING WITHDRAWALS" and context.user_data.get("withdrawal_admin_mode") == "main" and is_admin(uid):
        await show_pending_withdrawals(update, context)
        return

    if text == "📉 SET MINIMUM WITHDRAW" and context.user_data.get("withdrawal_admin_mode") == "main" and is_admin(uid):
        context.user_data["withdrawal_admin_mode"] = "set_minimum"
        await update.message.reply_text(
            f"📉 <b>SET MINIMUM WITHDRAW</b>\n\n"
            f"Current amount: <code>{get_min_withdraw():.2f} BDT</code>\n\n"
            "নতুন minimum amount BDT-তে লিখে পাঠান:",
            parse_mode="HTML",
            reply_markup=cancel_keyboard(),
        )
        return

    if context.user_data.get("withdrawal_admin_mode") == "set_minimum" and is_admin(uid):
        try:
            new_minimum = float(text)
        except ValueError:
            await update.message.reply_text(
                "❌ সঠিক amount দিন, যেমন: 50 বা 100",
                reply_markup=cancel_keyboard(),
            )
            return
        if new_minimum <= 0 or new_minimum > MAX_WITHDRAW:
            await update.message.reply_text(
                f"❌ Amount 0-এর বেশি এবং {MAX_WITHDRAW} BDT-এর মধ্যে হতে হবে।",
                reply_markup=cancel_keyboard(),
            )
            return
        settings = load_settings()
        settings["min_withdraw"] = new_minimum
        save_settings(settings)
        context.user_data["withdrawal_admin_mode"] = "main"
        await update.message.reply_text(
            f"✅ <b>MINIMUM WITHDRAW UPDATED</b>\n"
            f"New minimum: <code>{new_minimum:.2f} BDT</code>",
            parse_mode="HTML",
            reply_markup=withdrawal_management_keyboard(),
        )
        return

    if text == "👥 USER MANAGEMENT" and context.user_data.get("admin_mode") == "main" and is_admin(uid):
        context.user_data["user_management_mode"] = "main"
        await update.message.reply_text("👥 User Management:", reply_markup=user_management_keyboard())
        return

    if text == "⚙️ SYSTEM CONFIGURATION" and context.user_data.get("admin_mode") == "main" and is_admin(uid):
        context.user_data["system_config_mode"] = "main"
        await update.message.reply_text("⚙️ System Configuration:", reply_markup=system_config_keyboard())
        return

    if text == "📊 TODAY ALL STATUS" and context.user_data.get("system_config_mode") == "main" and is_admin(uid):
        t_n, t_o, s_n, s_o, tot_n, tot_o = get_global_system_stats()
        msg = (
            f"📊 <b>SYSTEM STATUS</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✨ <b>TODAY</b>\n📱 NUMBERS: {t_n}\n🔑 OTPS: {t_o}\n\n"
            f"🔥 <b>LAST 7 DAYS</b>\n📱 NUMBERS: {s_n}\n🔑 OTPS: {s_o}\n\n"
            f"🌐 <b>ALL TIME</b>\n📱 NUMBERS: {tot_n}\n🔑 OTPS: {tot_o}"
        )
        await update.message.reply_text(msg, parse_mode="HTML")
        return

    if text == "🔍 USER STATUS CHECK" and is_admin(uid):
        context.user_data["mode"] = "input_user_id"
        await update.message.reply_text("🔍 ENTER TELEGRAM ID:", reply_markup=cancel_keyboard())
        return

    if context.user_data.get("mode") == "input_user_id" and is_admin(uid):
        target_uid = text.strip()
        if not target_uid.isdigit():
            await update.message.reply_text("❌ INVALID ID!")
            return
        context.user_data["mode"] = None
        stats = get_user_stats(target_uid)
        msg = (
            f"👤 <b>USER STATUS</b> — <code>{target_uid}</code>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✨ TODAY: 📱 {stats['today_numbers']} | 🔑 {stats['today_otps']}\n"
            f"🔥 7 DAYS: 📱 {stats['last7d_numbers']} | 🔑 {stats['last7d_otps']}\n"
            f"🌐 ALL TIME: 📱 {stats['total_numbers']} | 🔑 {stats['total_otps']}"
        )
        await update.message.reply_text(
            msg, parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📂 CHECK ALL DATA", callback_data=f"full_logs_{target_uid}", style="primary")
            ]])
        )
        return

    if text == "🆔 ALL USER ID" and context.user_data.get("user_management_mode") == "main" and is_admin(uid):
        users = get_all_users()
        if users:
            content = "\n".join(f"{i}. {u}" for i, u in enumerate(users, 1))
            f = io.BytesIO(content.encode()); f.name = f"ALL_USERS_{len(users)}.txt"
            await update.message.reply_document(document=f, caption=f"👥 Total Users: {len(users)}", reply_markup=user_management_keyboard())
        else:
            await update.message.reply_text("No users found.", reply_markup=user_management_keyboard())
        return

    if text == "💰 ALL USER BALANCE" and context.user_data.get("user_management_mode") == "main" and is_admin(uid):
        user_db = load_data(USER_DATA_FILE)
        if user_db:
            total_bal = sum(v.get("balance", 0) for v in user_db.values())
            lines = [f"{i}. {uid_}: {v.get('balance', 0):.2f} BDT" for i, (uid_, v) in enumerate(user_db.items(), 1)]
            content = f"💰 TOTAL BALANCE: {total_bal:.2f} BDT\n\n" + "\n".join(lines)
            f = io.BytesIO(content.encode()); f.name = f"BALANCES_{total_bal:.0f}.txt"
            await update.message.reply_document(document=f, caption=f"💵 Total Balance: {total_bal:.2f} BDT", reply_markup=user_management_keyboard())
        else:
            await update.message.reply_text("No data.", reply_markup=user_management_keyboard())
        return

    if text == "🚫 BAN USER LIST" and is_admin(uid):
        await show_banned_users_list(update, context)
        return

    if text == "🚫 BAN USER" and context.user_data.get("system_config_mode") == "main" and is_admin(uid):
        await admin_ban_user_start(update, context)
        return

    if text == "✅ UNBAN USER" and context.user_data.get("system_config_mode") == "main" and is_admin(uid):
        await admin_unban_user_start(update, context)
        return

    if text == "➕ ADD BALANCE" and context.user_data.get("system_config_mode") == "main" and is_admin(uid):
        await admin_add_balance_start(update, context)
        return

    if text == "➖ REMOVE BALANCE" and context.user_data.get("system_config_mode") == "main" and is_admin(uid):
        await admin_remove_balance_start(update, context)
        return

    # ==================== FIXED BROADCAST (TEXT, PHOTO, VIDEO, FILE, ETC.) ====================
    if text == "📢 SEND MESSAGE TO ALL USERS" and is_admin(uid):
        context.user_data["broadcast_mode"] = True
        await update.message.reply_text(
            "📢 <b>ADMIN BROADCAST SYSTEM (PRO)</b>\n\n"
            "💬 আপনি এখন যা পাঠাবেন (Text, Photo, Video, Document, Voice, Audio, Animation, Sticker) – সকল ইউজারের কাছে প্রফেশনাল হেডারসহ চলে যাবে।\n\n"
            "✨ রেঞ্জ (যেমন: 237XXX) থাকলে তা অটোমেটিক ক্লিক-টু-কপি হয়ে যাবে।", 
            parse_mode="HTML", 
            reply_markup=cancel_keyboard()
        )
        return

    if context.user_data.get("broadcast_mode") and is_admin(uid):
        context.user_data["broadcast_mode"] = False
        
        user_db = load_data(USER_DATA_FILE)
        all_uids = list(user_db.keys())
        
        if not all_uids:
            await update.message.reply_text("❌ পাঠানোর জন্য কোনো ইউজার পাওয়া যায়নি!")
            return

        success_ids, fail_ids = [], []
        status_msg = await update.message.reply_text(f"🚀 <b>ব্রডকাস্ট শুরু হয়েছে...</b>\n🎯 টার্গেট: {len(all_uids)} জন ইউজার।", parse_mode="HTML")

        def format_broadcast_caption(caption_text):
            if not caption_text:
                return "<blockquote>📢 <b>ADMIN NOTICE :</b></blockquote>"
            formatted = re.sub(r'(\d{3,}[xX]{3,})', r'<code>\1</code>', str(caption_text))
            return f"<blockquote>📢 <b>ADMIN NOTICE :</b></blockquote>\n\n{formatted}"

        for user_id_str in all_uids:
            try:
                target_id = int(user_id_str)
                
                # টেক্সট মেসেজ
                if update.message.text:
                    await context.bot.send_message(
                        chat_id=target_id, 
                        text=format_broadcast_caption(update.message.text), 
                        parse_mode="HTML"
                    )
                # ফটো
                elif update.message.photo:
                    caption = format_broadcast_caption(update.message.caption) if update.message.caption else None
                    await context.bot.send_photo(
                        chat_id=target_id,
                        photo=update.message.photo[-1].file_id,
                        caption=caption,
                        parse_mode="HTML" if caption else None
                    )
                # ভিডিও
                elif update.message.video:
                    caption = format_broadcast_caption(update.message.caption) if update.message.caption else None
                    await context.bot.send_video(
                        chat_id=target_id,
                        video=update.message.video.file_id,
                        caption=caption,
                        parse_mode="HTML" if caption else None
                    )
                # ডকুমেন্ট (যেকোনো ফাইল)
                elif update.message.document:
                    caption = format_broadcast_caption(update.message.caption) if update.message.caption else None
                    await context.bot.send_document(
                        chat_id=target_id,
                        document=update.message.document.file_id,
                        caption=caption,
                        parse_mode="HTML" if caption else None
                    )
                # অডিও
                elif update.message.audio:
                    caption = format_broadcast_caption(update.message.caption) if update.message.caption else None
                    await context.bot.send_audio(
                        chat_id=target_id,
                        audio=update.message.audio.file_id,
                        caption=caption,
                        parse_mode="HTML" if caption else None
                    )
                # ভয়েস
                elif update.message.voice:
                    caption = format_broadcast_caption(update.message.caption) if update.message.caption else None
                    await context.bot.send_voice(
                        chat_id=target_id,
                        voice=update.message.voice.file_id,
                        caption=caption,
                        parse_mode="HTML" if caption else None
                    )
                # অ্যানিমেশন (GIF)
                elif update.message.animation:
                    caption = format_broadcast_caption(update.message.caption) if update.message.caption else None
                    await context.bot.send_animation(
                        chat_id=target_id,
                        animation=update.message.animation.file_id,
                        caption=caption,
                        parse_mode="HTML" if caption else None
                    )
                # স্টিকার
                elif update.message.sticker:
                    await context.bot.send_sticker(
                        chat_id=target_id,
                        sticker=update.message.sticker.file_id
                    )
                # অন্য সব কিছু (ফরোয়ার্ড/কপি)
                else:
                    try:
                        await context.bot.copy_message(
                            chat_id=target_id,
                            from_chat_id=update.message.chat_id,
                            message_id=update.message.message_id
                        )
                    except:
                        await context.bot.send_message(
                            chat_id=target_id,
                            text="📢 <b>ADMIN NOTICE :</b>\n\nআপনার জন্য একটি নতুন বার্তা আছে, কিন্তু এটি প্রদর্শন করা সম্ভব হয়নি।",
                            parse_mode="HTML"
                        )
                success_ids.append(user_id_str)
            except Exception as e:
                print(f"Broadcast fail to {user_id_str}: {e}")
                fail_ids.append(user_id_str)
            
            await asyncio.sleep(0.05)

        report_text = (
            f"✅ <b>ADMIN NOTICE COMPLETE !</b>\n\n"
            f"📊 <b>BROADCAST REPORT:</b>\n\n"
            f"<blockquote>✅ SUCCESSFULLY SENT: {len(success_ids)} USERS !</blockquote>\n"
            f"<blockquote>❌ FAILED TO SEND: {len(fail_ids)} USERS !</blockquote>"
        )
        
        await status_msg.delete()
        await context.bot.send_message(chat_id=uid, text=report_text, parse_mode="HTML", reply_markup=main_keyboard(uid))

        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        if success_ids:
            s_file = io.BytesIO(("\n".join(success_ids)).encode()); s_file.name = f"SUCCESS_{random_suffix}.txt"
            await context.bot.send_document(chat_id=uid, document=s_file, caption="✅ Success User List")
        if fail_ids:
            f_file = io.BytesIO(("\n".join(fail_ids)).encode()); f_file.name = f"FAILED_{random_suffix}.txt"
            await context.bot.send_document(chat_id=uid, document=f_file, caption="❌ Failed User List")
        
        return

    # ==================== BOT SETTINGS NAVIGATION ====================
    if text == "🤖 BOT SETTINGS" and context.user_data.get("admin_mode") == "main" and is_admin(uid):
        context.user_data["bot_settings_mode"] = "main"
        context.user_data["stex_config_mode"] = None
        await update.message.reply_text("⚙️ <b>BOT SETTINGS</b>", parse_mode="HTML", reply_markup=bot_settings_keyboard())
        return

    if text == "🔙 BACK TO BOT SETTINGS" and is_admin(uid):
        context.user_data["bot_settings_mode"] = "main"
        context.user_data["stex_config_mode"] = None
        await update.message.reply_text("⚙️ <b>BOT SETTINGS</b>", parse_mode="HTML", reply_markup=bot_settings_keyboard())
        return

    if text == "⚙️ STEX CONFIG" and context.user_data.get("bot_settings_mode") == "main" and is_admin(uid):
        context.user_data["stex_config_mode"] = "main"
        await update.message.reply_text("📡 <b>STEX PANEL CONFIG</b>", parse_mode="HTML", reply_markup=stex_config_keyboard())
        return

    if text == "🛠️ SERVICE MANAGEMENT" and context.user_data.get("admin_mode") == "main" and is_admin(uid):
        context.user_data["service_mgmt_mode"] = "main"
        await update.message.reply_text("🔧 <b>SERVICE MANAGEMENT</b>", parse_mode="HTML", reply_markup=service_management_keyboard())
        return

    # ==================== ADD / REMOVE ADMIN ====================
    if text == "➕ ADD ADMIN" and context.user_data.get("bot_settings_mode") == "main" and is_admin(uid):
        context.user_data["bot_settings_mode"] = "add_admin"
        s = load_settings()
        admin_list = "\n".join(f"• <code>{a}</code>" for a in s.get("admins", []))
        await update.message.reply_text(
            f"➕ <b>ADD ADMIN</b>\n\n<blockquote>Current admins:\n{admin_list}</blockquote>\n\n"
            f"Send the <b>Telegram User ID</b> to add as admin:",
            parse_mode="HTML", reply_markup=cancel_keyboard())
        return

    if context.user_data.get("bot_settings_mode") == "add_admin" and is_admin(uid):
        if not text.lstrip("-").isdigit():
            await update.message.reply_text("❌ Invalid ID! Send a numeric Telegram ID.")
            return
        new_admin_id = int(text)
        s = load_settings()
        admins = s.get("admins", [])
        if new_admin_id in admins:
            await update.message.reply_text("⚠️ This user is already an admin!", reply_markup=bot_settings_keyboard())
        else:
            admins.append(new_admin_id)
            s["admins"] = admins
            save_settings(s)
            await update.message.reply_text(
                f"✅ <b>ADMIN ADDED!</b>\n<blockquote>🆔 ID: <code>{new_admin_id}</code></blockquote>",
                parse_mode="HTML", reply_markup=bot_settings_keyboard())
        context.user_data["bot_settings_mode"] = "main"
        return

    if text == "➖ REMOVE ADMIN" and context.user_data.get("bot_settings_mode") == "main" and is_admin(uid):
        context.user_data["bot_settings_mode"] = "remove_admin"
        s = load_settings()
        admin_list = "\n".join(f"• <code>{a}</code>" for a in s.get("admins", []))
        await update.message.reply_text(
            f"➖ <b>REMOVE ADMIN</b>\n\n<blockquote>Current admins:\n{admin_list}</blockquote>\n\n"
            f"Send the <b>Telegram User ID</b> to remove from admin:",
            parse_mode="HTML", reply_markup=cancel_keyboard())
        return

    if context.user_data.get("bot_settings_mode") == "remove_admin" and is_admin(uid):
        if not text.lstrip("-").isdigit():
            await update.message.reply_text("❌ Invalid ID! Send a numeric Telegram ID.")
            return
        rem_id = int(text)
        s = load_settings()
        admins = s.get("admins", [])
        owners = s.get("owners", [])
        if rem_id in owners and rem_id == uid:
            await update.message.reply_text("❌ Cannot remove yourself (owner)!", reply_markup=bot_settings_keyboard())
        elif rem_id not in admins:
            await update.message.reply_text("⚠️ This user is not an admin!", reply_markup=bot_settings_keyboard())
        else:
            admins.remove(rem_id)
            s["admins"] = admins
            save_settings(s)
            await update.message.reply_text(
                f"✅ <b>ADMIN REMOVED!</b>\n<blockquote>🆔 ID: <code>{rem_id}</code></blockquote>",
                parse_mode="HTML", reply_markup=bot_settings_keyboard())
        context.user_data["bot_settings_mode"] = "main"
        return

    # ==================== SET NUMBER COUNT (numbers per Get Number) ====================
    if text == "🔢 SET NUMBER COUNT" and context.user_data.get("bot_settings_mode") == "main" and is_admin(uid):
        context.user_data["bot_settings_mode"] = "set_number_count"
        await update.message.reply_text(
            f"🔢 <b>SET NUMBER COUNT</b>\n\n<blockquote>Current: <code>{get_numbers_per_request()}</code> number(s) per request</blockquote>\n\n"
            f"Send how many numbers a user gets each time (1 - 10):",
            parse_mode="HTML", reply_markup=cancel_keyboard())
        return

    if context.user_data.get("bot_settings_mode") == "set_number_count" and is_admin(uid):
        val = text.strip()
        if not val.isdigit() or not (1 <= int(val) <= 10):
            await update.message.reply_text("❌ Invalid! Send a number from 1 to 10.")
            return
        s_ = load_settings()
        s_["numbers_per_request"] = int(val)
        save_settings(s_)
        await update.message.reply_text(
            f"✅ <b>NUMBER COUNT SET!</b>\n<blockquote>Users now get <code>{val}</code> number(s) per request.</blockquote>",
            parse_mode="HTML", reply_markup=bot_settings_keyboard())
        context.user_data["bot_settings_mode"] = "main"
        return

    # ==================== SET OTP GROUP LINK ====================
    if text == "🔗 SET OTP GROUP LINK" and context.user_data.get("bot_settings_mode") == "main" and is_admin(uid):
        context.user_data["bot_settings_mode"] = "set_otp_link"
        s = load_settings()
        cur = s.get("otp_group_url", "Not set")
        await update.message.reply_text(
            f"🔗 <b>SET OTP GROUP LINK</b>\n\n<blockquote>Current: <code>{cur}</code></blockquote>\n\n"
            f"Send the new OTP group invite link (e.g. https://t.me/+xxxxx):",
            parse_mode="HTML", reply_markup=cancel_keyboard())
        return

    if context.user_data.get("bot_settings_mode") == "set_otp_link" and is_admin(uid):
        s = load_settings()
        s["otp_group_url"] = text.strip()
        save_settings(s)
        await update.message.reply_text(
            f"✅ <b>OTP GROUP LINK UPDATED!</b>\n<blockquote>{html.escape(text.strip())}</blockquote>",
            parse_mode="HTML", reply_markup=bot_settings_keyboard())
        context.user_data["bot_settings_mode"] = "main"
        return

    # ==================== SET FORCE JOIN CHANNEL ====================
    if text == "📢 FORCE JOIN SYSTEM" and is_admin(uid):
        await send_force_panel(update.message.chat_id, context)
        return

    # ==================== SET OTP FORWARD CHAT ID ====================
    if text == "🆔 SET OTP CHAT ID" and context.user_data.get("bot_settings_mode") == "main" and is_admin(uid):
        context.user_data["bot_settings_mode"] = "set_otp_chat_id"
        s = load_settings()
        cur = s.get("otp_group_chat_id") or "Not set"
        await update.message.reply_text(
            f"📋 <b>SET OTP FORWARD CHAT ID</b>\n\n<blockquote>Current: <code>{cur}</code></blockquote>\n\n"
            f"Send the Chat ID where OTPs are forwarded (e.g. -1001234567890):\n"
            f"Or send <b>DISABLE</b> to clear:",
            parse_mode="HTML", reply_markup=cancel_keyboard())
        return

    if context.user_data.get("bot_settings_mode") == "set_otp_chat_id" and is_admin(uid):
        s = load_settings()
        val = text.strip()
        if val.upper() == "DISABLE":
            s["otp_group_chat_id"] = None
            await update.message.reply_text("✅ <b>OTP Chat ID CLEARED!</b>", parse_mode="HTML", reply_markup=bot_settings_keyboard())
        elif val.lstrip("-").isdigit():
            s["otp_group_chat_id"] = int(val)
            await update.message.reply_text(
                f"✅ <b>OTP CHAT ID SET!</b>\n<blockquote><code>{val}</code></blockquote>",
                parse_mode="HTML", reply_markup=bot_settings_keyboard())
        else:
            await update.message.reply_text("❌ Invalid! Send a numeric chat ID (e.g. -1001234567890)")
            return
        save_settings(s)
        context.user_data["bot_settings_mode"] = "main"
        return

    # ==================== STEX CONFIG HANDLERS ====================
    if text == "🔑 SET API KEY" and context.user_data.get("stex_config_mode") == "main" and is_admin(uid):
        context.user_data["stex_config_mode"] = "set_api_key"
        s = load_settings()
        cur = s.get("stex_api_key", "Not set")
        await update.message.reply_text(
            f"🔑 <b>SET STEX API KEY</b>\n\n<blockquote>Current: <code>{cur[:20]}...</code></blockquote>\n\nSend new API key:",
            parse_mode="HTML", reply_markup=cancel_keyboard())
        return

    if context.user_data.get("stex_config_mode") == "set_api_key" and is_admin(uid):
        s = load_settings()
        s["stex_api_key"] = text.strip()
        save_settings(s)
        await update.message.reply_text(
            f"✅ <b>STEX API KEY UPDATED!</b>\n<blockquote><code>{html.escape(text.strip()[:20])}...</code></blockquote>",
            parse_mode="HTML", reply_markup=stex_config_keyboard())
        context.user_data["stex_config_mode"] = "main"
        return

    if text == "🌐 SET BASE URL" and context.user_data.get("stex_config_mode") == "main" and is_admin(uid):
        context.user_data["stex_config_mode"] = "set_base_url"
        s = load_settings()
        cur = s.get("stex_base_url", "Not set")
        await update.message.reply_text(
            f"🌐 <b>SET STEX BASE URL</b>\n\n<blockquote>Current: <code>{cur}</code></blockquote>\n\nSend new base URL (e.g. https://api.example.com/xxxx/xxxx/@public/api):",
            parse_mode="HTML", reply_markup=cancel_keyboard())
        return

    if context.user_data.get("stex_config_mode") == "set_base_url" and is_admin(uid):
        s = load_settings()
        s["stex_base_url"] = text.strip().rstrip("/")
        save_settings(s)
        await update.message.reply_text(
            f"✅ <b>BASE URL UPDATED!</b>\n<blockquote><code>{html.escape(s['stex_base_url'])}</code></blockquote>",
            parse_mode="HTML", reply_markup=stex_config_keyboard())
        context.user_data["stex_config_mode"] = "main"
        return

    # ---- VoltX panel ----
    if text == "🔑 SET VOLT KEY" and context.user_data.get("stex_config_mode") == "main" and is_admin(uid):
        context.user_data["stex_config_mode"] = "set_volt_key"
        cur = str(load_settings().get("volt_api_key", "Not set"))
        await update.message.reply_text(f"🔑 <b>SET VOLTX API KEY</b>\n\n<blockquote>Current: <code>{html.escape(cur[:20])}</code></blockquote>\n\nSend new API key:",
                                        parse_mode="HTML", reply_markup=cancel_keyboard())
        return
    if context.user_data.get("stex_config_mode") == "set_volt_key" and is_admin(uid):
        s = load_settings(); s["volt_api_key"] = text.strip(); save_settings(s)
        _ranges_cache["updated_at"] = 0
        await update.message.reply_text(f"✅ <b>VOLTX API KEY UPDATED!</b>\n<blockquote><code>{html.escape(text.strip()[:20])}</code></blockquote>",
                                        parse_mode="HTML", reply_markup=stex_config_keyboard())
        context.user_data["stex_config_mode"] = "main"
        return
    if text == "🌐 SET VOLT URL" and context.user_data.get("stex_config_mode") == "main" and is_admin(uid):
        context.user_data["stex_config_mode"] = "set_volt_url"
        cur = str(load_settings().get("volt_base_url", "Not set"))
        await update.message.reply_text(f"🌐 <b>SET VOLTX BASE URL</b>\n\n<blockquote>Current: <code>{html.escape(cur)}</code></blockquote>\n\nSend new base URL (ends with /@public/api):",
                                        parse_mode="HTML", reply_markup=cancel_keyboard())
        return
    if context.user_data.get("stex_config_mode") == "set_volt_url" and is_admin(uid):
        s = load_settings(); s["volt_base_url"] = text.strip().rstrip("/"); save_settings(s)
        _ranges_cache["updated_at"] = 0
        await update.message.reply_text(f"✅ <b>VOLTX BASE URL UPDATED!</b>\n<blockquote><code>{html.escape(s['volt_base_url'])}</code></blockquote>",
                                        parse_mode="HTML", reply_markup=stex_config_keyboard())
        context.user_data["stex_config_mode"] = "main"
        return
    if text.startswith("⚡ VOLT PANEL") and context.user_data.get("stex_config_mode") == "main" and is_admin(uid):
        s = load_settings(); s["volt_enabled"] = not s.get("volt_enabled", True); save_settings(s)
        _ranges_cache["updated_at"] = 0
        await update.message.reply_text("✅ <b>VOLTX PANEL: " + ("ON" if s["volt_enabled"] else "OFF") + "</b>",
                                        parse_mode="HTML", reply_markup=stex_config_keyboard())
        return

    if text.startswith("🔄 AUTO ADD SERVICES") and context.user_data.get("stex_config_mode") == "main" and is_admin(uid):
        s = load_settings()
        s["auto_add_services"] = not s.get("auto_add_services", True)
        save_settings(s)
        _ranges_cache["updated_at"] = 0
        await update.message.reply_text(
            "✅ <b>AUTO ADD SERVICES: " + ("ON" if s["auto_add_services"] else "OFF") + "</b>\n<blockquote>New services found in live ranges "
            + ("are added automatically." if s["auto_add_services"] else "are ignored until you add them.") + "</blockquote>",
            parse_mode="HTML", reply_markup=stex_config_keyboard())
        return

    if text == "📋 SET ALLOWED SERVICES" and context.user_data.get("stex_config_mode") == "main" and is_admin(uid):
        context.user_data["stex_config_mode"] = "set_services"
        s = load_settings()
        cur = ", ".join(s.get("allowed_services", []))
        await update.message.reply_text(
            f"📋 <b>SET ALLOWED STEX SERVICES</b>\n\n<blockquote>Current:\n<code>{cur}</code></blockquote>\n\n"
            f"Send comma-separated list:\n<i>e.g. Instagram,Facebook,WhatsApp,TikTok</i>",
            parse_mode="HTML", reply_markup=cancel_keyboard())
        return

    if context.user_data.get("stex_config_mode") == "set_services" and is_admin(uid):
        services = [x.strip() for x in text.split(",") if x.strip()]
        s = load_settings()
        s["allowed_services"] = services
        save_settings(s)
        _ranges_cache["data"] = {}
        _ranges_cache["updated_at"] = 0
        svc_text = "\n".join(f"• {sv}" for sv in services)
        await update.message.reply_text(
            f"✅ <b>ALLOWED SERVICES UPDATED!</b>\n\n<blockquote>{svc_text}</blockquote>",
            parse_mode="HTML", reply_markup=stex_config_keyboard())
        context.user_data["stex_config_mode"] = "main"
        return

    if text == "📊 VIEW STEX CONFIG" and context.user_data.get("stex_config_mode") == "main" and is_admin(uid):
        s = load_settings()
        api_key = s.get("stex_api_key", "N/A")
        base_url = s.get("stex_base_url", "N/A")
        services = ", ".join(s.get("allowed_services", []))
        otp_link = s.get("otp_group_url", "N/A")
        force_ch = (f"{len(s.get('force_join_channels', []))} channels" if s.get("force_join_enabled", True) else "Disabled")
        otp_chat = s.get("otp_group_chat_id") or "Not set"
        msg = (
            f"📡 <b>STEX PANEL CONFIGURATION</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"<blockquote>🔑 API KEY: <code>{html.escape(api_key[:30])}...</code></blockquote>\n"
            f"<blockquote>🌐 BASE URL: <code>{html.escape(base_url)}</code></blockquote>\n"
            f"<blockquote>⚡ VOLTX: <b>{'ON' if s.get('volt_enabled', True) else 'OFF'}</b>\n🔑 <code>{html.escape(str(s.get('volt_api_key', ''))[:30])}</code>\n🌐 <code>{html.escape(str(s.get('volt_base_url', '')))}</code></blockquote>\n"
            f"<blockquote>📋 ALLOWED SERVICES:\n{html.escape(services)}</blockquote>\n"
            f"<blockquote>🔗 OTP GROUP LINK: {html.escape(otp_link)}</blockquote>\n"
            f"<blockquote>📢 FORCE CHANNEL: {html.escape(str(force_ch))}</blockquote>\n"
            f"<blockquote>📋 OTP CHAT ID: <code>{otp_chat}</code></blockquote>"
        )
        await update.message.reply_text(msg, parse_mode="HTML", reply_markup=stex_config_keyboard())
        return

    # ==================== SERVICE MANAGEMENT HANDLERS ====================
    if text == "📋 LIST SERVICES" and context.user_data.get("service_mgmt_mode") == "main" and is_admin(uid):
        s = load_settings()
        manual = s.get("manual_services", [])
        if not manual:
            await update.message.reply_text("📋 No manual services added yet.", reply_markup=service_management_keyboard())
        else:
            lines = []
            for i, svc in enumerate(manual):
                countries = svc.get("countries", [])
                clines = "\n".join(
                    f"   {c.get('flag','🌍')} {c.get('name','?')} — <code>{', '.join(c.get('ranges',[]))}</code>"
                    for c in countries
                )
                lines.append(f"{i+1}. <b>{html.escape(svc['name'])}</b>\n{clines}")
            msg = f"📋 <b>MANUAL SERVICES ({len(manual)})</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\n" + "\n\n".join(lines)
            await update.message.reply_text(msg, parse_mode="HTML", reply_markup=service_management_keyboard())
        return

    # ── ADD SERVICE: Step 1 — Service Name ──
    if text == "➕ ADD SERVICE" and context.user_data.get("service_mgmt_mode") == "main" and is_admin(uid):
        context.user_data["service_mgmt_mode"] = "add_name"
        await update.message.reply_text(
            "➕ <b>ADD MANUAL SERVICE</b>\n\n"
            "<blockquote>Step 1: Send the <b>Service Name</b>\n"
            "e.g. FACEBOOK, WHATSAPP, INSTAGRAM</blockquote>",
            parse_mode="HTML", reply_markup=cancel_keyboard())
        return

    if context.user_data.get("service_mgmt_mode") == "add_name" and is_admin(uid):
        context.user_data["new_svc_name"] = text.strip().upper()
        context.user_data["new_svc_countries"] = []
        context.user_data["service_mgmt_mode"] = "add_country"
        await update.message.reply_text(
            f"➕ <b>{html.escape(context.user_data['new_svc_name'])}</b>\n\n"
            f"<blockquote>Step 2: Send the <b>Country Name</b>\n"
            f"e.g. Bangladesh, Nigeria, India</blockquote>\n\n"
            f"Send country name ↓",
            parse_mode="HTML", reply_markup=cancel_keyboard())
        return

    # ── ADD SERVICE: DONE — save service (must be checked BEFORE add_country handler) ──
    if text == "DONE" and context.user_data.get("service_mgmt_mode") == "add_country" and is_admin(uid):
        svc_name = context.user_data.get("new_svc_name")
        countries_done = context.user_data.get("new_svc_countries", [])
        if not svc_name or not countries_done:
            await update.message.reply_text("❌ No data to save. Start again.", reply_markup=service_management_keyboard())
            context.user_data["service_mgmt_mode"] = "main"
            return
        s = load_settings()
        manual = s.get("manual_services", [])
        manual.append({"name": svc_name, "countries": countries_done})
        s["manual_services"] = manual
        save_settings(s)
        done_lines = "\n".join(f"  {c['flag']} {c['name']} — <code>{', '.join(c['ranges'])}</code>" for c in countries_done)
        await update.message.reply_text(
            f"✅ <b>SERVICE SAVED!</b>\n\n"
            f"<blockquote>📱 <b>{html.escape(svc_name)}</b>\n{done_lines}</blockquote>",
            parse_mode="HTML", reply_markup=service_management_keyboard())
        context.user_data["service_mgmt_mode"] = "main"
        for k in ["new_svc_name", "new_svc_countries", "new_svc_cur_country"]:
            context.user_data.pop(k, None)
        return

    # ── ADD SERVICE: Step 2 — Country Name ──
    if context.user_data.get("service_mgmt_mode") == "add_country" and is_admin(uid):
        country_name = text.strip().title()
        context.user_data["new_svc_cur_country"] = country_name
        context.user_data["service_mgmt_mode"] = "add_range"
        svc_name = context.user_data.get("new_svc_name", "?")
        countries_done = context.user_data.get("new_svc_countries", [])
        done_text = ""
        if countries_done:
            done_text = "\n\n<blockquote>✅ Already added:\n" + "\n".join(
                f"  {c['flag']} {c['name']}" for c in countries_done) + "</blockquote>"
        await update.message.reply_text(
            f"➕ <b>{html.escape(svc_name)}</b> — 🌍 <b>{html.escape(country_name)}</b>{done_text}\n\n"
            f"<blockquote>Step 3: Send the <b>Range</b> for {html.escape(country_name)}\n\n"
            f"Format: Country Code + XXX\n"
            f"🇧🇩 Bangladesh → <code>880XXX</code>\n"
            f"🇳🇬 Nigeria → <code>234XXX</code>\n"
            f"🇮🇳 India → <code>91XXXXX</code>\n"
            f"🇲🇾 Malaysia → <code>60XXXXX</code>\n"
            f"🇮🇩 Indonesia → <code>62XXXXX</code>\n\n"
            f"Multiple ranges: <code>880XXX, 8801XXX</code></blockquote>",
            parse_mode="HTML", reply_markup=cancel_keyboard())
        return

    # ── ADD SERVICE: Step 3 — Ranges for that country ──
    if context.user_data.get("service_mgmt_mode") == "add_range" and is_admin(uid):
        raw_ranges = [r.strip().upper() for r in text.split(",") if r.strip()]
        country_name = context.user_data.get("new_svc_cur_country", "Unknown")
        # Detect flag from first range
        flag, detected = "🌍", country_name
        if raw_ranges:
            import re as _re
            prefix = _re.sub(r'[xX]+$', '', raw_ranges[0]).strip()
            pfx_d  = _re.sub(r'\D', '', prefix)
            flag, detected = get_country_info(pfx_d)
        countries_done = context.user_data.get("new_svc_countries", [])
        countries_done.append({"name": country_name, "flag": flag, "ranges": raw_ranges})
        context.user_data["new_svc_countries"] = countries_done
        context.user_data["service_mgmt_mode"] = "add_country"
        context.user_data.pop("new_svc_cur_country", None)
        ranges_text = ", ".join(raw_ranges)
        done_lines = "\n".join(f"  {c['flag']} {c['name']} — <code>{', '.join(c['ranges'])}</code>" for c in countries_done)
        await update.message.reply_text(
            f"✅ <b>{flag} {html.escape(country_name)}</b> added!\n"
            f"<blockquote>Ranges: <code>{html.escape(ranges_text)}</code></blockquote>\n\n"
            f"<blockquote>Countries so far:\n{done_lines}</blockquote>\n\n"
            f"Send another <b>Country Name</b> to add more,\n"
            f"or send <b>DONE</b> to save the service.",
            parse_mode="HTML", reply_markup=cancel_keyboard())
        return

    if text == "➖ REMOVE SERVICE" and context.user_data.get("service_mgmt_mode") == "main" and is_admin(uid):
        s = load_settings()
        manual = s.get("manual_services", [])
        if not manual:
            await update.message.reply_text("📋 No services to remove.", reply_markup=service_management_keyboard())
            return
        lines = "\n".join(f"{i+1}. <b>{html.escape(svc['name'])}</b>" for i, svc in enumerate(manual))
        context.user_data["service_mgmt_mode"] = "remove"
        await update.message.reply_text(
            f"➖ <b>REMOVE SERVICE</b>\n\n<blockquote>{lines}</blockquote>\n\n"
            f"Send the <b>number</b> of the service to remove:",
            parse_mode="HTML", reply_markup=cancel_keyboard())
        return

    if context.user_data.get("service_mgmt_mode") == "remove" and is_admin(uid):
        if not text.isdigit():
            await update.message.reply_text("❌ Send a valid number from the list.")
            return
        idx = int(text) - 1
        s = load_settings()
        manual = s.get("manual_services", [])
        if idx < 0 or idx >= len(manual):
            await update.message.reply_text(f"❌ Invalid number! Choose 1-{len(manual)}.")
            return
        removed = manual.pop(idx)
        s["manual_services"] = manual
        save_settings(s)
        await update.message.reply_text(
            f"✅ <b>SERVICE REMOVED!</b>\n<blockquote>📱 {html.escape(removed['name'])}</blockquote>",
            parse_mode="HTML", reply_markup=service_management_keyboard())
        context.user_data["service_mgmt_mode"] = "main"
        return
        return

    # Force join check for regular users
    if not is_admin(uid):
        if not await check_force_join(update, context):
            return

    await update.message.reply_text("🔹 PLEASE USE THE BUTTONS BELOW:", reply_markup=main_keyboard(uid))

# ==================== COMMAND HANDLERS SECTION ====================

async def get1number_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_user_banned(uid):
        await update.message.reply_text("🚫 YOU ARE BANNED 🚫", reply_markup=main_keyboard(uid))
        return
    await show_app_selection(update, context)

async def searchotp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_user_banned(uid):
        await update.message.reply_text("🚫 YOU ARE BANNED 🚫", reply_markup=main_keyboard(uid))
        return
    context.user_data["mode"] = "search_otp"
    await update.message.reply_text("🔍 **ENTER THE NUMBER TO SEARCH OTP:**", parse_mode="Markdown")

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_user_banned(uid):
        await update.message.reply_text("🚫 YOU ARE BANNED 🚫", reply_markup=main_keyboard(uid))
        return
    balance = get_user(uid)['balance']
    await update.message.reply_text(f"💰 BALANCE: `{format_balance(balance)} BDT`", parse_mode="Markdown", reply_markup=main_keyboard(uid))

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_user_banned(uid):
        await update.message.reply_text("🚫 YOU ARE BANNED 🚫", reply_markup=main_keyboard(uid))
        return
    user_data = get_user(uid)
    stats = get_user_stats(uid)
    user = update.effective_user
    profile_text = (
        f"👤 **YOUR PROFILE**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🏷️ NAME: `{user.full_name}`\n"
        f"🆔 USERNAME: @{user.username or 'No username'}\n"
        f"🗝️ ID: `{uid}`\n\n"
        f"💵 BALANCE: {format_balance(user_data.get('balance', 0))} BDT\n\n"
        f"✨ TODAY: 📱 {stats['today_numbers']} | 🔑 {stats['today_otps']}\n"
        f"🔥 7 DAYS: 📱 {stats['last7d_numbers']} | 🔑 {stats['last7d_otps']}\n"
        f"🌐 ALL TIME: 📱 {stats['total_numbers']} | 🔑 {stats['total_otps']}"
    )
    await update.message.reply_text(profile_text, parse_mode="Markdown")

async def refer_command_slash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_user_banned(uid):
        await update.message.reply_text("🚫 YOU ARE BANNED 🚫", reply_markup=main_keyboard(uid))
        return
    await refer_command(update, context)

async def leaderboard_command_slash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_user_banned(uid):
        await update.message.reply_text("🚫 YOU ARE BANNED 🚫", reply_markup=main_keyboard(uid))
        return
    await leaderboard_command(update, context)

# ==================== START & CALLBACK SECTION ====================

def _link_hash(link):
    m = re.search(r"t\.me/(?:\+|joinchat/)([\w\-]+)", str(link or ""))
    return m.group(1) if m else ""

async def force_missing(context, uid):
    """-> (missing channel entries, unverifiable entries). Admin/disabled -> ([], [])."""
    s = load_settings()
    if not s.get("force_join_enabled", True) or is_admin(uid):
        return [], []
    missing, unverified = [], []
    for ch in s.get("force_join_channels", []):
        target = ch.get("chat_id")
        if not target:
            unverified.append(ch); continue
        try:
            member = await context.bot.get_chat_member(target, uid)
            if member.status in ("member", "administrator", "creator") or (member.status == "restricted" and getattr(member, "is_member", True)):
                continue
            missing.append(ch)
        except Exception as e:
            # bot cannot check this channel (not admin / wrong id): do not block users for it
            print(f"Force join: cannot check {target}: {e}")
            unverified.append(ch)
    if unverified:
        try:
            await alert_admin("fj_unverified",
                "⚠️ <b>Force join is NOT enforced for some channel(s)</b>\n"
                + "\n".join(f"• {html.escape(c.get('link') or str(c.get('chat_id')))}" for c in unverified)
                + "\n\n➡️ Make this bot <b>admin</b> in each channel, then post <code>/forcesetup</code> in the channel "
                  "(or <code>/forcesetup 1</code> / <code>/forcesetup 2</code> to pick the channel number).", every=3600)
        except Exception:
            pass
    return missing, unverified

def force_join_markup(missing):
    rows = []
    for i, ch in enumerate(missing, 1):
        url = ch.get("link") or (f"https://t.me/{str(ch.get('chat_id')).lstrip('@')}" if str(ch.get("chat_id", "")).startswith("@") else "")
        if url:
            rows.append([InlineKeyboardButton(f"📢 JOIN CHANNEL {i}" if len(missing) > 1 else "📢 JOIN CHANNEL", url=url, style="primary")])
    rows.append([InlineKeyboardButton("✅ I HAVE JOINED", callback_data="fj_check", style="success")])
    return InlineKeyboardMarkup(rows)

FORCE_JOIN_TEXT = ("⚠️ <b>FORCE JOIN REQUIRED!</b>\n\n"
                   "<blockquote>বট ব্যবহার করতে আগে নিচের সব চ্যানেলে জয়েন করুন।\n"
                   "জয়েন করার পর <b>I HAVE JOINED</b> চাপুন।</blockquote>")

async def check_force_join(update, context):
    """Returns True if user is allowed to proceed. False if they need to join first."""
    uid = update.effective_user.id
    missing, _ = await force_missing(context, uid)
    if not missing:
        return True
    await update.message.reply_text(FORCE_JOIN_TEXT, parse_mode="HTML", reply_markup=force_join_markup(missing))
    return False

async def fj_check_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    missing, _ = await force_missing(context, q.from_user.id)
    if missing:
        await q.answer("❌ আপনি এখনো সব চ্যানেলে জয়েন করেননি!", show_alert=True)
        try: await q.edit_message_reply_markup(reply_markup=force_join_markup(missing))
        except Exception: pass
        return
    await q.answer("✅ Verified!")
    try: await q.message.delete()
    except Exception: pass
    await context.bot.send_message(q.from_user.id, WELCOME_MESSAGE, parse_mode="Markdown")
    await context.bot.send_message(q.from_user.id, "🔹 PLEASE USE THE BUTTONS BELOW:", reply_markup=main_keyboard(q.from_user.id))

async def _force_bind(context, chat, arg=None):
    """Attach a channel's real chat id to a configured force-join entry. Returns the entry or None."""
    s = load_settings()
    chans = s.get("force_join_channels", [])
    target = None
    if arg and str(arg).isdigit() and 1 <= int(arg) <= len(chans):
        target = chans[int(arg) - 1]
    else:
        try:
            full = await context.bot.get_chat(chat.id)
            h = _link_hash(getattr(full, "invite_link", ""))
        except Exception:
            h = ""
        for c in chans:
            if str(c.get("chat_id")) == str(chat.id) or (h and _link_hash(c.get("link")) == h):
                target = c; break
    if not target: return None
    target["chat_id"] = chat.id; target["title"] = chat.title or ""
    save_settings(s)
    return target

async def forcesetup_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Post /forcesetup (or /forcesetup 1|2) inside a channel where this bot is admin."""
    post = update.channel_post
    if not post: return
    parts = (post.text or "").split()
    t = await _force_bind(context, post.chat, parts[1] if len(parts) > 1 else None)
    try: await post.delete()
    except Exception: pass
    if t:
        await _tg_call(BOT_TOKEN, ADMIN_ID, f"✅ <b>Force join linked</b>\n<b>{html.escape(post.chat.title or '')}</b>\nID: <code>{post.chat.id}</code>", None)
    else:
        await _tg_call(BOT_TOKEN, ADMIN_ID, f"⚠️ Could not match <b>{html.escape(post.chat.title or '')}</b> (<code>{post.chat.id}</code>) to a configured link.\nPost <code>/forcesetup 1</code> or <code>/forcesetup 2</code> in that channel to choose the channel number.", None)

async def force_my_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot was made admin in a channel -> try to link it automatically (invite link match)."""
    m = update.my_chat_member
    if not m or m.chat.type != "channel": return
    if m.new_chat_member.status != "administrator": return
    t = await _force_bind(context, m.chat)
    if t:
        await _tg_call(BOT_TOKEN, ADMIN_ID, f"✅ <b>Force join linked automatically</b>\n<b>{html.escape(m.chat.title or '')}</b>\nID: <code>{m.chat.id}</code>", None)

def force_panel_markup():
    s = load_settings()
    on = s.get("force_join_enabled", True)
    rows = [[InlineKeyboardButton("🟢 STATUS: ON" if on else "🔴 STATUS: OFF", callback_data="fj_toggle", style="success" if on else "danger")]]
    for i, c in enumerate(s.get("force_join_channels", [])):
        name = (c.get("title") or str(c.get("chat_id") or c.get("link")))[:28]
        rows.append([InlineKeyboardButton(f"🗑 Delete: {name}", callback_data=f"fj_del_{i}", style="danger")])
    rows.append([InlineKeyboardButton("➕ Add Channel", callback_data="fj_add", style="primary")])
    rows.append([InlineKeyboardButton("🔙 Back", callback_data="fj_back", style="primary")])
    return InlineKeyboardMarkup(rows)

FORCE_PANEL_TEXT = "🔗 <b>FORCE JOIN SYSTEM</b>\nManage channels below:"

async def send_force_panel(chat_id, context):
    await context.bot.send_message(chat_id, FORCE_PANEL_TEXT, parse_mode="HTML", reply_markup=force_panel_markup())

async def fj_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not is_admin(q.from_user.id):
        await q.answer("Admin only", show_alert=True); return
    d = q.data
    s = load_settings()
    if d == "fj_toggle":
        s["force_join_enabled"] = not s.get("force_join_enabled", True)
        save_settings(s)
        await q.answer("Force Join: " + ("ON" if s["force_join_enabled"] else "OFF"))
    elif d.startswith("fj_del_"):
        i = int(d[7:])
        chans = s.get("force_join_channels", [])
        if 0 <= i < len(chans):
            gone = chans.pop(i); save_settings(s)
            await q.answer("Deleted: " + str(gone.get("title") or gone.get("chat_id")))
        else:
            await q.answer("Already removed")
    elif d == "fj_add":
        await q.answer()
        kb = None
        if KeyboardButtonRequestChat:
            rights = None
            try:
                rights = ChatAdministratorRights(is_anonymous=False, can_manage_chat=True, can_delete_messages=False,
                    can_manage_video_chats=False, can_restrict_members=False, can_promote_members=False,
                    can_change_info=False, can_invite_users=True, can_post_messages=False, can_edit_messages=False)
            except Exception:
                rights = None
            req = KeyboardButtonRequestChat(request_id=7, chat_is_channel=True, bot_is_member=True,
                                            **({"bot_administrator_rights": rights} if rights else {}))
            kb = ReplyKeyboardMarkup([[KeyboardButton("✅ Select Force Join Channel", request_chat=req)],
                                      [make_reply_btn("🔙 BACK TO ADMIN", emoji_id="5267490665117275176", style="primary")]],
                                     resize_keyboard=True)
        await context.bot.send_message(q.from_user.id,
            "👇 <b>Select Channel from below:</b>\n<i>(Make sure bot is an admin there)</i>", parse_mode="HTML", reply_markup=kb)
        return
    elif d == "fj_back":
        await q.answer()
        try: await q.message.delete()
        except Exception: pass
        return
    try:
        await q.edit_message_text(FORCE_PANEL_TEXT, parse_mode="HTML", reply_markup=force_panel_markup())
    except Exception:
        pass

class _ChatSharedFilter(MessageFilter):
    def filter(self, message):
        return bool(getattr(message, "chat_shared", None))

async def fj_chat_shared(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin picked a channel with the 'Select Force Join Channel' button."""
    m = update.message
    if not m or not is_admin(m.from_user.id): return
    cid = m.chat_shared.chat_id
    try:
        me = await context.bot.get_chat_member(cid, context.bot.id)
        if me.status not in ("administrator", "creator"):
            raise RuntimeError("bot is not admin")
        chat = await context.bot.get_chat(cid)
    except Exception as e:
        await m.reply_text("❌ <b>Bot is not an admin in that channel.</b>\nMake the bot admin there and select again.", parse_mode="HTML",
                           reply_markup=main_keyboard(m.from_user.id))
        return
    link = f"https://t.me/{chat.username}" if getattr(chat, "username", None) else (getattr(chat, "invite_link", None) or "")
    if not link:
        try: link = await context.bot.export_chat_invite_link(cid)
        except Exception: link = ""
    s = load_settings()
    chans = s.setdefault("force_join_channels", [])
    entry = next((c for c in chans if str(c.get("chat_id")) == str(cid)), None)
    if entry is None:
        entry = {}; chans.append(entry)
    entry.update({"chat_id": cid, "title": chat.title or str(cid), "link": link})
    s["force_join_enabled"] = True
    save_settings(s)
    await m.reply_text("✅ <b>Successfully Selected!</b>", parse_mode="HTML", reply_markup=main_keyboard(m.from_user.id))
    await send_force_panel(m.chat_id, context)

async def forcestatus_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not is_admin(update.effective_user.id): return
    s = load_settings()
    L = [f"📢 <b>FORCE JOIN</b>: {'ON' if s.get('force_join_enabled', True) else 'OFF'}"]
    for i, c in enumerate(s.get("force_join_channels", []), 1):
        L.append(f"{i}. {'✅' if c.get('chat_id') else '⚠️ not linked'} {html.escape(c.get('title') or '')} <code>{c.get('chat_id') or '-'}</code>\n   {html.escape(c.get('link') or '')}")
    L.append("\nLink a channel: make the bot admin there, then post <code>/forcesetup</code> in the channel.")
    await update.message.reply_text("\n".join(L), parse_mode="HTML", disable_web_page_preview=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    uid_str = str(uid)

    existing_data = load_data(USER_DATA_FILE)
    is_new_user = uid_str not in existing_data
    if is_new_user:
        get_user(uid)

    args = context.args
    if args:
        param = args[0]
        if is_range_request(param):
            await request_queue.put({'type': 'auto_number', 'update': update, 'context': context, 'range_text': param})
            return
        elif is_referral_request(param) and is_new_user:
            try:
                referrer_id = int(param)
                if referrer_id != uid and str(referrer_id) in existing_data:
                    current_count = get_referral_count(referrer_id)
                    new_count = current_count + 1
                    update_referral_count(referrer_id, new_count)
                    await update_db_balance(referrer_id, REFERRAL_PRICE)
                    log_global_activity(referrer_id, "REFERRAL_JOINED", {"referred_user": uid})
                    try:
                        await context.bot.send_message(
                            referrer_id,
                            f"🎉 <b>NEW REFERRAL!</b>\n\n<blockquote>🗝️ ID: <code>{uid}</code>\n💰 REWARD: {format_balance(REFERRAL_PRICE)} BDT\n👥 TOTAL REFERS: {new_count}</blockquote>",
                            parse_mode="HTML"
                        )
                    except:
                        pass
            except Exception as e:
                print(f"Referral error: {e}")

    if not await check_force_join(update, context):
        return

    context.user_data.clear()
    await update.message.reply_text(WELCOME_MESSAGE, parse_mode="Markdown")
    await update.message.reply_text("🔹 PLEASE USE THE BUTTONS BELOW:", reply_markup=main_keyboard(uid))

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    data = query.data
    await query.answer()

    if not is_admin(uid) and is_user_banned(uid):
        await query.edit_message_text("🚫 YOU ARE BANNED 🚫")
        return

    # Admin support reply button.
    if data.startswith("support_reply_"):
        if not is_admin(uid):
            await query.answer("Only admins can reply to support messages.", show_alert=True)
            return
        target_uid_text = data.replace("support_reply_", "", 1)
        if not target_uid_text.isdigit():
            await query.answer("Invalid support user.", show_alert=True)
            return
        target_uid = int(target_uid_text)
        context.user_data["support_reply_uid"] = target_uid
        await query.message.reply_text(
            f"✍️ <b>REPLYING TO USER</b> <code>{target_uid}</code>\n\n"
            "এখন আপনার reply লিখে পাঠান।",
            parse_mode="HTML",
            reply_markup=cancel_keyboard(),
        )
        return

    # STEX — APP SELECTION
    if data.startswith("sel_app_"):
        app_name = data[8:]
        top = context.user_data.get("top_ranges_by_app") or (_ranges_cache.get("data") or {})
        if not top or app_name not in top:
            await query.answer("App not found. Please try again.", show_alert=True); return
        ranges = top[app_name].get("ranges", [])
        if not ranges:
            await query.answer("No ranges available for this app right now.", show_alert=True); return
        context.user_data["sel_app"] = app_name
        context.user_data["sel_ranges"] = ranges
        btns, seen = [], {}
        clrs = ["primary", "success", "danger"]
        ci = 0
        for i, r in enumerate(ranges[:24]):
            prefix = re.sub(r'[xX]+$', '', str(r)).strip()
            pfx_d = re.sub(r'\D', '', prefix)
            flag, cname = get_country_info(pfx_d)
            label = f"🌍 {flag} {cname}"
            if label not in seen:
                seen[label] = i
                btns.append(InlineKeyboardButton(label, callback_data=f"sel_rng_{i}",
                    api_kwargs={"style": clrs[ci % len(clrs)]}))
                ci += 1
        rows = [btns[j:j+2] for j in range(0, len(btns), 2)]
        rows.append([InlineKeyboardButton("🔙 BACK", callback_data="back_apps",
                                          api_kwargs={"style": "danger"})])
        await query.message.edit_text(
            f'╭━━━〔 📞 <b>𝗦𝗘𝗟𝗘𝗖𝗧 𝗖𝗢𝗨𝗡𝗧𝗥𝗬</b> 〕━━━╮\n\n'
            f'<blockquote>📱 App: <b>{html.escape(app_name)}</b></blockquote>\n'
            f'<blockquote>🌍 Select your Country:</blockquote>',
            parse_mode="HTML", reply_markup=InlineKeyboardMarkup(rows))
        return

    # STEX — RANGE SELECTION
    if data.startswith("sel_rng_"):
        idx = int(data[8:])
        ranges = context.user_data.get("sel_ranges", [])
        app_name = context.user_data.get("sel_app", "")
        if idx >= len(ranges):
            await query.answer("Range not found. Please try again.", show_alert=True); return
        _safe_task(fast_allocate_number(query, context, ranges[idx], app_name))
        return

    # CUSTOM RANGE
    if data == "custom_range":
        context.user_data["mode"] = "custom_range"
        await query.message.edit_text(
            "╭━━━〔 ⚙️ <b>𝗖𝗨𝗦𝗧𝗢𝗠 𝗥𝗔𝗡𝗚𝗘</b> 〕━━━╮\n\n"
            "<blockquote>📶 Type your custom range.\n"
            "Example: <code>234XXX</code> or <code>225XXX</code></blockquote>\n\n"
            "<blockquote>⌨️ Type range below and Send:</blockquote>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 BACK", callback_data="back_apps",
                                      api_kwargs={"style": "danger"})
            ]]))
        return

    # MANUAL SERVICE — Step 1: show countries
    if data.startswith("manual_svc_"):
        idx = int(data[len("manual_svc_"):])
        s = load_settings()
        manual = s.get("manual_services", [])
        if idx >= len(manual):
            await query.answer("Service not found.", show_alert=True); return
        svc = manual[idx]
        countries = svc.get("countries", [])
        if not countries:
            await query.answer("No countries added for this service yet.", show_alert=True); return

        clrs = ["primary", "success", "danger"]
        btns = []
        for ci, c in enumerate(countries):
            flag = c.get("flag", "🌍")
            cname = c.get("name", "Unknown")
            btns.append(InlineKeyboardButton(
                f"🌍 {flag} {cname}",
                callback_data=f"manual_cnt_{idx}_{ci}",
                api_kwargs={"style": clrs[ci % len(clrs)]}
            ))
        rows = [btns[j:j+2] for j in range(0, len(btns), 2)]
        rows.append([InlineKeyboardButton(
            "🔙 BACK", callback_data="back_apps",
            api_kwargs={"style": "danger"}
        )])
        await query.message.edit_text(
            f'╭━━━〔 🔧 <b>{html.escape(svc["name"])}</b> 〕━━━╮\n\n'
            f'<blockquote>📱 App: <b>{html.escape(svc["name"])}</b></blockquote>\n'
            f'<blockquote>🌍 Select your Country:</blockquote>',
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(rows)
        )
        return

    # MANUAL SERVICE — Step 2: country selected → directly allocate number
    if data.startswith("manual_cnt_"):
        parts = data.split("_")
        svc_idx = int(parts[2])
        cnt_idx = int(parts[3])
        s = load_settings()
        manual = s.get("manual_services", [])
        if svc_idx >= len(manual):
            await query.answer("Service not found.", show_alert=True); return
        svc = manual[svc_idx]
        countries = svc.get("countries", [])
        if cnt_idx >= len(countries):
            await query.answer("Country not found.", show_alert=True); return
        country = countries[cnt_idx]
        ranges = country.get("ranges", [])
        if not ranges:
            await query.answer("No ranges for this country.", show_alert=True); return
        import random
        range_text = random.choice(ranges).strip().upper()
        svc_name = svc["name"]
        _safe_task(fast_allocate_number(query, context, range_text, svc_name))
        return

    # MANUAL SERVICE — Step 3: range selected → allocate number
    if data.startswith("manual_rng_"):
        parts = data.split("_")
        svc_idx = int(parts[2])
        cnt_idx = int(parts[3])
        rng_idx = int(parts[4])
        s = load_settings()
        manual = s.get("manual_services", [])
        if svc_idx >= len(manual):
            await query.answer("Service not found.", show_alert=True); return
        countries = manual[svc_idx].get("countries", [])
        if cnt_idx >= len(countries):
            await query.answer("Country not found.", show_alert=True); return
        ranges = countries[cnt_idx].get("ranges", [])
        if rng_idx >= len(ranges):
            await query.answer("Range not found.", show_alert=True); return
        range_text = ranges[rng_idx].strip().upper()
        svc_name   = manual[svc_idx]["name"]
        _safe_task(fast_allocate_number(query, context, range_text, svc_name))
        return
    # BACK TO APP LIST
    if data in ("back_apps", "back_services"):
        top = context.user_data.get("top_ranges_by_app") or (_ranges_cache.get("data") or {})
        manual_rows = build_manual_service_buttons()
        stex_rows = build_app_buttons_from_cache(top) if top else []
        all_rows = stex_rows + manual_rows
        all_rows.append([InlineKeyboardButton("⚙️ CUSTOM RANGE", callback_data="custom_range",
                                               api_kwargs={"style": "danger"})])
        msg = f'╭━━━〔 📞 <b>𝗦𝗘𝗟𝗘𝗖𝗧 𝗔𝗣𝗣</b> 〕━━━╮\n<blockquote>Select an app to get numbers</blockquote>'
        await query.message.edit_text(msg, parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(all_rows))
        return

    if data == "same_range":
        r_text = last_range.get(uid)
        if r_text:
            try:
                await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📢 OTP GROUP", url=(load_settings().get("otp_group_url") or CONFIG_OTP_GROUP_LINK), style="primary")
                ]]))
            except:
                pass
            await process_numbers(update, context, r_text, get_numbers_per_request())
        return

    # WITHDRAW
    if data == "withdraw_start":
        balance = get_user(uid)['balance']
        min_withdraw = get_min_withdraw()
        if balance < min_withdraw:
            await query.message.reply_text(
                f"<blockquote>💵 BALANCE: {format_balance(balance)} BDT\n📉 MIN WITHDRAW: {min_withdraw:.2f} BDT</blockquote>",
                parse_mode="HTML"
            )
            return
        context.user_data["withdraw_mode"] = "select_method"
        await query.message.reply_text("💳 SELECT YOUR PAYMENT METHOD!", reply_markup=withdraw_method_keyboard())
        return

    if data == "withdraw_confirm":
        await process_withdraw_confirm(update, context)
        return

    if data == "withdraw_cancel":
        await process_withdraw_cancel(update, context)
        return

    if data == "withdraw_admin_back":
        await query.message.edit_text(
            "💸 <b>WITHDRAWAL MANAGEMENT</b>\n\n"
            f"📉 Current minimum: <code>{get_min_withdraw():.2f} BDT</code>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 BACK TO ADMIN", callback_data="withdraw_admin_close", style="primary")
            ]]),
        )
        return

    if data == "withdraw_admin_close":
        await query.message.edit_text("🔙 Open the Admin Panel menu to continue.")
        return

    if data.startswith("admin_approve_"):
        if not is_admin(uid):
            await query.answer("Admin access required.", show_alert=True)
            return
        await admin_approve_withdraw(update, context, data.replace("admin_approve_", ""))
        return

    if data.startswith("admin_reject_"):
        if not is_admin(uid):
            await query.answer("Admin access required.", show_alert=True)
            return
        await admin_reject_withdraw(update, context, data.replace("admin_reject_", ""))
        return

    # COPY / MISC CALLBACKS
    if data.startswith("copy_id_"):
        await query.answer(f"✅ Copied ID: {data.replace('copy_id_', '')}", show_alert=True)
        return

    if data.startswith("copy_text_"):
        await query.answer(f"✅ Copied: {data.replace('copy_text_', '')}", show_alert=True)
        return

    if data.startswith("my_ref_"):
        target_uid = data.replace("my_ref_", "")
        all_logs = load_data(ACTIVITY_LOGS_FILE)
        my_referrals = [log for log in all_logs if str(log.get('uid')) == str(target_uid) and log.get('action') == "REFERRAL_JOINED"]
        content = f"👥 REFERRAL REPORT — {target_uid}\n━━━━━━━━━━━━\nTOTAL: {len(my_referrals)}\n\n"
        for i, log in enumerate(my_referrals, 1):
            try:
                dt_obj = datetime.fromisoformat(log['timestamp'])
                ref_id = log.get('details', {}).get('referred_user', 'N/A')
                content += f"{i}. ID: {ref_id} | {dt_obj.strftime('%d/%m/%Y %I:%M %p')}\n"
            except:
                continue
        f = io.BytesIO(content.encode())
        f.name = f"REF_{target_uid}.txt"
        await context.bot.send_document(chat_id=uid, document=f, caption="✅ **REFERRAL DATA**", parse_mode="Markdown")
        return

    if data.startswith("full_logs_"):
        target_uid = data.replace("full_logs_", "")
        stats = get_user_stats(target_uid)
        all_logs = load_data(ACTIVITY_LOGS_FILE)
        user_db = load_data(USER_DATA_FILE)
        user_info = user_db.get(str(target_uid), {})
        user_otps = [log for log in all_logs if str(log.get('uid')) == str(target_uid) and log.get('action') == "OTP_RECEIVED"]
        content = (
            f"📊 USER DATA REPORT — {target_uid}\n"
            f"💰 BALANCE: {user_info.get('balance', 0):.2f} BDT\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"TODAY NUMBERS: {stats['today_numbers']}\n"
            f"TODAY OTPS: {stats['today_otps']}\n"
            f"7D NUMBERS: {stats['last7d_numbers']}\n"
            f"7D OTPS: {stats['last7d_otps']}\n"
            f"TOTAL NUMBERS: {stats['total_numbers']}\n"
            f"TOTAL OTPS: {stats['total_otps']}\n"
            f"━━━━━━━━━━━━━━━━━━\n\nOTP LOGS:\n"
        )
        for i, log in enumerate(user_otps, 1):
            try:
                dt_obj = datetime.fromisoformat(log['timestamp'])
                d = log.get('details', {})
                content += f"{i}. {dt_obj.strftime('%d/%m/%Y %I:%M %p')}\n   📞 {d.get('number', 'N/A')}\n   🔑 {d.get('otp', 'N/A')}\n\n"
            except:
                continue
        f = io.BytesIO(content.encode())
        f.name = f"USER_{target_uid}.txt"
        await context.bot.send_document(
            chat_id=uid, document=f,
            caption=f"✅ <b>DATA FOR USER: <code>{target_uid}</code></b>",
            parse_mode="HTML"
        )
        return

# ==================== MAIN & POST INIT SECTION ====================

async def post_init(application):
    global BOT_USERNAME
    try:
        BOT_USERNAME = (await application.bot.get_me()).username
    except Exception:
        pass
    try:
        await application.bot.set_my_commands([
            BotCommand("start", "Start the bot"),
            BotCommand("get1number", "Get a number"),
            BotCommand("searchotp", "Search OTP"),
            BotCommand("balance", "Check balance"),
            BotCommand("profile", "Your profile"),
            BotCommand("refer", "Refer and earn"),
            BotCommand("leaderboard", "Leaderboard"),
        ])
    except Exception as e:
        print(f"set_my_commands error: {e}")
    for _ in range(MAX_WORKERS):
        asyncio.create_task(worker())
    asyncio.create_task(monitor_loop(application))
    asyncio.create_task(otp_feed_loop(application))
    asyncio.create_task(_bg_refresh_ranges())

async def post_shutdown(application):
    await client_async.aclose()

def main():
    global BOT_TOKEN
    if _unset(BOT_TOKEN):
        print("\n[SETUP] Telegram bot token is missing.")
        print("1) Open @BotFather in Telegram and create/select your bot.")
        print("2) Copy its NEW API token and paste it below.")
        print("   (The token will be used for this run only; it is not saved to this file.)")
        try:
            BOT_TOKEN = input("Paste Telegram BOT_TOKEN: ").strip()
        except (EOFError, KeyboardInterrupt):
            BOT_TOKEN = ""
        if _unset(BOT_TOKEN):
            raise RuntimeError(
                "BOT_TOKEN is still missing. Start again and paste your BotFather token, "
                "or set it first with: export BOT_TOKEN='YOUR_NEW_TOKEN'"
            )
        if not re.fullmatch(r"\d{5,}:[A-Za-z0-9_-]{20,}", BOT_TOKEN):
            raise RuntimeError(
                "The supplied BOT_TOKEN format looks invalid. Copy the complete token "
                "from @BotFather and try again."
            )

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .concurrent_updates(True)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("get1number", get1number_command))
    app.add_handler(CommandHandler("searchotp", searchotp_command))
    app.add_handler(CommandHandler("balance", balance_command))
    app.add_handler(CommandHandler("profile", profile_command))
    app.add_handler(CommandHandler("refer", refer_command_slash))
    app.add_handler(CommandHandler("leaderboard", leaderboard_command_slash))
    app.add_handler(CommandHandler("feedtest", feedtest_command))
    app.add_handler(CommandHandler("setgroup", setgroup_command))

    app.add_handler(CommandHandler("forcestatus", forcestatus_command))
    app.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POST & filters.Regex(r"^/forcesetup"), forcesetup_channel_post))
    app.add_handler(ChatMemberHandler(force_my_chat_member, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(CallbackQueryHandler(fj_check_callback, pattern=r"^fj_check$"))
    app.add_handler(CallbackQueryHandler(fj_admin_callback, pattern=r"^fj_(toggle|del_\d+|add|back)$"))
    app.add_handler(MessageHandler(_ChatSharedFilter(), fj_chat_shared))
    app.add_handler(MessageHandler(filters.Regex(r"^📊 LIVE TRAFFIC$"), show_live_traffic))
    app.add_handler(CallbackQueryHandler(refresh_traffic_callback, pattern=r"^refresh_traffic$"))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    _start_health_server()
    print("🚀 BOT RUNNING... 😊BoooM")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    import asyncio
    asyncio.set_event_loop(asyncio.new_event_loop())
    main()
