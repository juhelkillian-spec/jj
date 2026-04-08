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

# ── Générateur index.js ───────────────────────────────────────

@api_router.get("/generate-bot")
async def generate_bot():
    commands = await db.commands.find({"active": True}, {"_id": 0}).to_list(1000)
    auto_replies = await db.auto_replies.find({"active": True}, {"_id": 0}).to_list(1000)
    banned_words = await db.banned_words.find({}, {"_id": 0}).to_list(1000)
    settings_doc = await db.settings.find_one({}, {"_id": 0})
    settings = settings_doc or {}

    bot_prefix = settings.get("bot_prefix", "!ai")
    gpt_model = settings.get("gpt_model", "gpt-4o-mini")
    max_tokens = settings.get("max_tokens", 1024)
    api_key = settings.get("openai_api_key", "VOTRE_CLE_ICI")
    auto_delete = settings.get("auto_delete", True)
    notify_group = settings.get("notify_group", True)

    banned_list = [w["word"] for w in banned_words]
    banned_str = ",\n  ".join(f'"{w}"' for w in banned_list)

    # Génération des auto-réponses
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
        auto_reply_blocks.append(
            f'  if ({cond}) {{\n'
            f'    await msg.reply("{resp}");\n'
            f'    logToDashboard("autoreply", "Auto-réponse déclenchée", \'Trigger "{t}" → réponse envoyée dans \' + (chat.name || msg.from));\n'
            f'    return;\n'
            f'  }}'
        )
    auto_replies_code = "\n".join(auto_reply_blocks) if auto_reply_blocks else "  // Aucune auto-réponse active"

    # Génération des commandes custom (non-builtin)
    builtin_cmds = {"!ai", "!manger", "!pile", "!dé", "!choisir", "!blague", "!motivation", "!fact", "!compliment", "!excuse", "!horoscope", "!ragequit", "!sondage", "!rappel", "!météo", "!meteo", "!licorne", "!regle"}
    custom_commands = [c for c in commands if c["command"].split(" ")[0].lower() not in builtin_cmds]

    custom_cmd_blocks = []
    for c in custom_commands:
        cmd_trigger = c["command"].split(" ")[0].lower().replace('"', '\\"')
        desc = c["description"].replace('"', '\\"')
        emoji = c.get("emoji", "🤖")
        custom_cmd_blocks.append(
            f'  if (lower === "{cmd_trigger}") {{\n'
            f'    await msg.reply("{emoji} *{desc}*");\n'
            f'    logToDashboard("command", "Commande {cmd_trigger} exécutée", \'Utilisée dans \' + (chat.name || msg.from));\n'
            f'    return;\n'
            f'  }}'
        )
    custom_cmds_code = "\n\n".join(custom_cmd_blocks) if custom_cmd_blocks else "  // Aucune commande custom"

    # Liste !licorne dynamique
    licorne_lines = []
    by_cat = {}
    for c in commands:
        cat = c.get("category", "Fun")
        by_cat.setdefault(cat, []).append(c)
    for cat, cmds in by_cat.items():
        licorne_lines.append(f"*{cat} :*")
        for c in cmds:
            licorne_lines.append(f"`{c['command']}` — {c['description']}")
        licorne_lines.append("")
    licorne_str = "\\\\n".join(licorne_lines)

    dashboard_url = "https://how-to-use-48.preview.emergentagent.com"

    notify_line = (
        f'await chat.sendMessage(\'nhaaaaaaa ca respecte pas les regles fais !regle pour les voir\');'
        if notify_group else ""
    )
    delete_block = f"""
  if (shouldDelete(text)) {{
    try {{
      {'await msg.delete(true);' if auto_delete else '// suppression désactivée'}
      const groupName = chat.name || msg.from;
      console.log(`🗑️  Supprimé [${{groupName}}] : "${{text.substring(0, 50)}}"`);
      logToDashboard("delete", "Message supprimé", `Mot interdit dans ${{groupName}} : "${{text.substring(0, 30)}}"`);
      if (chat.isGroup) {{ {notify_line} }}
    }} catch (err) {{
      console.warn("⚠️  Impossible de supprimer :", err.message);
    }}
    return;
  }}""" if auto_delete else ""

    code = f'''// ============================================================
//  WhatsApp Bot — Généré automatiquement par CROUS Dashboard
//  API : OpenAI ({gpt_model})
//  Dépendances : whatsapp-web.js, qrcode-terminal, openai
// ============================================================

const {{ Client, LocalAuth }} = require("whatsapp-web.js");
const qrcode = require("qrcode-terminal");
const OpenAI = require("openai");
const https = require("https");

// ── Configuration ─────────────────────────────────────────────
const OPENAI_API_KEY = "{api_key}";
const BOT_PREFIX = "{bot_prefix}";
const DASHBOARD_URL = "{dashboard_url}";

// ── Envoi de logs au dashboard ────────────────────────────────
function logToDashboard(type, message, detail) {{
  const body = JSON.stringify({{ type, message, detail }});
  const url = new URL(DASHBOARD_URL + "/api/activity");
  const options = {{
    hostname: url.hostname,
    port: 443,
    path: url.pathname,
    method: "POST",
    headers: {{ "Content-Type": "application/json", "Content-Length": Buffer.byteLength(body) }},
  }};
  const req = https.request(options);
  req.on("error", () => {{}});
  req.write(body);
  req.end();
}}

// ── Mots bannis ───────────────────────────────────────────────
const BANNED_WORDS = [
  {banned_str}
];

function shouldDelete(text) {{
  const lower = text.toLowerCase();
  return BANNED_WORDS.some((word) => lower.includes(word));
}}

// ── Client OpenAI ─────────────────────────────────────────────
const openai = new OpenAI({{ apiKey: OPENAI_API_KEY }});

async function askChatGPT(question) {{
  try {{
    const response = await openai.chat.completions.create({{
      model: "{gpt_model}",
      max_tokens: {max_tokens},
      messages: [
        {{ role: "system", content: "Tu es un etudiant, soit concis et de maniere jeune. Réponds en français sauf si l\\'utilisateur écrit dans une autre langue." }},
        {{ role: "user", content: question }},
      ],
    }});
    return response.choices[0].message.content;
  }} catch (err) {{
    return "❌ Désolé, réessaie dans un moment.";
  }}
}}

async function getAI(prompt, system) {{
  const r = await openai.chat.completions.create({{
    model: "{gpt_model}", max_tokens: 200,
    messages: [{{ role: "system", content: system }}, {{ role: "user", content: prompt }}],
  }});
  return r.choices[0].message.content;
}}

// ── Client WhatsApp ───────────────────────────────────────────
const client = new Client({{
  authStrategy: new LocalAuth({{ dataPath: "./session" }}),
  puppeteer: {{ headless: true, args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--disable-gpu"] }},
}});

client.on("qr", (qr) => {{ console.log("\\n📱 Scanne ce QR code avec WhatsApp :\\n"); qrcode.generate(qr, {{ small: true }}); }});
client.on("authenticated", () => console.log("✅ Authentifié !"));
client.on("ready", () => console.log(`🤖 Bot prêt ! Préfixe IA: "${{BOT_PREFIX}}" | ${{BANNED_WORDS.length}} mots surveillés`));

// ── Menus CROUS ───────────────────────────────────────────────
const MENUS_CROUS = [
  "🍝 Lasagnes bolognaise + salade verte + yaourt",
  "🍗 Poulet rôti + riz cantonais + compote",
  "🐟 Cabillaud sauce citron + purée + fruit",
  "🥩 Steak haché + frites + fromage blanc",
  "🥗 Quiche lorraine + salade + crème caramel",
  "🍲 Gratin dauphinois + jambon + mousse chocolat",
  "🌮 Chili con carne + pain + flan",
  "🍜 Soupe + croque-monsieur + salade de fruits",
];

// ── Traitement des messages ───────────────────────────────────
client.on("message", async (msg) => {{
  const text = msg.body || "";
  const chat = await msg.getChat();
  const lower = text.trim().toLowerCase();
{delete_block}
  // ── Auto-réponses (générées depuis le dashboard) ──────────
{auto_replies_code}

  // ── Commandes builtin ─────────────────────────────────────
  if (lower === "!manger") {{
    const menu = MENUS_CROUS[Math.floor(Math.random() * MENUS_CROUS.length)];
    await msg.reply(`🍽️ *Menu du CROUS :*\\n\\n${{menu}}\\n\\nBon appétit... ou pas 😅`);
    logToDashboard("command", "Commande !manger exécutée", `Menu envoyé dans ${{chat.name || msg.from}}`);
    return;
  }}

  if (lower === "!pile") {{
    await msg.reply(Math.random() < 0.5 ? "🪙 PILE !" : "🪙 FACE !");
    logToDashboard("command", "Commande !pile exécutée", `Dans ${{chat.name || msg.from}}`);
    return;
  }}
  if (lower === "!dé") {{
    await msg.reply(`🎲 Le dé donne : *${{Math.floor(Math.random() * 6) + 1}}*`);
    logToDashboard("command", "Commande !dé exécutée", `Dans ${{chat.name || msg.from}}`);
    return;
  }}

  if (lower.startsWith("!choisir ")) {{
    const options = text.slice(9).trim().split(" ");
    if (options.length < 2) {{ await msg.reply("❌ Donne au moins 2 options !"); return; }}
    await msg.reply(`🤔 J\\'ai choisi : *${{options[Math.floor(Math.random() * options.length)]}}* !`);
    logToDashboard("command", "Commande !choisir exécutée", `Dans ${{chat.name || msg.from}}`);
    return;
  }}

  if (lower === "!blague") {{
    await chat.sendStateTyping();
    await msg.reply(`😂 *Blague :*\\n\\n${{await getAI("Raconte une blague drôle.", "Tu racontes des blagues courtes et drôles en français.")}}`);
    logToDashboard("command", "Commande !blague exécutée", `Blague IA envoyée dans ${{chat.name || msg.from}}`);
    return;
  }}

  if (lower === "!motivation") {{
    await chat.sendStateTyping();
    await msg.reply(`💪 *Citation :*\\n\\n${{await getAI("Donne une citation motivante.", "Tu donnes des citations motivantes humoristiques pour étudiants CROUS.")}}`);
    logToDashboard("command", "Commande !motivation exécutée", `Dans ${{chat.name || msg.from}}`);
    return;
  }}

  if (lower.startsWith("!fact ")) {{
    await chat.sendStateTyping();
    const cible = text.slice(6).trim();
    await msg.reply(`🔥 *Roast :*\\n\\n${{await getAI(`Roast drôle pour ${{cible}}`, "Tu fais des roasts drôles et bienveillants en français.")}}`);
    logToDashboard("command", "Commande !fact exécutée", `Roast pour ${{cible}} dans ${{chat.name || msg.from}}`);
    return;
  }}

  if (lower.startsWith("!compliment ")) {{
    await chat.sendStateTyping();
    const cible2 = text.slice(12).trim();
    await msg.reply(`🌸 *Compliment :*\\n\\n${{await getAI(`Compliment exagéré pour ${{cible2}}`, "Tu fais des compliments exagérés et hilarants.")}}`);
    logToDashboard("command", "Commande !compliment exécutée", `Compliment pour ${{cible2}} dans ${{chat.name || msg.from}}`);
    return;
  }}

  if (lower === "!excuse") {{
    await chat.sendStateTyping();
    await msg.reply(`📝 *Excuse :*\\n\\n${{await getAI("Invente une excuse absurde pour ne pas aller en cours.", "Tu inventes des excuses absurdes en français.")}}`);
    logToDashboard("command", "Commande !excuse exécutée", `Dans ${{chat.name || msg.from}}`);
    return;
  }}

  if (lower === "!horoscope") {{
    await chat.sendStateTyping();
    const signes = ["Bélier","Taureau","Gémeaux","Cancer","Lion","Vierge","Balance","Scorpion","Sagittaire","Capricorne","Verseau","Poissons"];
    const s = signes[Math.floor(Math.random() * signes.length)];
    await msg.reply(`🔮 *${{s}} :*\\n\\n${{await getAI(`Horoscope drôle pour ${{s}}`, "Tu inventes des horoscopes dramatiques et absurdes.")}}`);
    logToDashboard("command", "Commande !horoscope exécutée", `${{s}} dans ${{chat.name || msg.from}}`);
    return;
  }}

  if (lower === "!météo" || lower === "!meteo") {{
    await chat.sendStateTyping();
    await msg.reply(`🌦️ *Météo :*\\n\\n${{await getAI("Donne la météo du jour.", "Tu inventes une météo dramatique et philosophique pour étudiants. Court.")}}`);
    logToDashboard("command", "Commande !météo exécutée", `Dans ${{chat.name || msg.from}}`);
    return;
  }}

  if (lower === "!ragequit") {{
    await msg.reply("C\\'est bon j\\'en peux plus... 🚪\\n\\n...\\n\\n(je suis toujours là 😐)");
    logToDashboard("command", "Commande !ragequit exécutée", `Dans ${{chat.name || msg.from}}`);
    return;
  }}

  if (lower.startsWith("!sondage ")) {{
    await chat.sendMessage(`📊 *Sondage :*\\n\\n❓ ${{text.slice(9).trim()}}\\n\\n👍 Pour\\n👎 Contre`);
    logToDashboard("command", "Commande !sondage exécutée", `"${{text.slice(9, 40).trim()}}" dans ${{chat.name || msg.from}}`);
    return;
  }}

  if (lower === "!rappel") {{
    await msg.reply("⚠️ *Rappel des règles :*\\n\\n1. Pas d\\'insultes\\n2. Pas de politique\\n3. Pas de religion\\n\\nMerci 🙏");
    logToDashboard("command", "Commande !rappel exécutée", `Dans ${{chat.name || msg.from}}`);
    return;
  }}

  if (lower === "!regle") {{
    await msg.reply("📋 *Règles du groupe :*\\n\\n🚫 Insultes interdites\\n🚫 Politique interdite\\n🚫 Religion interdite\\n\\nTout manquement = suppression du message ✅");
    logToDashboard("command", "Commande !regle exécutée", `Dans ${{chat.name || msg.from}}`);
    return;
  }}

  if (lower === "!licorne") {{
    await msg.reply("📋 *Commandes disponibles :*\\n\\n{licorne_str}");
    logToDashboard("command", "Commande !licorne exécutée", `Liste des commandes dans ${{chat.name || msg.from}}`);
    return;
  }}

  // ── Commandes custom (générées depuis le dashboard) ───────
{custom_cmds_code}

  // ── Commande IA ───────────────────────────────────────────
  if (lower.startsWith(BOT_PREFIX)) {{
    const question = text.slice(BOT_PREFIX.length).trim();
    if (!question) {{ await msg.reply(`👋 Pose une question après *${{BOT_PREFIX}}*\\nEx : \`${{BOT_PREFIX}} c\\'est quoi l\\'IA ?\``); return; }}
    await chat.sendStateTyping();
    const answer = await askChatGPT(question);
    await msg.reply(`🤖 *Assistant IA*\\n\\n${{answer}}`);
    logToDashboard("command", `Commande ${{BOT_PREFIX}} exécutée`, `"${{question.substring(0, 40)}}" dans ${{chat.name || msg.from}}`);
  }}
}});

client.initialize();
'''
    return {"code": code, "stats": {"commands": len(commands), "auto_replies": len(auto_replies), "banned_words": len(banned_words)}}


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
