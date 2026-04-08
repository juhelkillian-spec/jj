from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Request, Depends
from fastapi.responses import Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import aiofiles
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Literal
import uuid
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).parent
UPLOADS_DIR = ROOT_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'crous_bot')

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

app = FastAPI()
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")
api_router = APIRouter(prefix="/api")

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ── In-memory token store (Feature 6: Auth) ───────────────────
valid_tokens: set = set()

# ── Models ────────────────────────────────────────────────────

class AutoReply(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    trigger: str
    response: str
    type: Literal["exact", "contains", "regex"] = "exact"
    active: bool = True
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class AutoReplyCreate(BaseModel):
    trigger: str
    response: str
    type: Literal["exact", "contains", "regex"] = "exact"
    active: bool = True
    image_url: Optional[str] = None
    audio_url: Optional[str] = None

class AutoReplyUpdate(BaseModel):
    trigger: Optional[str] = None
    response: Optional[str] = None
    type: Optional[Literal["exact", "contains", "regex"]] = None
    active: Optional[bool] = None
    image_url: Optional[str] = None
    audio_url: Optional[str] = None

class BannedWord(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    word: str
    category: Literal["insultes", "religieux"] = "insultes"
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class BannedWordCreate(BaseModel):
    word: str
    category: Literal["insultes", "religieux"] = "insultes"
    image_url: Optional[str] = None
    audio_url: Optional[str] = None

class Command(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    command: str
    description: str
    category: Literal["IA", "Fun", "Jeux", "Utile"] = "Fun"
    emoji: str = "🤖"
    active: bool = True
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class CommandCreate(BaseModel):
    command: str
    description: str
    category: Literal["IA", "Fun", "Jeux", "Utile"] = "Fun"
    emoji: str = "🤖"
    active: bool = True
    image_url: Optional[str] = None
    audio_url: Optional[str] = None

class CommandUpdate(BaseModel):
    command: Optional[str] = None
    description: Optional[str] = None
    category: Optional[Literal["IA", "Fun", "Jeux", "Utile"]] = None
    emoji: Optional[str] = None
    active: Optional[bool] = None
    image_url: Optional[str] = None
    audio_url: Optional[str] = None

class BotSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")
    bot_prefix: str = "!bot"
    language: str = "fr"
    gpt_model: str = "gpt-4o-mini"
    max_tokens: int = 1024
    openai_api_key: str = ""
    auto_delete: bool = True
    notify_group: bool = True
    log_deletions: bool = True
    moderate_dm: bool = False
    admin_password: str = ""

class ActivityLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str
    message: str
    detail: str = ""
    content: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ActivityLogCreate(BaseModel):
    type: str
    message: str
    detail: str = ""
    content: str = ""

# ── Feature 4: Whitelist model ────────────────────────────────

class WhitelistEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    phone: str
    name: str = ""
    added_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class WhitelistEntryCreate(BaseModel):
    phone: str
    name: str = ""

# ── Feature 5: Scheduled Messages model ──────────────────────

class ScheduledMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message: str
    cron_time: str
    days: List[str] = ["lun", "mar", "mer", "jeu", "ven"]
    target_group: str = ""
    active: bool = True
    image_url: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ScheduledMessageCreate(BaseModel):
    message: str
    cron_time: str
    days: List[str] = ["lun", "mar", "mer", "jeu", "ven"]
    target_group: str = ""
    active: bool = True
    image_url: Optional[str] = None

class ScheduledMessageUpdate(BaseModel):
    message: Optional[str] = None
    cron_time: Optional[str] = None
    days: Optional[List[str]] = None
    target_group: Optional[str] = None
    active: Optional[bool] = None
    image_url: Optional[str] = None

# ── Feature 6: Auth models ────────────────────────────────────

class LoginRequest(BaseModel):
    password: str

# ── Auth dependency ───────────────────────────────────────────

async def require_auth(request: Request):
    """Dependency: checks auth only if admin_password is set in settings."""
    settings_doc = await db.settings.find_one({}, {"_id": 0})
    admin_password = (settings_doc or {}).get("admin_password", "")
    if not admin_password:
        # No password set — open dashboard
        return
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = auth_header[len("Bearer "):]
    if token not in valid_tokens:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# ── Seed initial data ─────────────────────────────────────────

async def seed_data():
    if await db.auto_replies.count_documents({}) == 0:
        initial_replies = [
            {"id": str(uuid.uuid4()), "trigger": "jsp", "response": "jsp non plus 🤷", "type": "exact", "active": True, "created_at": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid.uuid4()), "trigger": "gg", "response": "gg wp no re 🏆", "type": "exact", "active": True, "created_at": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid.uuid4()), "trigger": "ff", "response": "ff 15 min svp 😭", "type": "exact", "active": True, "created_at": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid.uuid4()), "trigger": "rip", "response": "rip bozo 💀", "type": "exact", "active": True, "created_at": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid.uuid4()), "trigger": "faim", "response": "Va au CROUS alors... ah bah non 😂", "type": "contains", "active": True, "created_at": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid.uuid4()), "trigger": "bot nul", "response": "Toi même tu sais 😒", "type": "contains", "active": True, "created_at": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid.uuid4()), "trigger": "quoi", "response": "feur 😂", "type": "contains", "active": True, "created_at": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid.uuid4()), "trigger": "wifi", "response": "moi je suis connecté h24 à part si vous me débranchez 😂", "type": "contains", "active": True, "created_at": datetime.now(timezone.utc).isoformat()},
        ]
        await db.auto_replies.insert_many(initial_replies)

    if await db.banned_words.count_documents({}) == 0:
        insultes = ["connard", "connasse", "salope", "pute", "putain", "merde", "enculé", "batard", "fdp", "fils de pute", "ta gueule", "nique", "niquer", "ntm", "tg", "fuck", "bitch", "asshole", "bastard"]
        religieux = ["allah", "الله", "inshallah", "mashallah", "alhamdulillah", "subhanallah", "allahu akbar", "bismillah", "amin", "salam", "coran", "imam", "mosquée", "ramadan", "eid", "prière", "salat", "halal", "haram", "prophète", "muhammad", "sunnah", "hadith", "jannah", "hajj", "omra", "kaaba", "mecca", "medine"]
        docs = []
        for w in insultes:
            docs.append({"id": str(uuid.uuid4()), "word": w, "category": "insultes", "created_at": datetime.now(timezone.utc).isoformat()})
        for w in religieux:
            docs.append({"id": str(uuid.uuid4()), "word": w, "category": "religieux", "created_at": datetime.now(timezone.utc).isoformat()})
        await db.banned_words.insert_many(docs)

    if await db.commands.count_documents({}) == 0:
        initial_commands = [
            {"id": str(uuid.uuid4()), "command": "!bot [question]", "description": "Pose une question à ChatGPT", "category": "IA", "emoji": "🤖", "active": True, "created_at": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid.uuid4()), "command": "!manger", "description": "Menu CROUS aléatoire du jour", "category": "Fun", "emoji": "🍽️", "active": True, "created_at": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid.uuid4()), "command": "!blague", "description": "Blague générée par IA", "category": "Fun", "emoji": "😂", "active": True, "created_at": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid.uuid4()), "command": "!motivation", "description": "Citation motivante humoristique", "category": "Fun", "emoji": "💪", "active": True, "created_at": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid.uuid4()), "command": "!excuse", "description": "Excuse absurde pour sécher les cours", "category": "Fun", "emoji": "📝", "active": True, "created_at": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid.uuid4()), "command": "!horoscope", "description": "Horoscope dramatique du jour", "category": "Fun", "emoji": "🔮", "active": True, "created_at": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid.uuid4()), "command": "!météo", "description": "Météo philosophique et drôle", "category": "Fun", "emoji": "🌦️", "active": True, "created_at": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid.uuid4()), "command": "!ragequit", "description": "... (reste quand même)", "category": "Fun", "emoji": "🚪", "active": True, "created_at": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid.uuid4()), "command": "!pile", "description": "Pile ou face", "category": "Jeux", "emoji": "🪙", "active": True, "created_at": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid.uuid4()), "command": "!dé", "description": "Lance un dé à 6 faces", "category": "Jeux", "emoji": "🎲", "active": True, "created_at": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid.uuid4()), "command": "!choisir opt1 opt2", "description": "Choisit une option au hasard", "category": "Jeux", "emoji": "🤔", "active": True, "created_at": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid.uuid4()), "command": "!fact [prénom]", "description": "Roast bienveillant d'une personne", "category": "Jeux", "emoji": "🔥", "active": True, "created_at": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid.uuid4()), "command": "!compliment [prénom]", "description": "Compliment exagéré et hilarant", "category": "Jeux", "emoji": "🌸", "active": True, "created_at": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid.uuid4()), "command": "!sondage [question]", "description": "Crée un sondage de groupe", "category": "Utile", "emoji": "📊", "active": True, "created_at": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid.uuid4()), "command": "!regle", "description": "Affiche les règles du groupe", "category": "Utile", "emoji": "📋", "active": True, "created_at": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid.uuid4()), "command": "!rappel", "description": "Rappel drôle des règles", "category": "Utile", "emoji": "⚠️", "active": True, "created_at": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid.uuid4()), "command": "!licorne", "description": "Liste toutes les commandes", "category": "Utile", "emoji": "🦄", "active": True, "created_at": datetime.now(timezone.utc).isoformat()},
        ]
        await db.commands.insert_many(initial_commands)

    if await db.settings.count_documents({}) == 0:
        await db.settings.insert_one({
            "bot_prefix": "!bot", "language": "fr", "gpt_model": "gpt-4o-mini",
            "max_tokens": 1024, "openai_api_key": "", "auto_delete": True,
            "notify_group": True, "log_deletions": True, "moderate_dm": False,
            "admin_password": ""
        })

    if await db.activity_logs.count_documents({}) == 0:
        logs = [
            {"id": str(uuid.uuid4()), "type": "delete", "message": "Message supprimé", "detail": "Insulte détectée dans #groupe-crous", "timestamp": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid.uuid4()), "type": "autoreply", "message": "Auto-réponse déclenchée", "detail": 'Trigger "faim" → réponse envoyée', "timestamp": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid.uuid4()), "type": "command", "message": "Commande !bot exécutée", "detail": "Question posée à ChatGPT", "timestamp": datetime.now(timezone.utc).isoformat()},
        ]
        await db.activity_logs.insert_many(logs)


