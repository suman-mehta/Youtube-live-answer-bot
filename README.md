# 🤖 LiveGuru - YouTube Live AI Bot

<p align="center">
  <img src="https://img.shields.io/badge/YouTube-AI_Bot-red?style=for-the-badge&logo=youtube">
  <img src="https://img.shields.io/badge/Telegram-Control-blue?style=for-the-badge&logo=telegram">
  <img src="https://img.shields.io/badge/Python-3.9+-yellow?style=for-the-badge&logo=python">
  <img src="https://img.shields.io/badge/Self_Healing-Enabled-green?style=for-the-badge">
  <img src="https://img.shields.io/badge/Speed-Ultra_Fast-orange?style=for-the-badge">
</p>

<p align="center"><b>⚡ Ultra-Fast | 🛡️ Self-Healing | 🧠 AI-Powered | 📱 Telegram Control</b></p>

<p align="center"><i>Automatically detects questions from YouTube Live streams and answers them instantly with AI-powered explanations</i></p>

---

## ✨ Features

### 🎯 Core Capabilities
- **👁️ Visual Question Detection** - OCR से board/screen से questions पढ़ता है
- **🧠 AI-Powered Answers** - Google Gemini से accurate answers + explanations
- **⚡ Ultra-Fast** - < 3 seconds में detect → answer
- **🌍 Multilingual** - Hindi + English दोनों support
- **🤖 Fully Automated** - 24/7 run करता है

### 🛡️ Self-Healing System
- **Connection Issues** → Auto-reconnect
- **API Failures** → Retry logic
- **Memory Leaks** → Auto cleanup
- **Missing Dependencies** → Auto-install
- **Stream Interruptions** → Auto-restart

### 📱 Telegram Commands
| Command | Action |
|---------|--------|
| `/join <url>` | YouTube live stream join करें |
| `/pause` | Answering pause करें |
| `/resume` | Resume करें |
| `/stop` | Bot stop करें |
| `/status` | Health check |
| `/stats` | Performance statistics |
| `/heal` | Healing system status |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Tesseract OCR installed
- Telegram Bot Token ([@BotFather](https://t.me/botfather))
- Google Gemini API Key ([Google AI Studio](https://aistudio.google.com/))

### Installation

```bash
git clone https://github.com/suman-mehta/Youtube-live-answer-bot.git
cd liveguru
pip install -r requirements.txt
```

**Linux/Mac:**
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-eng tesseract-ocr-hin
```

**Windows:** Download from [here](https://github.com/UB-Mannheim/tesseract/wiki)

### First Run

```bash
python liveguru_bot.py
```

Interactive setup मांगेगा:
1. Telegram Bot Token
2. Google Gemini API Key
3. Your Telegram User ID

---

## ⚙️ Configuration

`.env` file:
```env
TELEGRAM_TOKEN=your_token_here
GOOGLE_API_KEY=your_api_key_here
ADMIN_USER_IDS=123456789
```

---

## 📊 Performance

| Metric | Value |
|--------|-------|
| Detection Speed | 1.5-3 seconds |
| OCR Accuracy | 85-95% |
| AI Response | 1-2 seconds |
| Uptime | 99%+ |

---

## ⚠️ Disclaimer

**Educational Purpose Only!** Ensure compliance with YouTube Terms of Service.

**Do not use for:** Cheating, Spamming, Illegal activities

---

## 📜 License

MIT License - See [LICENSE](LICENSE)

---

<p align="center">
  <b>⭐ Star this repo if you find it helpful!</b><br>
  <b>Made with ❤️ by Suman Mehta</b><br>
  <b>🇮🇳 India</b>
</p>
