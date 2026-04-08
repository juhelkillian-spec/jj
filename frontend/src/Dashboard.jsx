import { useState, useEffect, useCallback } from "react";
import axios from "axios";
import {
  Robot, ChatCircleDots, ShieldWarning, Terminal,
  Gear, House, Plus, Trash, PencilSimple, Check,
  X, MagnifyingGlass, ArrowClockwise, FloppyDisk,
  Circle, Lightning, Smiley, GameController, Wrench,
  Eye, EyeSlash, ToggleLeft, ToggleRight, Code, DownloadSimple,
  Copy, Warning, ArrowRight, NumberCircleOne, NumberCircleTwo,
  NumberCircleThree, NumberCircleFour
} from "@phosphor-icons/react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const CATEGORY_COLORS = {
  IA: { bg: "bg-cyan-500/10", text: "text-cyan-400", border: "border-cyan-500/30" },
  Fun: { bg: "bg-emerald-500/10", text: "text-emerald-400", border: "border-emerald-500/30" },
  Jeux: { bg: "bg-violet-500/10", text: "text-violet-400", border: "border-violet-500/30" },
  Utile: { bg: "bg-amber-500/10", text: "text-amber-400", border: "border-amber-500/30" },
};

const CATEGORY_ICONS = {
  IA: <Robot size={12} />, Fun: <Smiley size={12} />,
  Jeux: <GameController size={12} />, Utile: <Wrench size={12} />
};

const TYPE_LABELS = { exact: "Exact", contains: "Contient", regex: "Regex" };

// ── Composants UI ─────────────────────────────────────────────