@app.on_event("startup")
async def startup():
    await seed_data()

# ── Auto-Replies Routes ───────────────────────────────────────

@api_router.get("/auto-replies", response_model=List[AutoReply])
async def get_auto_replies():
    items = await db.auto_replies.find({}, {"_id": 0}).to_list(1000)
    return items

@api_router.post("/auto-replies", response_model=AutoReply, dependencies=[Depends(require_auth)])
async def create_auto_reply(data: AutoReplyCreate):
    obj = AutoReply(**data.model_dump())
    await db.auto_replies.insert_one(obj.model_dump())
    return obj

@api_router.put("/auto-replies/{reply_id}", response_model=AutoReply, dependencies=[Depends(require_auth)])
async def update_auto_reply(reply_id: str, data: AutoReplyUpdate):
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    await db.auto_replies.update_one({"id": reply_id}, {"$set": update_data})
    item = await db.auto_replies.find_one({"id": reply_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return item

@api_router.delete("/auto-replies/{reply_id}", dependencies=[Depends(require_auth)])
async def delete_auto_reply(reply_id: str):
    result = await db.auto_replies.delete_one({"id": reply_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Not found")
    return {"ok": True}

# ── Banned Words Routes ───────────────────────────────────────

@api_router.get("/banned-words", response_model=List[BannedWord])
async def get_banned_words():
    items = await db.banned_words.find({}, {"_id": 0}).to_list(1000)
    return items

@api_router.post("/banned-words", response_model=BannedWord, dependencies=[Depends(require_auth)])
async def create_banned_word(data: BannedWordCreate):
    existing = await db.banned_words.find_one({"word": data.word.lower()}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=409, detail="Ce mot existe déjà")
    obj = BannedWord(word=data.word.lower(), category=data.category)
    await db.banned_words.insert_one(obj.model_dump())
    return obj

@api_router.delete("/banned-words/{word_id}", dependencies=[Depends(require_auth)])
async def delete_banned_word(word_id: str):
    result = await db.banned_words.delete_one({"id": word_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Not found")
    return {"ok": True}

# ── Commands Routes ───────────────────────────────────────────

@api_router.get("/commands", response_model=List[Command])
async def get_commands():
    items = await db.commands.find({}, {"_id": 0}).to_list(1000)
    return items

@api_router.post("/commands", response_model=Command, dependencies=[Depends(require_auth)])
async def create_command(data: CommandCreate):
    obj = Command(**data.model_dump())
    await db.commands.insert_one(obj.model_dump())
    return obj

@api_router.put("/commands/{cmd_id}", response_model=Command, dependencies=[Depends(require_auth)])
async def update_command(cmd_id: str, data: CommandUpdate):
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    await db.commands.update_one({"id": cmd_id}, {"$set": update_data})
    item = await db.commands.find_one({"id": cmd_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return item

@api_router.delete("/commands/{cmd_id}", dependencies=[Depends(require_auth)])
async def delete_command(cmd_id: str):
    result = await db.commands.delete_one({"id": cmd_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Not found")
    return {"ok": True}

# ── Settings Routes ───────────────────────────────────────────

@api_router.get("/settings", response_model=BotSettings)
async def get_settings():
    s = await db.settings.find_one({}, {"_id": 0})
    if not s:
        return BotSettings()
    return BotSettings(**s)

@api_router.put("/settings", response_model=BotSettings, dependencies=[Depends(require_auth)])
async def update_settings(data: BotSettings):
    await db.settings.update_one({}, {"$set": data.model_dump()}, upsert=True)
    return data

# ── Activity Logs Routes ──────────────────────────────────────

@api_router.get("/activity", response_model=List[ActivityLog])
async def get_activity():
    items = await db.activity_logs.find({}, {"_id": 0}).sort("timestamp", -1).to_list(10000)
    return items

@api_router.post("/activity", response_model=ActivityLog)
async def create_activity(data: ActivityLogCreate):
    obj = ActivityLog(**data.model_dump())
    await db.activity_logs.insert_one(obj.model_dump())
    return obj

# ── Stats Route ───────────────────────────────────────────────

@api_router.get("/stats")
async def get_stats():
    auto_replies_count = await db.auto_replies.count_documents({"active": True})
    banned_insultes = await db.banned_words.count_documents({"category": "insultes"})
    banned_religieux = await db.banned_words.count_documents({"category": "religieux"})
    commands_count = await db.commands.count_documents({"active": True})
    deleted_count = await db.activity_logs.count_documents({"type": "delete"})
    return {
        "auto_replies": auto_replies_count,
        "banned_words": banned_insultes + banned_religieux,
        "banned_insultes": banned_insultes,
        "banned_religieux": banned_religieux,
        "commands": commands_count,
        "messages_deleted": deleted_count,
    }

@api_router.get("/")
async def root():
    return {"message": "WhatsApp Bot Dashboard API"}

# ── Upload fichier media ──────────────────────────────────────

ALLOWED_IMAGE = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
ALLOWED_AUDIO = {".mp4", ".mp3", ".ogg", ".wav", ".m4a"}

@api_router.post("/upload", dependencies=[Depends(require_auth)])
async def upload_file(file: UploadFile = File(...)):
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_IMAGE and ext not in ALLOWED_AUDIO:
        raise HTTPException(status_code=400, detail=f"Format non supporté : {ext}")
    file_id = str(uuid.uuid4())
    filename = f"{file_id}{ext}"
    file_path = UPLOADS_DIR / filename
    async with aiofiles.open(file_path, "wb") as f:
        content = await file.read()
        await f.write(content)
    file_type = "image" if ext in ALLOWED_IMAGE else "audio"
    url = f"/uploads/{filename}"
    return {"url": url, "type": file_type, "filename": filename}

@api_router.delete("/upload/{filename}", dependencies=[Depends(require_auth)])
async def delete_upload(filename: str):
    file_path = UPLOADS_DIR / filename
    if file_path.exists():
        file_path.unlink()
    return {"ok": True}

# ── Générateur index.js ───────────────────────────────────────

import base64
import mimetypes

def file_to_base64(url_path: str) -> tuple:
    try:
        filename = url_path.split("/")[-1]
        file_path = UPLOADS_DIR / filename
        if not file_path.exists():
            return None, None
        with open(file_path, "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")
        mime, _ = mimetypes.guess_type(str(file_path))
        if not mime:
            ext = file_path.suffix.lower()
            mime_map = {".mp4": "video/mp4", ".mp3": "audio/mpeg", ".ogg": "audio/ogg", ".wav": "audio/wav", ".m4a": "audio/mp4"}
            mime = mime_map.get(ext, "application/octet-stream")
        return data, mime
    except Exception:
        return None, None

@api_router.get("/generate-bot")
async def generate_bot():
    commands = await db.commands.find({"active": True}, {"_id": 0}).to_list(1000)
    auto_replies = await db.auto_replies.find({"active": True}, {"_id": 0}).to_list(1000)
    banned_words = await db.banned_words.find({}, {"_id": 0}).to_list(1000)
    settings_doc = await db.settings.find_one({}, {"_id": 0})
    settings = settings_doc or {}
    whitelist_docs = await db.whitelist.find({}, {"_id": 0}).to_list(1000)
    scheduled_docs = await db.scheduled_messages.find({"active": True}, {"_id": 0}).to_list(1000)

    bot_prefix = settings.get("bot_prefix", "!bot")
    gpt_model = settings.get("gpt_model", "gpt-4o-mini")
    max_tokens = settings.get("max_tokens", 1024)
    api_key = settings.get("openai_api_key", "VOTRE_CLE_ICI")
    auto_delete = settings.get("auto_delete", True)
    notify_group = settings.get("notify_group", True)

    dashboard_url = "http://31.185.105.18"

    banned_list = [w["word"] for w in banned_words]
    banned_str = ",\n  ".join(f'"{w}"' for w in banned_list)

    # Whitelist phones array
    whitelist_phones = [e.get("phone", "") for e in whitelist_docs if e.get("phone")]
    whitelist_str = ",\n  ".join(f'"{p}"' for p in whitelist_phones)

    auto_reply_blocks = []
    for r in auto_replies:
        t = r["trigger"].replace('"', '\\"')
        resp = r["response"].replace('"', '\\"').replace('\n', '\\n')
        rtype = r["type"]
        if rtype == "exact":
            cond = f'lower === "{t}"'
        elif rtype == "contains":
            cond = f'lower.includes("{t}")'
        else:
            cond = f'/{t}/i.test(lower)'
        auto_reply_blocks.append(f'  if ({cond}) {{\n    await msg.reply("{resp}");\n    logToDashboard("autoreply", "Auto-réponse déclenchée", \'Trigger "{t}" → réponse envoyée dans \' + (chat.name || msg.from));\n    return;\n  }}')
    auto_replies_code = "\n".join(auto_reply_blocks) if auto_reply_blocks else "  // Aucune auto-réponse active"

    # Scheduled messages JS blocks
    day_map = {"lun": 1, "mar": 2, "mer": 3, "jeu": 4, "ven": 5, "sam": 6, "dim": 0}
    scheduled_blocks = []
    for sm in scheduled_docs:
        msg_text = sm.get("message", "").replace('"', '\\"').replace('\n', '\\n')
        cron_time = sm.get("cron_time", "08:00")
        days = sm.get("days", [])
        target_group = sm.get("target_group", "").replace('"', '\\"')
        day_nums = [str(day_map.get(d, -1)) for d in days if d in day_map]
        day_nums_str = ", ".join(day_nums)
        target_cond = f'chat.name === "{target_group}"' if target_group else "chat.isGroup"
        scheduled_blocks.append(
            f'  // Scheduled: {cron_time} on [{", ".join(days)}]\n'
            f'  if (nowH === "{cron_time}" && [{day_nums_str}].includes(nowDay)) {{\n'
            f'    const chats = await client.getChats();\n'
            f'    for (const chat of chats) {{\n'
            f'      if ({target_cond}) {{\n'
            f'        try {{ await chat.sendMessage("{msg_text}"); }} catch (e) {{}}\n'
            f'      }}\n'
            f'    }}\n'
            f'  }}'
        )
    scheduled_code = "\n".join(scheduled_blocks) if scheduled_blocks else "  // Aucun message programmé actif"

    code = f'''// WhatsApp Bot — Généré par CROUS Dashboard
// API : OpenAI ({gpt_model})
const {{ Client, LocalAuth }} = require("whatsapp-web.js");
const qrcode = require("qrcode-terminal");
const OpenAI = require("openai");
const https = require("https");

const OPENAI_API_KEY = "{api_key}";
const BOT_PREFIX = "{bot_prefix}";
const DASHBOARD_URL = "{dashboard_url}";

function logToDashboard(type, message, detail, content) {{
  const body = JSON.stringify({{ type, message, detail, content: content || "" }});
  const url = new URL(DASHBOARD_URL + "/api/activity");
  const options = {{
    hostname: url.hostname, port: url.port || 80, path: url.pathname,
    method: "POST", headers: {{ "Content-Type": "application/json", "Content-Length": Buffer.byteLength(body) }},
  }};
  const req = (url.protocol === "https:" ? require("https") : require("http")).request(options);
  req.on("error", () => {{}});
  req.write(body);
  req.end();
}}

const BANNED_WORDS = [{banned_str}];

const WHITELIST = [{whitelist_str}];

function escapeRegex(s) {{ return s.replace(/[.*+?^${{}}()|[\\]\\\\]/g, '\\$&'); }}

function shouldDelete(text, senderPhone) {{
  if (WHITELIST.length > 0 && WHITELIST.some(p => senderPhone && senderPhone.includes(p))) return false;
  const lower = text.toLowerCase();
  return BANNED_WORDS.some((word) => new RegExp('\\\\b' + escapeRegex(word) + '\\\\b', 'i').test(lower));
}}

const openai = new OpenAI({{ apiKey: OPENAI_API_KEY }});

async function askChatGPT(question) {{
  try {{
    const response = await openai.chat.completions.create({{
      model: "{gpt_model}", max_tokens: {max_tokens},
      messages: [
        {{ role: "system", content: "Tu es un etudiant, soit concis et de maniere jeune. Réponds en français." }},
        {{ role: "user", content: question }},
      ],
    }});
    return response.choices[0].message.content;
  }} catch (err) {{ return "❌ Désolé, réessaie."; }}
}}

const client = new Client({{
  authStrategy: new LocalAuth({{ dataPath: "./session" }}),
  puppeteer: {{ headless: true, args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--disable-gpu"] }},
}});

client.on("qr", (qr) => {{ qrcode.generate(qr, {{ small: true }}); }});
client.on("ready", () => {{
  console.log("🤖 Bot prêt !");

  // ── Scheduled messages — check every minute ──────────────
  setInterval(async () => {{
    const now = new Date();
    const nowH = now.getHours().toString().padStart(2, "0") + ":" + now.getMinutes().toString().padStart(2, "0");
    const nowDay = now.getDay(); // 0=Sun, 1=Mon, ...
{scheduled_code}
  }}, 60000);
}});

client.on("message", async (msg) => {{
  const text = msg.body || "";
  const chat = await msg.getChat();
  const lower = text.trim().toLowerCase();
  const contact = await msg.getContact();
  const senderPhone = contact.number || msg.from || "";

  if (shouldDelete(text, senderPhone)) {{
    const name = contact.pushname || contact.number || "Quelqu'un";
    try {{ await msg.delete(true); }} catch {{}}
    try {{ await chat.sendMessage("⚠️ *" + name + "* ne respecte pas !regle"); }} catch {{}}
    logToDashboard("delete", "Message supprimé", "Mot interdit par " + name + " dans " + (chat.name || "DM"), text);
    return;
  }}

{auto_replies_code}

  if (lower.startsWith(BOT_PREFIX)) {{
    const question = text.slice(BOT_PREFIX.length).trim();
    if (!question) {{ await msg.reply("👋 Pose une question après *" + BOT_PREFIX + "*"); return; }}
    await chat.sendStateTyping();
    const answer = await askChatGPT(question);
    await msg.reply("🤖 " + answer);
    logToDashboard("command", BOT_PREFIX + " exécutée", question.substring(0, 40));
  }}
}});

client.initialize();
'''
    return {"code": code, "stats": {"commands": len(commands), "auto_replies": len(auto_replies), "banned_words": len(banned_words)}}

# ── Feature 1: Récidivistes ───────────────────────────────────

@api_router.get("/recidivistes")
async def get_recidivistes():
    """
    Aggregates activity_logs where type='delete', extracts person name from
    detail field (format: "Mot interdit par NAME dans GROUPNAME"),
    counts occurrences per person, sorted descending by count.
    """
    pipeline = [
        {"$match": {"type": "delete"}},
        {"$addFields": {
            "parsed_name": {
                "$trim": {
                    "input": {
                        "$arrayElemAt": [
                            {"$split": [
                                {"$arrayElemAt": [{"$split": ["$detail", " par "]}, 1]},
                                " dans "
                            ]},
                            0
                        ]
                    }
                }
            }
        }},
        {"$group": {
            "_id": "$parsed_name",
            "count": {"$sum": 1},
            "last_message": {"$last": "$content"},
            "last_seen": {"$last": "$timestamp"}
        }},
        {"$match": {"_id": {"$ne": None}, "_id": {"$ne": ""}}},
        {"$sort": {"count": -1}},
        {"$project": {
            "_id": 0,
            "name": "$_id",
            "count": 1,
            "last_message": 1,
            "last_seen": 1
        }}
    ]
    results = await db.activity_logs.aggregate(pipeline).to_list(1000)
    return results

# ── Feature 2: Backup / Restore ───────────────────────────────

@api_router.get("/backup")
async def backup_data():
    """Returns all data from all collections (excluding _id)."""
    auto_replies = await db.auto_replies.find({}, {"_id": 0}).to_list(10000)
    banned_words = await db.banned_words.find({}, {"_id": 0}).to_list(10000)
    commands = await db.commands.find({}, {"_id": 0}).to_list(10000)
    settings_list = await db.settings.find({}, {"_id": 0}).to_list(10)
    whitelist = await db.whitelist.find({}, {"_id": 0}).to_list(10000)
    scheduled_messages = await db.scheduled_messages.find({}, {"_id": 0}).to_list(10000)
    return {
        "auto_replies": auto_replies,
        "banned_words": banned_words,
        "commands": commands,
        "settings": settings_list,
        "whitelist": whitelist,
        "scheduled_messages": scheduled_messages,
    }

@api_router.post("/restore", dependencies=[Depends(require_auth)])
async def restore_data(payload: dict):
    """
    Accepts a backup JSON object. For each collection present in the body,
    drops existing data and inserts the new data.
    """
    collection_map = {
        "auto_replies": db.auto_replies,
        "banned_words": db.banned_words,
        "commands": db.commands,
        "settings": db.settings,
        "whitelist": db.whitelist,
        "scheduled_messages": db.scheduled_messages,
    }
    restored = []
    for key, collection in collection_map.items():
        if key in payload and isinstance(payload[key], list):
            await collection.delete_many({})
            if payload[key]:
                await collection.insert_many(payload[key])
            restored.append(key)
    return {"ok": True, "restored": restored}

# ── Feature 3: PWA / Mobile Dashboard ────────────────────────

@app.get("/manifest.json")
async def pwa_manifest():
    manifest = {
        "name": "CROUS BOT Dashboard",
        "short_name": "CROUS BOT",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#030305",
        "theme_color": "#10B981",
        "icons": [
            {
                "src": "/api/pwa-icon",
                "sizes": "512x512",
                "type": "image/png"
            }
        ]
    }
    return JSONResponse(content=manifest)

@api_router.get("/pwa-icon")
async def pwa_icon():
    svg = """<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
  <rect width="512" height="512" rx="80" fill="#030305"/>
  <!-- Robot head -->
  <rect x="136" y="160" width="240" height="200" rx="30" fill="#10B981"/>
  <!-- Eyes -->
  <circle cx="196" cy="230" r="28" fill="#030305"/>
  <circle cx="316" cy="230" r="28" fill="#030305"/>
  <circle cx="196" cy="230" r="14" fill="#10B981"/>
  <circle cx="316" cy="230" r="14" fill="#10B981"/>
  <!-- Mouth -->
  <rect x="176" y="300" width="160" height="30" rx="15" fill="#030305"/>
  <rect x="196" y="308" width="24" height="14" rx="4" fill="#10B981"/>
  <rect x="232" y="308" width="24" height="14" rx="4" fill="#10B981"/>
  <rect x="268" y="308" width="24" height="14" rx="4" fill="#10B981"/>
  <rect x="304" y="308" width="24" height="14" rx="4" fill="#10B981"/>
  <!-- Antenna -->
  <rect x="244" y="110" width="24" height="56" rx="12" fill="#10B981"/>
  <circle cx="256" cy="100" r="20" fill="#10B981"/>
  <!-- Ears / side bolts -->
  <rect x="100" y="205" width="36" height="50" rx="10" fill="#10B981"/>
  <rect x="376" y="205" width="36" height="50" rx="10" fill="#10B981"/>
  <!-- Body -->
  <rect x="176" y="370" width="160" height="80" rx="20" fill="#10B981"/>
  <!-- Arms -->
  <rect x="80" y="375" width="96" height="36" rx="18" fill="#10B981"/>
  <rect x="336" y="375" width="96" height="36" rx="18" fill="#10B981"/>
</svg>"""
    return Response(content=svg, media_type="image/svg+xml")

# ── Feature 4: Whitelist ──────────────────────────────────────

@api_router.get("/whitelist", response_model=List[WhitelistEntry])
async def get_whitelist():
    items = await db.whitelist.find({}, {"_id": 0}).to_list(1000)
    return items

@api_router.post("/whitelist", response_model=WhitelistEntry, dependencies=[Depends(require_auth)])
async def add_whitelist_entry(data: WhitelistEntryCreate):
    obj = WhitelistEntry(phone=data.phone, name=data.name)
    await db.whitelist.insert_one(obj.model_dump())
    return obj

@api_router.delete("/whitelist/{entry_id}", dependencies=[Depends(require_auth)])
async def delete_whitelist_entry(entry_id: str):
    result = await db.whitelist.delete_one({"id": entry_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Not found")
    return {"ok": True}

# ── Feature 5: Scheduled Messages ────────────────────────────

@api_router.get("/scheduled", response_model=List[ScheduledMessage])
async def get_scheduled():
    items = await db.scheduled_messages.find({}, {"_id": 0}).to_list(1000)
    return items

@api_router.post("/scheduled", response_model=ScheduledMessage, dependencies=[Depends(require_auth)])
async def create_scheduled(data: ScheduledMessageCreate):
    obj = ScheduledMessage(**data.model_dump())
    await db.scheduled_messages.insert_one(obj.model_dump())
    return obj

@api_router.put("/scheduled/{msg_id}", response_model=ScheduledMessage, dependencies=[Depends(require_auth)])
async def update_scheduled(msg_id: str, data: ScheduledMessageUpdate):
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    await db.scheduled_messages.update_one({"id": msg_id}, {"$set": update_data})
    item = await db.scheduled_messages.find_one({"id": msg_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return item

@api_router.delete("/scheduled/{msg_id}", dependencies=[Depends(require_auth)])
async def delete_scheduled(msg_id: str):
    result = await db.scheduled_messages.delete_one({"id": msg_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Not found")
    return {"ok": True}

# ── Feature 6: Auth / Admin Login ────────────────────────────

@api_router.post("/login")
async def login(data: LoginRequest):
    settings_doc = await db.settings.find_one({}, {"_id": 0})
    admin_password = (settings_doc or {}).get("admin_password", "")
    if not admin_password:
        # No password set — always succeed
        token = str(uuid.uuid4())
        valid_tokens.add(token)
        return {"ok": True, "token": token}
    if data.password != admin_password:
        raise HTTPException(status_code=401, detail="Mot de passe incorrect")
    token = str(uuid.uuid4())
    valid_tokens.add(token)
    return {"ok": True, "token": token}

@api_router.get("/auth-check")
async def auth_check(request: Request):
    settings_doc = await db.settings.find_one({}, {"_id": 0})
    admin_password = (settings_doc or {}).get("admin_password", "")
    if not admin_password:
        return {"authenticated": True}
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = auth_header[len("Bearer "):]
    if token not in valid_tokens:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return {"authenticated": True}


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
