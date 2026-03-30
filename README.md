# 🎬 Promo Video Creator — Streamlit App

AI-powered promo video creator using **Inworld TTS** voiceover + animated slides + background music → final MP4.

---

## 🚀 Quick Deploy to Streamlit Cloud (Free)

1. **Create a GitHub repo** → upload `app.py` + `requirements.txt`
2. Go to **[share.streamlit.io](https://share.streamlit.io)** → New app → pick your repo
3. Click **Deploy** — done!

---

## 💻 Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## 🔑 Get Inworld API Key (Free)

1. Sign up at **[platform.inworld.ai](https://platform.inworld.ai/signup)**
2. Go to **API Keys** → **Generate new key**
3. Copy the **Basic (Base64)** value
4. Paste it in the app on Step 1

---

## 📋 5-Step Wizard

| Step | What happens |
|------|-------------|
| **① Product** | Enter product name, industry, features, CTA + API key |
| **② Style** | Choose duration (30/60/90s), theme, voice, music |
| **③ Script** | Auto-generated script per scene — edit freely |
| **④ Voiceover** | Generate AI audio for each scene via Inworld TTS |
| **⑤ Render** | Combine slides + audio + music → download MP4 |

---

## 🎤 Available Voices (Inworld TTS)

| Voice | Style |
|-------|-------|
| Ashley | Friendly Female |
| Elizabeth | Professional Female |
| Olivia | Energetic Female |
| Timothy | Young Male |
| Theodore | Authoritative Male |
| Craig | Deep Male |

---

## 🎨 Themes

- Dark — Cinematic (purple/blue)
- Dark — Neon (cyan/purple)
- Dark — Crimson (red/orange)
- Light — Minimal (clean white)
- Light — Warm (amber/red)

---

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| `streamlit` | Web UI |
| `requests` | Inworld API calls |
| `Pillow` | Slide image rendering |
| `moviepy` | Video assembly & encoding |
| `numpy` | Array processing |

---

## ⚠️ Notes

- Video rendering requires `Pillow` + `moviepy` (included in requirements.txt)
- On Streamlit Cloud, rendering may take 1–3 minutes depending on video length
- All voiceover MP3s can be downloaded individually (Step 4) even without video rendering
- Music is fetched from Pixabay (royalty-free)
