from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Literal
import uuid
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ── Models ────────────────────────────────────────────────────

class AutoReply(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    trigger: str
    response: str
    type: Literal["exact", "contains", "regex"] = "exact"
    active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class AutoReplyCreate(BaseModel):
    trigger: str
    response: str
    type: Literal["exact", "contains", "regex"] = "exact"
    active: bool = True

class AutoReplyUpdate(BaseModel):
    trigger: Optional[str] = None
    response: Optional[str] = None
    type: Optional[Literal["exact", "contains", "regex"]] = None
    active: Optional[bool] = None

class BannedWord(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    word: str
    category: Literal["insultes", "religieux"] = "insultes"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class BannedWordCreate(BaseModel):
    word: str
    category: Literal["insultes", "religieux"] = "insultes"

class Command(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    command: str
    description: str
    category: Literal["IA", "Fun", "Jeux", "Utile"] = "Fun"
    emoji: str = "🤖"
    active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class CommandCreate(BaseModel):
    command: str
    description: str
    category: Literal["IA", "Fun", "Jeux", "Utile"] = "Fun"
    emoji: str = "🤖"
    active: bool = True

class CommandUpdate(BaseModel):
    command: Optional[str] = None
    description: Optional[str] = None
    category: Optional[Literal["IA", "Fun", "Jeux", "Utile"]] = None
    emoji: Optional[str] = None
    active: Optional[bool] = None

class BotSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")
    bot_prefix: str = "!ai"
    language: str = "fr"
    gpt_model: str = "gpt-4o-mini"
    max_tokens: int = 1024
    openai_api_key: str = ""
    auto_delete: bool = True
    notify_group: bool = True
    log_deletions: bool = True
    moderate_dm: bool = False

class ActivityLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str
    message: str
    detail: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ActivityLogCreate(BaseModel):
    type: str
    message: str
    detail: str = ""

# ── Seed initial data ─────────────────────────────────────────

async def seed_data():
    # Seed auto-replies
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

    # Seed banned words (insultes)
    if await db.banned_words.count_documents({}) == 0:
        insultes = ["connard", "connasse", "salope", "pute", "putain", "merde", "enculé", "batard", "fdp", "fils de pute", "ta gueule", "nique", "niquer", "ntm", "tg", "fuck", "bitch", "asshole", "bastard"]
        religieux = ["allah", "الله", "inshallah", "mashallah", "alhamdulillah", "subhanallah", "allahu akbar", "bismillah", "amin", "salam", "coran", "imam", "mosquée", "ramadan", "eid", "prière", "salat", "halal", "haram", "prophète", "muhammad", "sunnah", "hadith", "jannah", "hajj", "omra", "kaaba", "mecca", "medine"]
        docs = []
        for w in insultes:
            docs.append({"id": str(uuid.uuid4()), "word": w, "category": "insultes", "created_at": datetime.now(timezone.utc).isoformat()})
        for w in religieux:
            docs.append({"id": str(uuid.uuid4()), "word": w, "category": "religieux", "created_at": datetime.now(timezone.utc).isoformat()})
        await db.banned_words.insert_many(docs)

    # Seed commands
    if await db.commands.count_documents({}) == 0:
        initial_commands = [
            {"id": str(uuid.uuid4()), "command": "!ai [question]", "description": "Pose une question à ChatGPT", "category": "IA", "emoji": "🤖", "active": True, "created_at": datetime.now(timezone.utc).isoformat()},
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

    # Seed settings
    if await db.settings.count_documents({}) == 0:
        await db.settings.insert_one({
            "bot_prefix": "!ai", "language": "fr", "gpt_model": "gpt-4o-mini",
            "max_tokens": 1024, "openai_api_key": "", "auto_delete": True,
            "notify_group": True, "log_deletions": True, "moderate_dm": False
        })

    # Seed activity logs
    if await db.activity_logs.count_documents({}) == 0:
        logs = [
            {"id": str(uuid.uuid4()), "type": "delete", "message": "Message supprimé", "detail": "Insulte détectée dans #groupe-crous", "timestamp": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid.uuid4()), "type": "autoreply", "message": "Auto-réponse déclenchée", "detail": 'Trigger "faim" → réponse envoyée', "timestamp": datetime.now(timezone.utc).isoformat()},
            {"id": str(uuid.uuid4()), "type": "command", "message": "Commande !ai exécutée", "detail": "Question posée à ChatGPT", "timestamp": datetime.now(timezone.utc).isoformat()},
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

@api_router.post("/auto-replies", response_model=AutoReply)
async def create_auto_reply(data: AutoReplyCreate):
    obj = AutoReply(**data.model_dump())
    await db.auto_replies.insert_one(obj.model_dump())
    return obj

@api_router.put("/auto-replies/{reply_id}", response_model=AutoReply)
async def update_auto_reply(reply_id: str, data: AutoReplyUpdate):
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    await db.auto_replies.update_one({"id": reply_id}, {"$set": update_data})
    item = await db.auto_replies.find_one({"id": reply_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return item

@api_router.delete("/auto-replies/{reply_id}")
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

@api_router.post("/banned-words", response_model=BannedWord)
async def create_banned_word(data: BannedWordCreate):
    existing = await db.banned_words.find_one({"word": data.word.lower()}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=409, detail="Ce mot existe déjà")
    obj = BannedWord(word=data.word.lower(), category=data.category)
    await db.banned_words.insert_one(obj.model_dump())
    return obj

@api_router.delete("/banned-words/{word_id}")
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

@api_router.post("/commands", response_model=Command)
async def create_command(data: CommandCreate):
    obj = Command(**data.model_dump())
    await db.commands.insert_one(obj.model_dump())
    return obj

@api_router.put("/commands/{cmd_id}", response_model=Command)
async def update_command(cmd_id: str, data: CommandUpdate):
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    await db.commands.update_one({"id": cmd_id}, {"$set": update_data})
    item = await db.commands.find_one({"id": cmd_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return item

@api_router.delete("/commands/{cmd_id}")
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

@api_router.put("/settings", response_model=BotSettings)
async def update_settings(data: BotSettings):
    await db.settings.update_one({}, {"$set": data.model_dump()}, upsert=True)
    return data

# ── Activity Logs Routes ──────────────────────────────────────

@api_router.get("/activity", response_model=List[ActivityLog])
async def get_activity():
    items = await db.activity_logs.find({}, {"_id": 0}).sort("timestamp", -1).to_list(100)
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

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
