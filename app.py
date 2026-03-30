"""
🎬 Promo Video Creator
Full pipeline: Script → AI Voiceover (Inworld TTS) → Animated Slides → Final MP4
"""

import streamlit as st
import requests
import base64
import io
import os
import time
import tempfile
import traceback

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import moviepy.editor as mpy
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="🎬 Promo Video Creator",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap');

*, *::before, *::after { box-sizing: border-box; }
html, body, .stApp { background: #07070f !important; font-family: 'DM Sans', sans-serif; color: #e2e0f0; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2rem 3rem 5rem !important; max-width: 1300px !important; }
h1, h2, h3, h4 { font-family: 'Syne', sans-serif !important; }

.hero {
    background: linear-gradient(135deg, #100020 0%, #080818 45%, #001830 100%);
    border: 1px solid rgba(140,70,220,0.25);
    border-radius: 22px; padding: 2.8rem 3.5rem;
    margin-bottom: 2rem; position: relative; overflow: hidden;
}
.hero::before {
    content:''; position:absolute; top:-80px; right:-80px;
    width:350px; height:350px;
    background: radial-gradient(circle, rgba(140,70,220,0.18) 0%, transparent 65%);
    pointer-events:none;
}
.hero-title {
    font-family:'Syne',sans-serif; font-size:2.8rem; font-weight:800;
    background: linear-gradient(110deg,#fff 0%,#c084fc 45%,#60a5fa 100%);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    margin:0 0 0.5rem;
}
.hero-sub { color:#8a86b0; font-size:1rem; margin:0; font-weight:300; }

.step-bar { display:flex; border-radius:12px; overflow:hidden; border:1px solid rgba(255,255,255,0.05); margin-bottom:2rem; }
.step-item { flex:1; padding:0.85rem 0.4rem; text-align:center; font-size:0.78rem; font-family:'Syne',sans-serif; font-weight:700; letter-spacing:0.05em; text-transform:uppercase; background:#0c0c1c; color:#2e2c50; border-right:1px solid rgba(255,255,255,0.04); }
.step-item:last-child { border-right:none; }
.step-active { background:linear-gradient(135deg,#4c1d95,#1e3a5f) !important; color:#ddd0ff !important; }
.step-done { background:#110d22 !important; color:#6d4fa0 !important; }

.card { background:#0d0d1c; border:1px solid rgba(255,255,255,0.07); border-radius:16px; padding:1.5rem 1.8rem; margin-bottom:1.2rem; }
.card-label { font-family:'Syne',sans-serif; font-size:0.72rem; font-weight:700; letter-spacing:0.12em; text-transform:uppercase; color:#6d28d9; margin-bottom:0.9rem; }

.scene-box { background:linear-gradient(135deg,#0d0d1c,#090918); border:1px solid rgba(109,40,217,0.22); border-radius:13px; padding:1.1rem 1.4rem; margin:0.5rem 0; }
.scene-lbl { font-family:'Syne',sans-serif; font-size:0.65rem; font-weight:800; letter-spacing:0.15em; text-transform:uppercase; color:#5b21b6; margin-bottom:0.3rem; }
.scene-title { font-size:0.95rem; font-weight:500; color:#ccc8e8; margin-bottom:0.25rem; }
.scene-text { font-size:0.84rem; color:#6a6882; line-height:1.5; font-style:italic; }

.warn { background:#160f00; border:1px solid rgba(217,119,6,0.3); border-radius:11px; padding:1rem 1.4rem; color:#fcd34d; font-size:0.88rem; }
.info { background:#050f1e; border-left:4px solid #3b82f6; border-radius:0 11px 11px 0; padding:1rem 1.4rem; color:#93c5fd; font-size:0.9rem; }
.ok   { background:linear-gradient(135deg,#042014,#041828); border:1px solid rgba(34,197,94,0.3); border-radius:11px; padding:1rem 1.4rem; color:#86efac; }

.stTextArea textarea, .stTextInput input {
    background:#090918 !important; border:1px solid rgba(109,40,217,0.28) !important;
    border-radius:10px !important; color:#d4d0f0 !important; font-family:'DM Sans',sans-serif !important;
}
.stSelectbox > div > div { background:#090918 !important; border:1px solid rgba(109,40,217,0.28) !important; color:#d4d0f0 !important; border-radius:10px !important; }
.stSlider [data-baseweb="slider"] div[role="slider"] { background:#6d28d9 !important; }

.stButton > button {
    background:linear-gradient(135deg,#6d28d9,#1d4ed8) !important; color:#fff !important;
    border:none !important; border-radius:11px !important;
    font-family:'Syne',sans-serif !important; font-weight:700 !important;
    font-size:0.92rem !important; padding:0.62rem 1.6rem !important;
    letter-spacing:0.03em !important; transition:all 0.22s !important;
}
.stButton > button:hover { transform:translateY(-2px) !important; box-shadow:0 6px 24px rgba(109,40,217,0.4) !important; }
.stButton > button:disabled { background:#181830 !important; color:#2e2c50 !important; transform:none !important; }

label, .stMarkdown p { color:#9a96b8 !important; }
small { color:#5a5878 !important; }
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
INWORLD_TTS_URL = "https://api.inworld.ai/tts/v1/voice"

VOICES = {
    "Ashley — Friendly Female":      "Ashley",
    "Elizabeth — Professional Female":"Elizabeth",
    "Olivia — Energetic Female":     "Olivia",
    "Sarah — Calm Female":           "Sarah",
    "Julia — Warm Female":           "Julia",
    "Priya — Expressive Female":     "Priya",
    "Wendy — Bright Female":         "Wendy",
    "Timothy — Young Male":          "Timothy",
    "Theodore — Authoritative Male": "Theodore",
    "Craig — Deep Male":             "Craig",
    "Dennis — Confident Male":       "Dennis",
    "Mark — Strong Male":            "Mark",
}

MODELS = {
    "TTS-1.5 Max — Best quality": "inworld-tts-1.5-max",
    "TTS-1.5 Mini — Ultra-fast":  "inworld-tts-1.5-mini",
    "TTS-1 Max — Stable":         "inworld-tts-1-max",
}

DURATIONS = {"30 seconds": 30, "60 seconds": 60, "90 seconds": 90}

INDUSTRIES = {
    "🚀 SaaS / App": {
        "hook": "Your team is wasting hours every week on tasks that should take minutes.",
        "pain": "Disconnected tools. Missed deadlines. No single source of truth.",
        "solution": "Introducing {product} — the all-in-one platform built for modern teams.",
        "features": [
            "Automate repetitive workflows in minutes",
            "Real-time collaboration across your whole team",
            "Powerful analytics to track what matters",
        ],
        "results": "Teams using {product} save an average of 10 hours per week.",
        "cta": "Start free today. No credit card required.",
    },
    "🛍️ E-commerce": {
        "hook": "Shoppers expect fast, personal, effortless experiences.",
        "pain": "Generic recommendations. Slow checkout. High cart abandonment.",
        "solution": "Introducing {product} — where every purchase feels personal.",
        "features": [
            "AI-powered product recommendations",
            "One-click checkout — lightning fast",
            "Exclusive loyalty rewards for every order",
        ],
        "results": "Stores using {product} see up to 35% higher conversion rates.",
        "cta": "Start your free trial. See results in 7 days.",
    },
    "🎓 Education / Course": {
        "hook": "Skills are the new currency. Are you investing in yours?",
        "pain": "Outdated content. No flexibility. Zero real-world application.",
        "solution": "Introducing {product} — expert-led learning built for real results.",
        "features": [
            "Learn at your own pace, from anywhere",
            "Projects reviewed by industry mentors",
            "Certificates recognized by top employers",
        ],
        "results": "Over 500,000 learners have transformed their careers with {product}.",
        "cta": "Join free today. Your future starts now.",
    },
    "🏢 B2B / Enterprise": {
        "hook": "Your competitors are moving faster. Here is why.",
        "pain": "Siloed teams. Slow decisions. Rising costs with shrinking margins.",
        "solution": "Introducing {product} — the platform that gives enterprises an unfair advantage.",
        "features": [
            "Enterprise-grade security and compliance",
            "Integrates with 200+ tools you already use",
            "Dedicated onboarding and 24/7 support",
        ],
        "results": "Enterprise clients report 40% faster decision-making after deploying {product}.",
        "cta": "Book a free strategy session today.",
    },
    "✍️ Custom": {
        "hook": "Your hook — grab attention in the first 3 seconds.",
        "pain": "The problem your audience is struggling with every day.",
        "solution": "Introducing {product} — your solution to that problem.",
        "features": ["Key feature one", "Key feature two", "Key feature three"],
        "results": "The measurable results your customers achieve with {product}.",
        "cta": "Your call-to-action — tell them exactly what to do next.",
    },
}

THEMES = {
    "Dark — Cinematic":  {"bg":"#080810","surface":"#0f0f1e","acc1":"#9333ea","acc2":"#3b82f6","text":"#f0eeff","sub":"#6a6882"},
    "Dark — Neon":       {"bg":"#04040e","surface":"#080818","acc1":"#22d3ee","acc2":"#a855f7","text":"#e0f8ff","sub":"#3a5a6a"},
    "Dark — Crimson":    {"bg":"#0a0506","surface":"#120a0c","acc1":"#e11d48","acc2":"#f97316","text":"#ffeef0","sub":"#7a4050"},
    "Light — Minimal":   {"bg":"#f9f9fd","surface":"#ffffff","acc1":"#6d28d9","acc2":"#2563eb","text":"#1e1b4b","sub":"#6b7280"},
    "Light — Warm":      {"bg":"#fdf9f3","surface":"#ffffff","acc1":"#b45309","acc2":"#dc2626","text":"#1c1208","sub":"#8a7060"},
}

MUSIC = {
    "🎵 Inspired Ambient": "https://cdn.pixabay.com/download/audio/2023/10/09/audio_c8c8a73467.mp3",
    "⚡ Upbeat Corporate":  "https://cdn.pixabay.com/download/audio/2022/10/25/audio_946b8bce4f.mp3",
    "🔇 No music":          None,
}


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def build_scenes(product: str, industry: str, features: list, cta: str, duration: int) -> list:
    tmpl = dict(INDUSTRIES[industry])
    feats = [f for f in features if f.strip()] or tmpl["features"]
    tmpl["features"] = feats + tmpl["features"][len(feats):]
    if cta.strip():
        tmpl["cta"] = cta
    p = product or "This Product"

    def fmt(s): return s.format(product=p)

    if duration == 30:
        return [
            {"id":"hook",  "name":"Hook",          "dur":6,  "script":fmt(tmpl["hook"])},
            {"id":"pain",  "name":"The Problem",   "dur":7,  "script":fmt(tmpl["pain"])},
            {"id":"sol",   "name":"Solution",      "dur":8,  "script":fmt(tmpl["solution"])},
            {"id":"feat1", "name":"Key Feature",   "dur":6,  "script":fmt(tmpl["features"][0])},
            {"id":"cta",   "name":"Call to Action","dur":3,  "script":fmt(tmpl["cta"])},
        ]
    elif duration == 60:
        return [
            {"id":"hook",  "name":"Hook",          "dur":7,  "script":fmt(tmpl["hook"])},
            {"id":"pain",  "name":"The Problem",   "dur":10, "script":fmt(tmpl["pain"])},
            {"id":"sol",   "name":"Solution",      "dur":12, "script":fmt(tmpl["solution"])},
            {"id":"feat1", "name":"Feature 1",     "dur":8,  "script":fmt(tmpl["features"][0])},
            {"id":"feat2", "name":"Feature 2",     "dur":8,  "script":fmt(tmpl["features"][1])},
            {"id":"feat3", "name":"Feature 3",     "dur":8,  "script":fmt(tmpl["features"][2])},
            {"id":"cta",   "name":"Call to Action","dur":7,  "script":fmt(tmpl["cta"])},
        ]
    else:
        return [
            {"id":"hook",    "name":"Hook",          "dur":8,  "script":fmt(tmpl["hook"])},
            {"id":"pain",    "name":"The Problem",   "dur":12, "script":fmt(tmpl["pain"])},
            {"id":"sol",     "name":"Solution",      "dur":14, "script":fmt(tmpl["solution"])},
            {"id":"feat1",   "name":"Feature 1",     "dur":10, "script":fmt(tmpl["features"][0])},
            {"id":"feat2",   "name":"Feature 2",     "dur":10, "script":fmt(tmpl["features"][1])},
            {"id":"feat3",   "name":"Feature 3",     "dur":10, "script":fmt(tmpl["features"][2])},
            {"id":"results", "name":"Results",       "dur":12, "script":fmt(tmpl["results"])},
            {"id":"cta",     "name":"Call to Action","dur":14, "script":fmt(tmpl["cta"])},
        ]


def gen_tts(api_key, text, voice_id, model_id, speed=1.0, temp=0.8):
    r = requests.post(
        INWORLD_TTS_URL,
        headers={"Authorization": f"Basic {api_key}", "Content-Type": "application/json"},
        json={"text": text, "voiceId": voice_id, "modelId": model_id,
              "audioConfig": {"speakingRate": speed, "temperature": temp, "audioEncoding": "MP3"}},
        timeout=30,
    )
    r.raise_for_status()
    return base64.b64decode(r.json()["audioContent"])


def make_slide(scene: dict, theme: dict, product: str, w=1280, h=720):
    bg  = hex_to_rgb(theme["bg"])
    acc = hex_to_rgb(theme["acc1"])
    ac2 = hex_to_rgb(theme["acc2"])
    txt = hex_to_rgb(theme["text"])
    sub = hex_to_rgb(theme["sub"])

    img = Image.new("RGB", (w, h), bg)
    d   = ImageDraw.Draw(img)

    # Gradient background
    for x in range(w):
        t = x / w
        r = int(bg[0] + (acc[0] - bg[0]) * t * 0.12)
        g = int(bg[1] + (acc[1] - bg[1]) * t * 0.06)
        b = int(bg[2] + (ac2[2] - bg[2]) * t * 0.18)
        d.line([(x,0),(x,h)], fill=(max(0,min(255,r)), max(0,min(255,g)), max(0,min(255,b))))

    # Left accent stripe
    d.rectangle([0, 0, 5, h], fill=acc)

    # Top: scene label
    label_txt = scene["name"].upper()
    d.rectangle([50, 36, 50 + len(label_txt)*9 + 24, 62],
                fill=(*acc[:3], 30) if len(acc)==3 else acc)
    d.text((62, 40), label_txt, fill=acc)

    # Top right: product name
    prod_short = (product[:18] + "…") if len(product) > 18 else product
    d.text((w - 200, 40), prod_short, fill=sub)

    # Main script — large, wrapped
    script = scene["script"]
    words  = script.split()
    max_ch = 40 if len(script) < 80 else 50 if len(script) < 140 else 58
    lines, cur = [], ""
    for word in words:
        if len(cur) + len(word) + 1 <= max_ch:
            cur = (cur + " " + word).strip()
        else:
            lines.append(cur); cur = word
    if cur: lines.append(cur)

    line_h   = 72
    total_h  = len(lines) * line_h
    start_y  = (h - total_h) // 2 - 10

    for i, line in enumerate(lines):
        y = start_y + i * line_h
        # Shadow
        d.text((122, y+3), line, fill=(0,0,0))
        # Highlight first line of hook/sol/cta
        color = acc if (i == 0 and scene["id"] in ("hook","sol","cta","results")) else txt
        d.text((120, y), line, fill=color)

    # Bottom: progress bar (accent line)
    prog = {"hook":1,"pain":2,"sol":3,"feat1":4,"feat2":5,"feat3":6,"results":7,"cta":8}
    total = 8
    filled = prog.get(scene["id"], 1)
    bar_w  = w - 120
    seg_w  = bar_w // total
    for i in range(total):
        col = acc if i < filled else sub
        d.rectangle([60 + i*(seg_w+2), h-16, 60 + i*(seg_w+2) + seg_w, h-10], fill=col)

    return img


def render_video(scenes, audio_map, theme, product, music_url, progress_cb=None):
    if not PIL_AVAILABLE or not MOVIEPY_AVAILABLE:
        return None
    tmpdir = tempfile.mkdtemp()
    clips  = []

    for i, scene in enumerate(scenes):
        if progress_cb:
            progress_cb(i, len(scenes)+2, f"Rendering: {scene['name']}")

        audio_bytes = audio_map[scene["id"]]
        ap = os.path.join(tmpdir, f"a{i}.mp3")
        with open(ap, "wb") as f: f.write(audio_bytes)

        ip = os.path.join(tmpdir, f"s{i}.png")
        make_slide(scene, theme, product).save(ip)

        ac  = mpy.AudioFileClip(ap)
        dur = ac.duration + 0.35
        ic  = (mpy.ImageClip(ip).set_duration(dur).set_audio(ac)
               .fadein(0.25).fadeout(0.25))
        clips.append(ic)

    if progress_cb:
        progress_cb(len(scenes), len(scenes)+2, "Compositing…")

    final = mpy.concatenate_videoclips(clips, method="compose")

    if music_url:
        try:
            mr = requests.get(music_url, timeout=20)
            mp = os.path.join(tmpdir, "music.mp3")
            with open(mp, "wb") as f: f.write(mr.content)
            mc = mpy.AudioFileClip(mp).volumex(0.10).audio_fadein(2).audio_fadeout(3)
            if mc.duration < final.duration:
                reps = int(final.duration / mc.duration) + 1
                mc   = mpy.concatenate_audioclips([mc] * reps)
            mc    = mc.set_duration(final.duration)
            mixed = mpy.CompositeAudioClip([final.audio, mc])
            final = final.set_audio(mixed)
        except Exception:
            pass

    if progress_cb:
        progress_cb(len(scenes)+1, len(scenes)+2, "Encoding MP4…")

    out = os.path.join(tmpdir, "final.mp4")
    final.write_videofile(out, fps=24, codec="libx264",
                           audio_codec="aac", logger=None, verbose=False)
    return open(out,"rb").read()


# ── Session state ─────────────────────────────────────────────────────────────
DEFAULTS = {
    "step":1, "api_key":"", "product":"",
    "industry":"🚀 SaaS / App", "tagline":"",
    "features":["","",""], "cta":"", "duration":"60 seconds",
    "voice":"Timothy — Young Male", "model":"TTS-1.5 Max — Best quality",
    "theme":"Dark — Cinematic", "music":"🎵 Inspired Ambient",
    "speed":1.0, "scenes":[], "audios":{}, "video":None,
}
for k,v in DEFAULTS.items():
    if k not in st.session_state: st.session_state[k] = v

STEP_LABELS = ["① Product","② Style","③ Script","④ Voiceover","⑤ Render"]

def render_hero():
    st.markdown("""<div class="hero">
    <p class="hero-title">🎬 Promo Video Creator</p>
    <p class="hero-sub">AI-powered promo videos · Inworld TTS voiceover · Animated slides · Background music · One-click MP4</p>
    </div>""", unsafe_allow_html=True)

def render_steps(cur):
    items=""
    for i,lbl in enumerate(STEP_LABELS,1):
        cls = "step-active" if i==cur else ("step-done" if i<cur else "step-item")
        prefix = "✓ " if i<cur else ("▶ " if i==cur else "")
        items += f'<div class="step-item {cls}">{prefix}{lbl}</div>'
    st.markdown(f'<div class="step-bar">{items}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — PRODUCT
# ══════════════════════════════════════════════════════════════════════════════
def step1():
    st.markdown("### 🏷️ About your product")
    c1, c2 = st.columns(2, gap="large")

    with c1:
        st.markdown('<div class="card"><div class="card-label">Inworld API Key</div>', unsafe_allow_html=True)
        key = st.text_input("key", value=st.session_state.api_key, type="password",
                            placeholder="Paste Base64 credentials from platform.inworld.ai",
                            label_visibility="collapsed")
        st.session_state.api_key = key
        if key:
            st.markdown('<div class="ok">✅ API key saved</div>', unsafe_allow_html=True)
        else:
            st.markdown("""<div class="warn">🔑 Get free key →
            <a href="https://platform.inworld.ai/api-keys" target="_blank" style="color:#fcd34d">platform.inworld.ai</a>
            → Generate new key → copy <b>Basic (Base64)</b></div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="card"><div class="card-label">Product</div>', unsafe_allow_html=True)
        st.session_state.product = st.text_input("name", value=st.session_state.product,
            placeholder="e.g. TaskFlow, ShopEasy, LearnNow…", label_visibility="collapsed")
        st.session_state.industry = st.selectbox("Industry",list(INDUSTRIES.keys()),
            index=list(INDUSTRIES.keys()).index(st.session_state.industry))
        st.session_state.tagline = st.text_input("Tagline (optional)", value=st.session_state.tagline,
            placeholder="e.g. Work smarter, not harder")
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="card"><div class="card-label">Key Features (3 max)</div>', unsafe_allow_html=True)
        defaults_feats = INDUSTRIES[st.session_state.industry]["features"]
        for i in range(3):
            v = st.text_input(f"Feature {i+1}", value=st.session_state.features[i],
                              placeholder=defaults_feats[i], key=f"feat_{i}")
            st.session_state.features[i] = v
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="card"><div class="card-label">Call to Action</div>', unsafe_allow_html=True)
        cta_opts = ["Start free today. No credit card required.",
                    "Book a free demo today.",
                    "Sign up now — limited spots.",
                    "Download free. Results in 7 days.",
                    "Custom…"]
        choice = st.selectbox("CTA", cta_opts, label_visibility="collapsed")
        if choice == "Custom…":
            st.session_state.cta = st.text_input("Your CTA", value=st.session_state.cta, label_visibility="collapsed")
        else:
            st.session_state.cta = choice
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    _, rc = st.columns([3,1])
    with rc:
        if st.button("Next → Style & Voice", use_container_width=True):
            if not st.session_state.api_key:
                st.error("Please enter your Inworld API Key.")
            elif not st.session_state.product.strip():
                st.error("Please enter a product name.")
            else:
                st.session_state.step = 2; st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — STYLE
# ══════════════════════════════════════════════════════════════════════════════
def step2():
    st.markdown("### 🎨 Style, Voice & Music")
    c1, c2 = st.columns(2, gap="large")

    with c1:
        st.markdown('<div class="card"><div class="card-label">Duration</div>', unsafe_allow_html=True)
        st.session_state.duration = st.radio("dur", list(DURATIONS.keys()),
            index=list(DURATIONS.keys()).index(st.session_state.duration),
            horizontal=True, label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="card"><div class="card-label">Visual Theme</div>', unsafe_allow_html=True)
        st.session_state.theme = st.selectbox("theme", list(THEMES.keys()),
            index=list(THEMES.keys()).index(st.session_state.theme),
            label_visibility="collapsed")
        t = THEMES[st.session_state.theme]
        sw = "".join(f'<span style="display:inline-block;width:22px;height:22px;border-radius:50%;background:{c};margin-right:5px"></span>'
                     for c in [t["bg"],t["surface"],t["acc1"],t["acc2"],t["text"]])
        st.markdown(f"<div style='margin-top:0.4rem'>{sw}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="card"><div class="card-label">Background Music</div>', unsafe_allow_html=True)
        st.session_state.music = st.selectbox("music", list(MUSIC.keys()),
            index=list(MUSIC.keys()).index(st.session_state.music), label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="card"><div class="card-label">AI Voice</div>', unsafe_allow_html=True)
        st.session_state.voice = st.selectbox("voice", list(VOICES.keys()),
            index=list(VOICES.keys()).index(st.session_state.voice), label_visibility="collapsed")
        st.session_state.model = st.selectbox("model", list(MODELS.keys()),
            index=list(MODELS.keys()).index(st.session_state.model), label_visibility="collapsed")
        st.session_state.speed = st.slider("Speaking speed", 0.7, 1.4,
            st.session_state.speed, 0.05)
        st.markdown("</div>", unsafe_allow_html=True)

        dur_s = DURATIONS[st.session_state.duration]
        n_scenes = len(build_scenes(st.session_state.product, st.session_state.industry,
                                    st.session_state.features, st.session_state.cta, dur_s))
        st.markdown(f"""<div class="card">
        <div class="card-label">Summary</div>
        <p style='color:#ccc8e8;font-size:0.88rem;line-height:1.9;margin:0'>
        <b>Product:</b> {st.session_state.product}<br>
        <b>Duration:</b> {st.session_state.duration} · {n_scenes} scenes<br>
        <b>Theme:</b> {st.session_state.theme}<br>
        <b>Voice:</b> {st.session_state.voice}<br>
        <b>Music:</b> {st.session_state.music}
        </p></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    lc, rc = st.columns(2)
    with lc:
        if st.button("← Back", use_container_width=True):
            st.session_state.step = 1; st.rerun()
    with rc:
        if st.button("Next → Review Script", use_container_width=True):
            scenes = build_scenes(st.session_state.product, st.session_state.industry,
                                  st.session_state.features, st.session_state.cta,
                                  DURATIONS[st.session_state.duration])
            st.session_state.scenes = scenes
            st.session_state.step = 3; st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — SCRIPT
# ══════════════════════════════════════════════════════════════════════════════
def step3():
    st.markdown("### 📝 Review & edit script")
    st.markdown('<div class="info">💡 Edit each scene below. This exact text will be spoken and shown on screen.</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    scenes = st.session_state.scenes
    updated = []
    words = 0
    for i, sc in enumerate(scenes):
        st.markdown(f"""<div class="scene-box">
        <div class="scene-lbl">Scene {i+1}/{len(scenes)} · {sc['dur']}s</div>
        <div class="scene-title">{sc['name']}</div></div>""", unsafe_allow_html=True)
        nv = st.text_area(f"s{i}", value=sc["script"], height=88,
                          key=f"sc_{i}", label_visibility="collapsed")
        words += len(nv.split())
        updated.append({**sc, "script": nv})
    st.session_state.scenes = updated

    total_dur = sum(s["dur"] for s in scenes)
    st.markdown(f"""<div class="card" style="margin-top:1.2rem">
    <div class="card-label">Script Stats</div>
    <p style='color:#ccc8e8;margin:0'>📊 {words} words · 🎬 {len(scenes)} scenes · ⏱️ ~{total_dur}s total</p>
    </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    lc, rc = st.columns(2)
    with lc:
        if st.button("← Back", use_container_width=True):
            st.session_state.step = 2; st.rerun()
    with rc:
        if st.button("Next → Generate Voiceover", use_container_width=True):
            st.session_state.step = 4; st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — VOICEOVER
# ══════════════════════════════════════════════════════════════════════════════
def step4():
    st.markdown("### 🎙️ Generate AI Voiceover")
    scenes  = st.session_state.scenes
    vid     = VOICES[st.session_state.voice]
    mid     = MODELS[st.session_state.model]
    done    = set(st.session_state.audios.keys())
    all_ok  = all(s["id"] in done for s in scenes)

    st.markdown(f"""<div class="info">
    🎙️ <b>{st.session_state.voice}</b> · 
    ⚡ <b>{st.session_state.model.split('—')[0].strip()}</b> · 
    ✅ <b>{len(done)}/{len(scenes)}</b> scenes ready
    </div>""", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    ga, gb = st.columns([2,1])
    with ga:
        if st.button("⚡ Generate All Voiceovers", use_container_width=True, disabled=all_ok):
            pb  = st.progress(0)
            msg = st.empty()
            for i, sc in enumerate(scenes):
                if sc["id"] in done: continue
                msg.markdown(f'<div class="info">🎙️ Generating: <b>{sc["name"]}</b> ({i+1}/{len(scenes)})…</div>', unsafe_allow_html=True)
                try:
                    a = gen_tts(st.session_state.api_key, sc["script"], vid, mid, st.session_state.speed)
                    st.session_state.audios[sc["id"]] = a
                except requests.HTTPError as e:
                    code = e.response.status_code if e.response else 0
                    st.error(f"HTTP {code}: {'Invalid API Key' if code==401 else e}"); break
                except Exception as e:
                    st.error(str(e)); break
                pb.progress((i+1)/len(scenes))
                time.sleep(0.08)
            pb.empty(); msg.empty(); st.rerun()
    with gb:
        if st.button("🗑️ Reset All", use_container_width=True):
            st.session_state.audios = {}; st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    for sc in scenes:
        sid = sc["id"]
        has = sid in st.session_state.audios
        ca, cb = st.columns([3,2])
        with ca:
            icon = "✅" if has else "⬜"
            st.markdown(f"""<div class="scene-box">
            <div class="scene-lbl">{icon} {sc['name']} · {sc['dur']}s</div>
            <div class="scene-text">"{sc['script']}"</div></div>""", unsafe_allow_html=True)
        with cb:
            if has:
                st.audio(st.session_state.audios[sid], format="audio/mp3")
                st.download_button(f"⬇️ {sc['name']}.mp3", data=st.session_state.audios[sid],
                    file_name=f"vo_{sid}.mp3", mime="audio/mpeg",
                    key=f"dl_{sid}", use_container_width=True)
            else:
                if st.button(f"🎙️ Generate", key=f"g_{sid}", use_container_width=True):
                    with st.spinner(f"Generating {sc['name']}…"):
                        try:
                            a = gen_tts(st.session_state.api_key, sc["script"], vid, mid, st.session_state.speed)
                            st.session_state.audios[sid] = a; st.rerun()
                        except Exception as e:
                            st.error(str(e))

    st.markdown("<br>", unsafe_allow_html=True)
    all_ok2 = all(s["id"] in st.session_state.audios for s in scenes)
    lc, rc  = st.columns(2)
    with lc:
        if st.button("← Back", use_container_width=True):
            st.session_state.step = 3; st.rerun()
    with rc:
        if st.button("Next → Render Video", use_container_width=True, disabled=not all_ok2):
            st.session_state.step = 5; st.rerun()
        if not all_ok2:
            st.markdown("<small>Generate all scenes first</small>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# STEP 5 — RENDER
# ══════════════════════════════════════════════════════════════════════════════
def step5():
    st.markdown("### 🎬 Render Final Video")
    scenes = st.session_state.scenes
    theme  = THEMES[st.session_state.theme]
    m_url  = MUSIC[st.session_state.music]

    st.markdown(f"""<div class="card">
    <div class="card-label">Render Config</div>
    <p style='color:#ccc8e8;font-size:0.88rem;line-height:2;margin:0'>
    🎬 <b>{st.session_state.product}</b> &nbsp;·&nbsp;
    🎨 {st.session_state.theme} &nbsp;·&nbsp;
    🎙️ {st.session_state.voice}<br>
    🎵 {st.session_state.music} &nbsp;·&nbsp;
    📐 1280×720 HD &nbsp;·&nbsp;
    🎞️ 24 fps &nbsp;·&nbsp;
    🎬 {len(scenes)} scenes
    </p></div>""", unsafe_allow_html=True)

    if st.session_state.video:
        st.markdown('<div class="ok">✅ Video rendered — ready to download!</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.video(st.session_state.video)
        fn = f"{st.session_state.product.replace(' ','_')}_promo.mp4"
        st.download_button("⬇️  Download Final MP4", data=st.session_state.video,
            file_name=fn, mime="video/mp4", use_container_width=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Create New Video", use_container_width=True):
            for k,v in DEFAULTS.items(): st.session_state[k] = v
            st.rerun()
        return

    if not PIL_AVAILABLE or not MOVIEPY_AVAILABLE:
        missing = [p for p,av in [("Pillow",PIL_AVAILABLE),("moviepy",MOVIEPY_AVAILABLE)] if not av]
        st.markdown(f"""<div class="warn">
        ⚠️ Missing packages for video rendering: <b>{', '.join(missing)}</b><br><br>
        Add to <b>requirements.txt</b>:
        <pre style="background:#1c1408;padding:0.8rem;border-radius:8px;margin-top:0.5rem;color:#fde68a">Pillow>=10.0.0
moviepy>=1.0.3
requests>=2.31.0</pre>
        Meanwhile, download individual voiceover MP3s from Step 4.
        </div>""", unsafe_allow_html=True)
        lc, _ = st.columns(2)
        with lc:
            if st.button("← Back", use_container_width=True):
                st.session_state.step = 4; st.rerun()
        return

    st.markdown("<br>", unsafe_allow_html=True)
    rc, _ = st.columns([1,1])
    with rc:
        if st.button("🚀 Render Video Now", use_container_width=True):
            pb  = st.progress(0)
            msg = st.empty()

            def pcb(done, total, text):
                pb.progress(min(done/total, 1.0))
                msg.markdown(f'<div class="info">⚙️ {text}</div>', unsafe_allow_html=True)

            try:
                vid = render_video(scenes, st.session_state.audios,
                                   theme, st.session_state.product, m_url, pcb)
                pb.empty(); msg.empty()
                if vid:
                    st.session_state.video = vid; st.rerun()
                else:
                    st.error("Render returned no data.")
            except Exception as e:
                pb.empty(); msg.empty()
                st.error(f"Render error: {e}")
                with st.expander("Details"): st.code(traceback.format_exc())

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("← Back to Voiceover", use_container_width=True):
        st.session_state.step = 4; st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
render_hero()
render_steps(st.session_state.step)

{1: step1, 2: step2, 3: step3, 4: step4, 5: step5}[st.session_state.step]()