function Badge({ category }) {
  const c = CATEGORY_COLORS[category] || CATEGORY_COLORS.Fun;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 text-xs font-mono uppercase tracking-wider border rounded-none ${c.bg} ${c.text} ${c.border}`}>
      {CATEGORY_ICONS[category]} {category}
    </span>
  );
}

function StatCard({ icon, label, value, sub, accent = false }) {
  return (
    <div className={`p-5 border transition-all duration-200 hover:-translate-y-0.5 ${accent ? "border-emerald-500/40 bg-emerald-500/5" : "border-white/5 bg-[#0B0B10]"}`}>
      <div className="flex items-center justify-between mb-3">
        <span className="font-mono text-xs uppercase tracking-widest text-zinc-500">{label}</span>
        <span className={accent ? "text-emerald-400" : "text-zinc-500"}>{icon}</span>
      </div>
      <div className={`text-3xl font-black font-mono ${accent ? "text-emerald-400" : "text-white"}`}>{value}</div>
      {sub && <div className="text-xs text-zinc-600 mt-1 font-mono">{sub}</div>}
    </div>
  );
}

function Notification({ msg, type }) {
  if (!msg) return null;
  const colors = type === "success" ? "bg-emerald-500/10 border-emerald-500/40 text-emerald-400" : "bg-red-500/10 border-red-500/40 text-red-400";
  return (
    <div className={`fixed top-4 right-4 z-50 px-4 py-3 border text-sm font-mono flex items-center gap-2 ${colors}`} data-testid="notification">
      {type === "success" ? <Check size={14} /> : <X size={14} />} {msg}
    </div>
  );
}

// ── Section : Vue d'ensemble ──────────────────────────────────

function Overview({ stats, activity }) {
  const LOG_COLORS = {
    delete: "text-red-400", autoreply: "text-emerald-400",
    command: "text-cyan-400", default: "text-zinc-400"
  };
  return (
    <div className="space-y-6">
      <div>
        <p className="font-mono text-xs uppercase tracking-widest text-zinc-500 mb-1">État du système</p>
        <h2 className="text-2xl font-black text-white" style={{ fontFamily: "Unbounded, sans-serif" }}>Vue d'ensemble</h2>
      </div>
      {/* Status bar */}
      <div className="flex items-center gap-3 p-4 border border-white/5 bg-[#0B0B10]">
        <span className="relative flex h-2.5 w-2.5">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
        </span>
        <span className="text-emerald-400 font-mono text-sm font-bold">BOT EN LIGNE</span>
        <span className="ml-auto text-zinc-500 font-mono text-xs">WhatsApp Bot — CROUS</span>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4" data-testid="stats-grid">
        <StatCard icon={<ChatCircleDots size={18} />} label="Auto-réponses" value={stats.auto_replies ?? "—"} sub="actives" accent />
        <StatCard icon={<ShieldWarning size={18} />} label="Mots bannis" value={stats.banned_words ?? "—"} sub={`${stats.banned_insultes ?? 0} insultes • ${stats.banned_religieux ?? 0} religieux`} />
        <StatCard icon={<Terminal size={18} />} label="Commandes" value={stats.commands ?? "—"} sub="disponibles" />
        <StatCard icon={<Trash size={18} />} label="Messages sup." value={stats.messages_deleted ?? "—"} sub="depuis le début" />
      </div>

      {/* Activity log */}
      <div className="border border-emerald-500/20 bg-black">
        <div className="border-b border-emerald-500/20 px-4 py-3 flex items-center gap-2">
          <Terminal size={14} className="text-emerald-400" />
          <span className="font-mono text-xs uppercase tracking-widest text-emerald-400">Journal d'activité</span>
          <span className="ml-auto font-mono text-xs text-zinc-600">{activity.length} entrées</span>
        </div>
        <div className="p-4 space-y-2 max-h-72 overflow-y-auto" style={{ fontFamily: "JetBrains Mono, monospace" }} data-testid="activity-log">
          {activity.length === 0 && (
            <p className="text-zinc-600 text-sm text-center py-4">Aucune activité enregistrée</p>
          )}
          {activity.map((log, i) => (
            <div key={log.id || i} className="flex items-start gap-3 text-sm group">
              <span className="text-zinc-700 shrink-0 text-xs mt-0.5">
                {new Date(log.timestamp).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" })}
              </span>
              <span className={`shrink-0 ${LOG_COLORS[log.type] || LOG_COLORS.default}`}>›</span>
              <span className="text-zinc-300">{log.message}</span>
              {log.detail && <span className="text-zinc-600 text-xs ml-auto">{log.detail}</span>}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Section : Auto-Réponses ───────────────────────────────────

function AutoReplies({ notify }) {
  const [replies, setReplies] = useState([]);
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ trigger: "", response: "", type: "exact", active: true });
  const [editId, setEditId] = useState(null);

  const load = useCallback(async () => {
    const r = await axios.get(`${API}/auto-replies`);
    setReplies(r.data);
  }, []);

  useEffect(() => { load(); }, [load]);

  const filtered = replies.filter(r =>
    r.trigger.toLowerCase().includes(search.toLowerCase()) ||
    r.response.toLowerCase().includes(search.toLowerCase())
  );

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editId) {
        await axios.put(`${API}/auto-replies/${editId}`, form);
        notify("Auto-réponse modifiée !", "success");
      } else {
        await axios.post(`${API}/auto-replies`, form);
        notify("Auto-réponse ajoutée !", "success");
      }
      setForm({ trigger: "", response: "", type: "exact", active: true });
      setShowForm(false);
      setEditId(null);
      load();
    } catch { notify("Erreur lors de l'opération", "error"); }
  };

  const toggleActive = async (r) => {
    await axios.put(`${API}/auto-replies/${r.id}`, { active: !r.active });
    load();
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Supprimer cette auto-réponse ?")) return;
    await axios.delete(`${API}/auto-replies/${id}`);
    notify("Supprimée !", "success");
    load();
  };

  const startEdit = (r) => {
    setForm({ trigger: r.trigger, response: r.response, type: r.type, active: r.active });
    setEditId(r.id);
    setShowForm(true);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <p className="font-mono text-xs uppercase tracking-widest text-zinc-500 mb-1">Automatisation</p>
          <h2 className="text-2xl font-black text-white" style={{ fontFamily: "Unbounded, sans-serif" }}>Auto-Réponses</h2>
        </div>
        <button
          data-testid="add-autoreply-btn"
          onClick={() => { setShowForm(!showForm); setEditId(null); setForm({ trigger: "", response: "", type: "exact", active: true }); }}
          className="flex items-center gap-2 px-4 py-2 bg-emerald-500 text-black font-bold text-sm hover:bg-emerald-400 transition-colors duration-200"
        >
          <Plus size={16} /> Ajouter
        </button>
      </div>

      {/* Form */}
      {showForm && (
        <form onSubmit={handleSubmit} className="p-5 border border-emerald-500/30 bg-[#0B0B10] space-y-4" data-testid="autoreply-form">
          <p className="font-mono text-xs uppercase tracking-widest text-emerald-400">{editId ? "Modifier" : "Nouvelle auto-réponse"}</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block font-mono text-xs text-zinc-500 mb-1 uppercase tracking-widest">Déclencheur</label>
              <input
                data-testid="autoreply-trigger-input"
                value={form.trigger} onChange={e => setForm({ ...form, trigger: e.target.value })}
                placeholder="mot ou phrase"
                required
                className="w-full bg-[#030305] border border-white/10 text-white px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 font-mono"
              />
            </div>
            <div>
              <label className="block font-mono text-xs text-zinc-500 mb-1 uppercase tracking-widest">Type</label>
              <select
                data-testid="autoreply-type-select"
                value={form.type} onChange={e => setForm({ ...form, type: e.target.value })}
                className="w-full bg-[#030305] border border-white/10 text-white px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none font-mono"
              >
                <option value="exact">Exact</option>
                <option value="contains">Contient</option>
                <option value="regex">Regex</option>
              </select>
            </div>
          </div>
          <div>
            <label className="block font-mono text-xs text-zinc-500 mb-1 uppercase tracking-widest">Réponse</label>
            <textarea
              data-testid="autoreply-response-input"
              value={form.response} onChange={e => setForm({ ...form, response: e.target.value })}
              placeholder="Ce que le bot va répondre..."
              required rows={3}
              className="w-full bg-[#030305] border border-white/10 text-white px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 font-mono resize-none"
            />
          </div>
          <div className="flex gap-3">
            <button type="submit" data-testid="autoreply-submit-btn" className="px-4 py-2 bg-emerald-500 text-black font-bold text-sm hover:bg-emerald-400 transition-colors duration-200 flex items-center gap-2">
              <Check size={14} /> {editId ? "Modifier" : "Ajouter"}
            </button>
            <button type="button" onClick={() => { setShowForm(false); setEditId(null); }} className="px-4 py-2 border border-white/10 text-white text-sm hover:border-white/30 transition-colors duration-200">
              Annuler
            </button>
          </div>
        </form>
      )}

      {/* Search */}
      <div className="relative">
        <MagnifyingGlass size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
        <input
          data-testid="autoreply-search"
          value={search} onChange={e => setSearch(e.target.value)}
          placeholder="Rechercher..."
          className="w-full bg-[#030305] border border-white/10 text-white pl-9 pr-3 py-2 text-sm focus:border-emerald-500 focus:outline-none font-mono"
        />
      </div>

      {/* List */}
      <div className="space-y-2" data-testid="autoreply-list">
        {filtered.length === 0 && <p className="text-zinc-600 font-mono text-sm text-center py-8">Aucune auto-réponse trouvée</p>}
        {filtered.map(r => (
          <div key={r.id} className={`flex items-center gap-4 p-4 border transition-all duration-200 ${r.active ? "border-white/5 bg-[#0B0B10]" : "border-white/5 bg-[#030305] opacity-50"}`}>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="font-mono text-sm text-white font-bold">"{r.trigger}"</span>
                <span className="font-mono text-xs px-1.5 py-0.5 border border-white/10 text-zinc-500">{TYPE_LABELS[r.type]}</span>
                {!r.active && <span className="font-mono text-xs text-zinc-600">[inactif]</span>}
              </div>
              <p className="text-zinc-400 text-sm truncate">{r.response}</p>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <button onClick={() => toggleActive(r)} data-testid={`toggle-reply-${r.id}`} className="text-zinc-500 hover:text-emerald-400 transition-colors duration-200">
                {r.active ? <ToggleRight size={20} weight="fill" className="text-emerald-400" /> : <ToggleLeft size={20} />}
              </button>
              <button onClick={() => startEdit(r)} data-testid={`edit-reply-${r.id}`} className="text-zinc-500 hover:text-white transition-colors duration-200 p-1">
                <PencilSimple size={15} />
              </button>
              <button onClick={() => handleDelete(r.id)} data-testid={`delete-reply-${r.id}`} className="text-zinc-500 hover:text-red-400 transition-colors duration-200 p-1">
                <Trash size={15} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Section : Mots Bannis ─────────────────────────────────────

function BannedWords({ notify }) {
  const [words, setWords] = useState([]);
  const [tab, setTab] = useState("insultes");
  const [newWord, setNewWord] = useState("");

  const load = useCallback(async () => {
    const r = await axios.get(`${API}/banned-words`);
    setWords(r.data);
  }, []);

  useEffect(() => { load(); }, [load]);

  const insultes = words.filter(w => w.category === "insultes");
  const religieux = words.filter(w => w.category === "religieux");
  const current = tab === "insultes" ? insultes : religieux;

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!newWord.trim()) return;
    try {
      await axios.post(`${API}/banned-words`, { word: newWord.trim(), category: tab });
      notify(`"${newWord}" ajouté !`, "success");
      setNewWord("");
      load();
    } catch (err) {
      notify(err.response?.data?.detail || "Erreur", "error");
    }
  };

  const handleDelete = async (id, word) => {
    await axios.delete(`${API}/banned-words/${id}`);
    notify(`"${word}" supprimé`, "success");
    load();
  };

  return (
    <div className="space-y-6">
      <div>
        <p className="font-mono text-xs uppercase tracking-widest text-zinc-500 mb-1">Modération</p>
        <h2 className="text-2xl font-black text-white" style={{ fontFamily: "Unbounded, sans-serif" }}>Mots Bannis</h2>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4">
        <div className="p-4 border border-white/5 bg-[#0B0B10]">
          <div className="font-mono text-xs uppercase tracking-widest text-zinc-500 mb-1">Insultes</div>
          <div className="text-2xl font-black text-red-400 font-mono">{insultes.length}</div>
        </div>
        <div className="p-4 border border-white/5 bg-[#0B0B10]">
          <div className="font-mono text-xs uppercase tracking-widest text-zinc-500 mb-1">Religieux</div>
          <div className="text-2xl font-black text-amber-400 font-mono">{religieux.length}</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-white/5">
        {["insultes", "religieux"].map(t => (
          <button
            key={t}
            data-testid={`tab-${t}`}
            onClick={() => setTab(t)}
            className={`px-5 py-2.5 font-mono text-sm uppercase tracking-wider transition-colors duration-200 border-b-2 ${tab === t ? "text-emerald-400 border-emerald-500" : "text-zinc-500 border-transparent hover:text-white"}`}
          >
            {t} <span className="ml-1 text-xs opacity-60">({t === "insultes" ? insultes.length : religieux.length})</span>
          </button>
        ))}
      </div>

      {/* Add form */}
      <form onSubmit={handleAdd} className="flex gap-3" data-testid="banned-word-form">
        <input
          data-testid="banned-word-input"
          value={newWord} onChange={e => setNewWord(e.target.value)}
          placeholder={`Ajouter un mot (${tab})...`}
          className="flex-1 bg-[#030305] border border-white/10 text-white px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none font-mono"
        />
        <button type="submit" data-testid="banned-word-add-btn" className="px-4 py-2 bg-emerald-500 text-black font-bold text-sm hover:bg-emerald-400 transition-colors duration-200 flex items-center gap-2">
          <Plus size={16} /> Ajouter
        </button>
      </form>

      {/* List */}
      <div className="flex flex-wrap gap-2" data-testid="banned-words-list">
        {current.length === 0 && <p className="text-zinc-600 font-mono text-sm py-4">Aucun mot dans cette catégorie</p>}
        {current.map(w => (
          <div key={w.id} className={`group flex items-center gap-2 px-3 py-1.5 border font-mono text-sm ${tab === "insultes" ? "border-red-500/20 bg-red-500/5 text-red-300" : "border-amber-500/20 bg-amber-500/5 text-amber-300"}`}>
            {w.word}
            <button onClick={() => handleDelete(w.id, w.word)} data-testid={`delete-word-${w.id}`} className="opacity-0 group-hover:opacity-100 transition-opacity duration-200 hover:text-white ml-1">
              <X size={12} />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Section : Commandes ───────────────────────────────────────

function Commands({ notify }) {
  const [commands, setCommands] = useState([]);
  const [filter, setFilter] = useState("Tous");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ command: "", description: "", category: "Fun", emoji: "🤖", active: true });
  const [editId, setEditId] = useState(null);

  const load = useCallback(async () => {
    const r = await axios.get(`${API}/commands`);
    setCommands(r.data);
  }, []);

  useEffect(() => { load(); }, [load]);

  const categories = ["Tous", "IA", "Fun", "Jeux", "Utile"];
  const filtered = filter === "Tous" ? commands : commands.filter(c => c.category === filter);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editId) {
        await axios.put(`${API}/commands/${editId}`, form);
        notify("Commande modifiée !", "success");
      } else {
        await axios.post(`${API}/commands`, form);
        notify("Commande ajoutée !", "success");
      }
      setForm({ command: "", description: "", category: "Fun", emoji: "🤖", active: true });
      setShowForm(false);
      setEditId(null);
      load();
    } catch { notify("Erreur lors de l'opération", "error"); }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Supprimer cette commande ?")) return;
    await axios.delete(`${API}/commands/${id}`);
    notify("Supprimée !", "success");
    load();
  };

  const toggleActive = async (c) => {
    await axios.put(`${API}/commands/${c.id}`, { active: !c.active });
    load();
  };

  const startEdit = (c) => {
    setForm({ command: c.command, description: c.description, category: c.category, emoji: c.emoji, active: c.active });
    setEditId(c.id);
    setShowForm(true);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <p className="font-mono text-xs uppercase tracking-widest text-zinc-500 mb-1">Commandes Bot</p>
          <h2 className="text-2xl font-black text-white" style={{ fontFamily: "Unbounded, sans-serif" }}>Commandes</h2>
        </div>
        <button
          data-testid="add-command-btn"
          onClick={() => { setShowForm(!showForm); setEditId(null); setForm({ command: "", description: "", category: "Fun", emoji: "🤖", active: true }); }}
          className="flex items-center gap-2 px-4 py-2 bg-emerald-500 text-black font-bold text-sm hover:bg-emerald-400 transition-colors duration-200"
        >
          <Plus size={16} /> Nouvelle commande
        </button>
      </div>

      {/* Form */}
      {showForm && (
        <form onSubmit={handleSubmit} className="p-5 border border-emerald-500/30 bg-[#0B0B10] space-y-4" data-testid="command-form">
          <p className="font-mono text-xs uppercase tracking-widest text-emerald-400">{editId ? "Modifier la commande" : "Nouvelle commande"}</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block font-mono text-xs text-zinc-500 mb-1 uppercase tracking-widest">Emoji</label>
              <input
                data-testid="command-emoji-input"
                value={form.emoji} onChange={e => setForm({ ...form, emoji: e.target.value })}
                placeholder="🤖" maxLength={4}
                className="w-full bg-[#030305] border border-white/10 text-white px-3 py-2 text-lg focus:border-emerald-500 focus:outline-none"
              />
            </div>
            <div className="md:col-span-2">
              <label className="block font-mono text-xs text-zinc-500 mb-1 uppercase tracking-widest">Commande</label>
              <input
                data-testid="command-name-input"
                value={form.command} onChange={e => setForm({ ...form, command: e.target.value })}
                placeholder="!macommande [param]" required
                className="w-full bg-[#030305] border border-white/10 text-white px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none font-mono"
              />
            </div>
          </div>
          <div>
            <label className="block font-mono text-xs text-zinc-500 mb-1 uppercase tracking-widest">Description</label>
            <input
              data-testid="command-desc-input"
              value={form.description} onChange={e => setForm({ ...form, description: e.target.value })}
              placeholder="Ce que fait cette commande..." required
              className="w-full bg-[#030305] border border-white/10 text-white px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none font-mono"
            />
          </div>
          <div>
            <label className="block font-mono text-xs text-zinc-500 mb-1 uppercase tracking-widest">Catégorie</label>
            <select
              data-testid="command-category-select"
              value={form.category} onChange={e => setForm({ ...form, category: e.target.value })}
              className="w-full bg-[#030305] border border-white/10 text-white px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none font-mono"
            >
              {["IA", "Fun", "Jeux", "Utile"].map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div className="flex gap-3">
            <button type="submit" data-testid="command-submit-btn" className="px-4 py-2 bg-emerald-500 text-black font-bold text-sm hover:bg-emerald-400 transition-colors duration-200 flex items-center gap-2">
              <Check size={14} /> {editId ? "Modifier" : "Ajouter"}
            </button>
            <button type="button" onClick={() => { setShowForm(false); setEditId(null); }} className="px-4 py-2 border border-white/10 text-white text-sm hover:border-white/30 transition-colors duration-200">
              Annuler
            </button>
          </div>
        </form>
      )}

      {/* Category filters */}
      <div className="flex flex-wrap gap-2" data-testid="category-filters">
        {categories.map(cat => (
          <button
            key={cat}
            data-testid={`filter-${cat}`}
            onClick={() => setFilter(cat)}
            className={`px-3 py-1.5 text-xs font-mono uppercase tracking-wider border transition-colors duration-200 ${filter === cat ? "bg-emerald-500/10 border-emerald-500/40 text-emerald-400" : "border-white/10 text-zinc-500 hover:border-white/20 hover:text-zinc-300"}`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Commands list */}
      <div className="space-y-2" data-testid="commands-list">
        {filtered.length === 0 && <p className="text-zinc-600 font-mono text-sm text-center py-8">Aucune commande dans cette catégorie</p>}
        {filtered.map(c => (
          <div key={c.id} className={`flex items-center gap-4 p-4 border transition-all duration-200 ${c.active ? "border-white/5 bg-[#0B0B10] hover:border-white/10" : "border-white/5 bg-[#030305] opacity-40"}`}>
            <span className="text-2xl">{c.emoji}</span>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="font-mono text-sm text-white">{c.command}</span>
                <Badge category={c.category} />
              </div>
              <p className="text-zinc-400 text-sm">{c.description}</p>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <button onClick={() => toggleActive(c)} data-testid={`toggle-cmd-${c.id}`} className="text-zinc-500 hover:text-emerald-400 transition-colors duration-200">
                {c.active ? <ToggleRight size={20} weight="fill" className="text-emerald-400" /> : <ToggleLeft size={20} />}
              </button>
              <button onClick={() => startEdit(c)} data-testid={`edit-cmd-${c.id}`} className="text-zinc-500 hover:text-white transition-colors duration-200 p-1">
                <PencilSimple size={15} />
              </button>
              <button onClick={() => handleDelete(c.id)} data-testid={`delete-cmd-${c.id}`} className="text-zinc-500 hover:text-red-400 transition-colors duration-200 p-1">
                <Trash size={15} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Section : Paramètres ──────────────────────────────────────

function Settings({ notify }) {
  const [settings, setSettings] = useState(null);
  const [showKey, setShowKey] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    axios.get(`${API}/settings`).then(r => setSettings(r.data));
  }, []);

  const handleSave = async () => {
    try {
      await axios.put(`${API}/settings`, settings);
      setSaved(true);
      notify("Paramètres sauvegardés !", "success");
      setTimeout(() => setSaved(false), 2000);
    } catch { notify("Erreur lors de la sauvegarde", "error"); }
  };

  const handleReset = () => {
    if (!window.confirm("Réinitialiser les paramètres ?")) return;
    setSettings({ bot_prefix: "!ai", language: "fr", gpt_model: "gpt-4o-mini", max_tokens: 1024, openai_api_key: "", auto_delete: true, notify_group: true, log_deletions: true, moderate_dm: false });
  };

  if (!settings) return <div className="text-zinc-500 font-mono text-sm text-center py-16">Chargement...</div>;

  const Toggle = ({ label, sub, value, field }) => (
    <div className="flex items-center justify-between p-4 border border-white/5">
      <div>
        <div className="text-white text-sm font-medium">{label}</div>
        {sub && <div className="text-zinc-500 text-xs font-mono mt-0.5">{sub}</div>}
      </div>
      <button
        data-testid={`toggle-setting-${field}`}
        onClick={() => setSettings({ ...settings, [field]: !value })}
        className="transition-colors duration-200"
      >
        {value ? <ToggleRight size={28} weight="fill" className="text-emerald-400" /> : <ToggleLeft size={28} className="text-zinc-600" />}
      </button>
    </div>
  );

  return (
    <div className="space-y-6">
      <div>
        <p className="font-mono text-xs uppercase tracking-widest text-zinc-500 mb-1">Configuration</p>
        <h2 className="text-2xl font-black text-white" style={{ fontFamily: "Unbounded, sans-serif" }}>Paramètres</h2>
      </div>

      {/* Bot config */}
      <div className="border border-white/5 bg-[#0B0B10]">
        <div className="border-b border-white/5 px-5 py-3">
          <span className="font-mono text-xs uppercase tracking-widest text-zinc-400 flex items-center gap-2"><Robot size={12} /> Configuration Bot</span>
        </div>
        <div className="p-5 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block font-mono text-xs text-zinc-500 mb-1 uppercase tracking-widest">Préfixe IA</label>
            <input data-testid="setting-prefix" value={settings.bot_prefix} onChange={e => setSettings({ ...settings, bot_prefix: e.target.value })}
              className="w-full bg-[#030305] border border-white/10 text-white px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none font-mono" />
          </div>
          <div>
            <label className="block font-mono text-xs text-zinc-500 mb-1 uppercase tracking-widest">Langue</label>
            <select data-testid="setting-language" value={settings.language} onChange={e => setSettings({ ...settings, language: e.target.value })}
              className="w-full bg-[#030305] border border-white/10 text-white px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none font-mono">
              <option value="fr">Français</option>
              <option value="en">English</option>
              <option value="ar">العربية</option>
            </select>
          </div>
        </div>
      </div>

      {/* OpenAI config */}
      <div className="border border-white/5 bg-[#0B0B10]">
        <div className="border-b border-white/5 px-5 py-3">
          <span className="font-mono text-xs uppercase tracking-widest text-zinc-400 flex items-center gap-2"><Lightning size={12} /> OpenAI / ChatGPT</span>
        </div>
        <div className="p-5 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block font-mono text-xs text-zinc-500 mb-1 uppercase tracking-widest">Modèle GPT</label>
              <select data-testid="setting-gpt-model" value={settings.gpt_model} onChange={e => setSettings({ ...settings, gpt_model: e.target.value })}
                className="w-full bg-[#030305] border border-white/10 text-white px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none font-mono">
                <option value="gpt-4o-mini">gpt-4o-mini (Recommandé)</option>
                <option value="gpt-4o">gpt-4o (Plus puissant)</option>
                <option value="gpt-3.5-turbo">gpt-3.5-turbo (Économique)</option>
              </select>
            </div>
            <div>
              <label className="block font-mono text-xs text-zinc-500 mb-1 uppercase tracking-widest">Max tokens</label>
              <input data-testid="setting-max-tokens" type="number" value={settings.max_tokens} onChange={e => setSettings({ ...settings, max_tokens: parseInt(e.target.value) })}
                min={100} max={4096}
                className="w-full bg-[#030305] border border-white/10 text-white px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none font-mono" />
            </div>
          </div>
          <div>
            <label className="block font-mono text-xs text-zinc-500 mb-1 uppercase tracking-widest">Clé API OpenAI</label>
            <div className="relative">
              <input
                data-testid="setting-api-key"
                type={showKey ? "text" : "password"}
                value={settings.openai_api_key}
                onChange={e => setSettings({ ...settings, openai_api_key: e.target.value })}
                placeholder="sk-proj-..."
                className="w-full bg-[#030305] border border-white/10 text-white px-3 py-2 pr-10 text-sm focus:border-emerald-500 focus:outline-none font-mono"
              />
              <button type="button" onClick={() => setShowKey(!showKey)} className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-white transition-colors duration-200">
                {showKey ? <EyeSlash size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Moderation */}
      <div className="border border-white/5 bg-[#0B0B10]">
        <div className="border-b border-white/5 px-5 py-3">
          <span className="font-mono text-xs uppercase tracking-widest text-zinc-400 flex items-center gap-2"><ShieldWarning size={12} /> Modération</span>
        </div>
        <div className="divide-y divide-white/5">
          <Toggle label="Suppression automatique" sub="Supprime les messages interdits" value={settings.auto_delete} field="auto_delete" />
          <Toggle label="Notification de groupe" sub="Avertit le groupe après suppression" value={settings.notify_group} field="notify_group" />
          <Toggle label="Logs en console" sub="Journalise les suppressions" value={settings.log_deletions} field="log_deletions" />
          <Toggle label="Modération en DM" sub="Modère aussi les messages privés" value={settings.moderate_dm} field="moderate_dm" />
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <button data-testid="save-settings-btn" onClick={handleSave} className="flex items-center gap-2 px-5 py-2.5 bg-emerald-500 text-black font-bold text-sm hover:bg-emerald-400 transition-colors duration-200">
          {saved ? <Check size={16} /> : <FloppyDisk size={16} />} {saved ? "Sauvegardé !" : "Sauvegarder"}
        </button>
        <button data-testid="reset-settings-btn" onClick={handleReset} className="flex items-center gap-2 px-5 py-2.5 border border-white/10 text-white text-sm hover:border-white/30 transition-colors duration-200">
          <ArrowClockwise size={16} /> Réinitialiser
        </button>
      </div>
    </div>
  );
}

// ── Section : Générateur index.js ────────────────────────────

function Generator() {
  const [code, setCode] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const generate = async () => {
    setLoading(true);
    try {
      const r = await axios.get(`${API}/generate-bot`);
      setCode(r.data.code);
      setStats(r.data.stats);
    } catch { setCode("// Erreur lors de la génération"); }
    setLoading(false);
  };

  const download = () => {
    const blob = new Blob([code], { type: "text/javascript" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "index.js"; a.click();
    URL.revokeObjectURL(url);
  };

  const copyCode = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      <div>
        <p className="font-mono text-xs uppercase tracking-widest text-zinc-500 mb-1">Exportation</p>
        <h2 className="text-2xl font-black text-white" style={{ fontFamily: "Unbounded, sans-serif" }}>Générateur de Bot</h2>
        <p className="text-zinc-500 text-sm mt-1">Génère automatiquement votre fichier <span className="font-mono text-emerald-400">index.js</span> depuis vos données du dashboard.</p>
      </div>

      {/* Info box */}
      <div className="p-4 border border-amber-500/20 bg-amber-500/5 flex gap-3">
        <Warning size={18} className="text-amber-400 shrink-0 mt-0.5" />
        <p className="text-amber-200/80 text-sm">
          Assurez-vous d'avoir renseigné votre <strong>Clé API OpenAI</strong> dans les Paramètres avant de générer. Elle sera incluse dans le fichier.
        </p>
      </div>

      {/* Generate button */}
      <button
        data-testid="generate-btn"
        onClick={generate}
        disabled={loading}
        className="flex items-center gap-2 px-6 py-3 bg-emerald-500 text-black font-bold hover:bg-emerald-400 transition-colors duration-200 disabled:opacity-50"
      >
        <Code size={18} /> {loading ? "Génération..." : "Générer index.js"}
      </button>

      {/* Stats summary */}
      {stats && (
        <div className="flex flex-wrap gap-3" data-testid="gen-stats">
          {[
            { label: "commandes", val: stats.commands },
            { label: "auto-réponses", val: stats.auto_replies },
            { label: "mots bannis", val: stats.banned_words },
          ].map(s => (
            <div key={s.label} className="flex items-center gap-2 px-3 py-1.5 border border-emerald-500/30 bg-emerald-500/5">
              <Check size={12} className="text-emerald-400" />
              <span className="font-mono text-xs text-emerald-300">{s.val} {s.label}</span>
            </div>
          ))}
        </div>
      )}

      {/* Code preview */}
      {code && (
        <div className="border border-emerald-500/20 bg-black">
          <div className="border-b border-emerald-500/20 px-4 py-3 flex items-center gap-2">
            <Code size={14} className="text-emerald-400" />
            <span className="font-mono text-xs text-emerald-400 uppercase tracking-widest">index.js — Aperçu</span>
            <div className="ml-auto flex gap-2">
              <button onClick={copyCode} data-testid="copy-code-btn" className="flex items-center gap-1.5 px-3 py-1 border border-white/10 text-zinc-400 hover:text-white text-xs font-mono transition-colors duration-200">
                {copied ? <><Check size={12} /> Copié !</> : <><Copy size={12} /> Copier</>}
              </button>
              <button onClick={download} data-testid="download-btn" className="flex items-center gap-1.5 px-3 py-1 bg-emerald-500 text-black font-bold text-xs font-mono hover:bg-emerald-400 transition-colors duration-200">
                <DownloadSimple size={12} /> Télécharger
              </button>
            </div>
          </div>
          <pre className="p-4 text-xs font-mono text-zinc-300 overflow-x-auto max-h-96 leading-relaxed" style={{ fontFamily: "JetBrains Mono, monospace" }}>
            {code}
          </pre>
        </div>
      )}

      {/* Instructions d'utilisation */}
      <div className="border border-white/5 bg-[#0B0B10]">
        <div className="border-b border-white/5 px-5 py-3">
          <span className="font-mono text-xs uppercase tracking-widest text-zinc-400">Comment utiliser votre bot</span>
        </div>
        <div className="p-5 space-y-5">

          {/* Étape 1 */}
          <div className="flex gap-4">
            <div className="shrink-0 w-7 h-7 bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center">
              <span className="text-emerald-400 font-mono text-xs font-bold">1</span>
            </div>
            <div>
              <p className="text-white text-sm font-semibold mb-1">Installer Node.js et les dépendances</p>
              <p className="text-zinc-500 text-xs mb-2">Sur votre PC/serveur, ouvrez un terminal et exécutez :</p>
              <div className="bg-black border border-white/5 px-3 py-2 font-mono text-xs text-emerald-300">
                npm install whatsapp-web.js qrcode-terminal openai
              </div>
            </div>
          </div>

          {/* Étape 2 */}
          <div className="flex gap-4">
            <div className="shrink-0 w-7 h-7 bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center">
              <span className="text-emerald-400 font-mono text-xs font-bold">2</span>
            </div>
            <div>
              <p className="text-white text-sm font-semibold mb-1">Mettre votre clé OpenAI dans les Paramètres</p>
              <p className="text-zinc-500 text-xs">Allez dans <span className="text-white">Paramètres → Clé API OpenAI</span> et entrez votre clé <span className="font-mono text-emerald-400">sk-proj-...</span> puis sauvegardez.</p>
            </div>
          </div>

          {/* Étape 3 */}
          <div className="flex gap-4">
            <div className="shrink-0 w-7 h-7 bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center">
              <span className="text-emerald-400 font-mono text-xs font-bold">3</span>
            </div>
            <div>
              <p className="text-white text-sm font-semibold mb-1">Générer et télécharger index.js</p>
              <p className="text-zinc-500 text-xs">Cliquez sur <span className="text-white font-semibold">Générer index.js</span> ci-dessus, puis <span className="text-white font-semibold">Télécharger</span>. Placez le fichier dans un dossier sur votre PC.</p>
            </div>
          </div>

          {/* Étape 4 */}
          <div className="flex gap-4">
            <div className="shrink-0 w-7 h-7 bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center">
              <span className="text-emerald-400 font-mono text-xs font-bold">4</span>
            </div>
            <div>
              <p className="text-white text-sm font-semibold mb-1">Lancer le bot</p>
              <p className="text-zinc-500 text-xs mb-2">Dans le terminal, dans le dossier où se trouve le fichier :</p>
              <div className="bg-black border border-white/5 px-3 py-2 font-mono text-xs text-emerald-300">
                node index.js
              </div>
              <p className="text-zinc-500 text-xs mt-2">Un QR code s'affiche dans le terminal. Scannez-le avec WhatsApp (<span className="text-white">Appareils liés → Lier un appareil</span>).</p>
            </div>
          </div>

          {/* Étape 5 */}
          <div className="flex gap-4">
            <div className="shrink-0 w-7 h-7 bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center">
              <span className="text-cyan-400 font-mono text-xs font-bold">+</span>
            </div>
            <div>
              <p className="text-white text-sm font-semibold mb-1">Mise à jour des commandes</p>
              <p className="text-zinc-500 text-xs">À chaque fois que vous ajoutez une commande ou auto-réponse depuis le dashboard, <span className="text-white">régénérez et re-téléchargez</span> le fichier, puis relancez le bot.</p>
            </div>
          </div>

          {/* Accès dashboard */}
          <div className="mt-4 p-4 border border-cyan-500/20 bg-cyan-500/5">
            <p className="font-mono text-xs text-cyan-400 uppercase tracking-widest mb-2">Accès au Dashboard</p>
            <p className="text-zinc-300 text-sm mb-2">Ce dashboard est accessible depuis n'importe quel navigateur à l'adresse :</p>
            <div className="bg-black border border-white/5 px-3 py-2 font-mono text-xs text-cyan-300 break-all select-all" data-testid="dashboard-url">
              {window.location.origin}
            </div>
            <p className="text-zinc-500 text-xs mt-2">Bookmarkez cette URL pour y accéder rapidement depuis votre téléphone ou PC.</p>
          </div>

        </div>
      </div>
    </div>
  );
}

// ── Navigation ────────────────────────────────────────────────

const NAV = [
  { id: "overview", icon: <House size={18} />, label: "Vue d'ensemble" },
  { id: "autoreplies", icon: <ChatCircleDots size={18} />, label: "Auto-Réponses" },
  { id: "banned", icon: <ShieldWarning size={18} />, label: "Mots Bannis" },
  { id: "commands", icon: <Terminal size={18} />, label: "Commandes" },
  { id: "settings", icon: <Gear size={18} />, label: "Paramètres" },
  { id: "generator", icon: <Code size={18} />, label: "Générateur" },
];

// ── Dashboard principal ───────────────────────────────────────

export default function Dashboard() {
  const [active, setActive] = useState("overview");
  const [stats, setStats] = useState({});
  const [activity, setActivity] = useState([]);
  const [notification, setNotification] = useState({ msg: null, type: "success" });
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const notify = (msg, type = "success") => {
    setNotification({ msg, type });
    setTimeout(() => setNotification({ msg: null, type: "success" }), 3000);
  };

  const loadOverview = useCallback(async () => {
    const [s, a] = await Promise.all([
      axios.get(`${API}/stats`),
      axios.get(`${API}/activity`)
    ]);
    setStats(s.data);
    setActivity(a.data);
  }, []);

  useEffect(() => { loadOverview(); }, [loadOverview]);

  const renderSection = () => {
    switch (active) {
      case "overview": return <Overview stats={stats} activity={activity} />;
      case "autoreplies": return <AutoReplies notify={notify} />;
      case "banned": return <BannedWords notify={notify} />;
      case "commands": return <Commands notify={notify} />;
      case "settings": return <Settings notify={notify} />;
      case "generator": return <Generator />;
      default: return null;
    }
  };

  return (
    <div className="min-h-screen bg-[#030305] flex" style={{ fontFamily: "Manrope, sans-serif" }}>
      <Notification msg={notification.msg} type={notification.type} />

      {/* Sidebar overlay for mobile */}
      {sidebarOpen && (
        <div className="fixed inset-0 bg-black/60 z-20 md:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      {/* Sidebar */}
      <aside className={`fixed md:static top-0 left-0 h-full z-30 w-64 bg-[#0B0B10]/70 backdrop-blur-xl border-r border-white/5 flex flex-col transition-transform duration-300 ${sidebarOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"}`} data-testid="sidebar">
        {/* Logo */}
        <div className="p-6 border-b border-white/5">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-emerald-500 flex items-center justify-center">
              <Robot size={18} weight="fill" className="text-black" />
            </div>
            <div>
              <div className="text-white font-black text-sm" style={{ fontFamily: "Unbounded, sans-serif" }}>CROUS BOT</div>
              <div className="text-zinc-500 text-xs font-mono">Dashboard v1.0</div>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-4 space-y-1">
          {NAV.map(item => (
            <button
              key={item.id}
              data-testid={`nav-${item.id}`}
              onClick={() => { setActive(item.id); setSidebarOpen(false); if (item.id === "overview") loadOverview(); }}
              className={`w-full flex items-center gap-3 px-3 py-2.5 text-sm transition-all duration-200 rounded-none ${active === item.id
                ? "bg-emerald-500/10 border border-emerald-500/40 text-emerald-400"
                : "text-zinc-500 hover:text-white hover:bg-white/5 border border-transparent"
                }`}
            >
              <span className={active === item.id ? "text-emerald-400" : "text-zinc-600"}>{item.icon}</span>
              <span className="font-mono text-xs uppercase tracking-wider">{item.label}</span>
              {active === item.id && <span className="ml-auto w-1 h-1 rounded-full bg-emerald-400"></span>}
            </button>
          ))}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-white/5">
          <div className="flex items-center gap-2">
            <Circle size={8} weight="fill" className="text-emerald-400" />
            <span className="font-mono text-xs text-zinc-500">whatsapp-web.js</span>
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <header className="border-b border-white/5 px-6 py-4 flex items-center gap-4" data-testid="header">
          <button className="md:hidden text-zinc-500 hover:text-white" onClick={() => setSidebarOpen(true)}>
            <div className="space-y-1"><div className="w-5 h-0.5 bg-current"></div><div className="w-5 h-0.5 bg-current"></div><div className="w-5 h-0.5 bg-current"></div></div>
          </button>
          <span className="font-mono text-xs text-zinc-600 uppercase tracking-widest">
            {NAV.find(n => n.id === active)?.label}
          </span>
          <div className="ml-auto flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span className="font-mono text-xs text-emerald-400">En ligne</span>
          </div>
        </header>

        {/* Content */}
        <div className="flex-1 p-6 md:p-8 overflow-auto">
          {renderSection()}
        </div>
      </main>
    </div>
  );
}
