#!/usr/bin/env python3
"""
🤖 LiveGuru - YouTube Live AI Assistant
Author: Suman Mehta
GitHub: https://github.com/sumanmehta/liveguru

Ultra-fast, Self-Healing, AI-Powered YouTube Live Stream Bot
"""

import os, sys, json, time, asyncio, logging, traceback, subprocess, threading, queue
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Optional, Dict, List, Any

REQUIRED_PACKAGES = {
    'telegram': 'python-telegram-bot>=20.0',
    'cv2': 'opencv-python>=4.8.0',
    'pytesseract': 'pytesseract>=0.3.10',
    'PIL': 'Pillow>=10.0.0',
    'numpy': 'numpy>=1.24.0',
    'requests': 'requests>=2.31.0',
    'google.generativeai': 'google-generativeai>=0.3.0',
    'yt_dlp': 'yt-dlp>=2023.10.0',
    'dotenv': 'python-dotenv>=1.0.0',
}

def install_missing():
    missing = []
    for module, package in REQUIRED_PACKAGES.items():
        try:
            __import__(module.replace('google.generativeai', 'google.generativeai'))
        except ImportError:
            missing.append(package)

    if missing:
        print(f"📦 Installing: {', '.join(missing)}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
        print("✅ Installed! Restarting...")
        os.execv(sys.executable, [sys.executable] + sys.argv)

install_missing()

import cv2, pytesseract, numpy as np
from PIL import Image
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, filters
import google.generativeai as genai
from yt_dlp import YoutubeDL
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('liveguru.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
load_dotenv()

@dataclass
class Config:
    TELEGRAM_TOKEN: str = ""
    GOOGLE_API_KEY: str = ""
    ADMIN_USER_IDS: List[int] = None
    OCR_LANGUAGE: str = "eng+hin"
    FRAME_SKIP: int = 3
    ANSWER_COOLDOWN: int = 15
    MAX_RETRIES: int = 3
    CONFIDENCE_THRESHOLD: float = 0.6
    STREAM_QUALITY: str = "480p"
    HEALING_ENABLED: bool = True
    AUTO_RESTART: bool = True

    def __post_init__(self):
        if self.ADMIN_USER_IDS is None:
            self.ADMIN_USER_IDS = []

    def save(self, path="config.json"):
        with open(path, 'w') as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def load(cls, path="config.json"):
        if os.path.exists(path):
            with open(path, 'r') as f:
                return cls(**json.load(f))
        return cls()

class SelfHealing:
    def __init__(self):
        self.errors = {}
        self.actions = []
        self.is_healthy = True

    def log(self, e, ctx=""):
        err_type = type(e).__name__
        self.errors[err_type] = self.errors.get(err_type, 0) + 1
        logger.error(f"{ctx}: {e}")

        if self.errors[err_type] >= 3:
            self.heal(err_type, e)

    def heal(self, err_type, e):
        if not config.HEALING_ENABLED:
            return

        strategies = {
            'ConnectionError': lambda: time.sleep(5),
            'APIError': lambda: genai.configure(api_key=config.GOOGLE_API_KEY) if config.GOOGLE_API_KEY else None,
            'ImportError': install_missing,
            'TesseractNotFoundError': self._fix_tesseract,
            'RuntimeError': lambda: __import__('gc').collect(),
        }

        try:
            if err_type in strategies:
                strategies[err_type]()
                self.errors[err_type] = 0
                logger.info(f"✅ Healed: {err_type}")
        except Exception as he:
            logger.error(f"❌ Heal failed: {he}")

    def _fix_tesseract(self):
        paths = ['/usr/bin/tesseract', '/usr/local/bin/tesseract', r'C:\Program Files\Tesseract-OCR\tesseract.exe']
        for p in paths:
            if os.path.exists(p):
                pytesseract.pytesseract.tesseract_cmd = p
                return True
        return False

class OCREngine:
    def __init__(self):
        self.seen = set()

    def preprocess(self, img):
        h, w = img.shape[:2]
        if w > 1280:
            img = cv2.resize(img, None, fx=1280/w, fy=1280/w)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresh

    def extract(self, frame):
        try:
            processed = self.preprocess(frame)
            data = pytesseract.image_to_data(processed, lang=config.OCR_LANGUAGE, output_type=pytesseract.Output.DICT)

            texts, confs = [], []
            for i, text in enumerate(data['text']):
                if int(data['conf'][i]) > 30 and text.strip():
                    texts.append(text)
                    confs.append(int(data['conf'][i]))

            full = ' '.join(texts)
            return {'text': full, 'conf': np.mean(confs)/100 if confs else 0, 'ok': True}
        except Exception as e:
            healer.log(e, "OCR")
            return {'text': '', 'conf': 0, 'ok': False}

    def is_question(self, text):
        if not text or len(text) < 10:
            return None

        h = hash(text[:50])
        if h in self.seen:
            return None

        indicators = ['?', 'what', 'which', 'who', 'when', 'where', 'how', 'क्या', 'कौन', 'कब', 'कहाँ', 'option', 'a)', 'b)', 'c)', 'answer']
        text_l = text.lower()

        if any(i in text_l for i in indicators):
            self.seen.add(h)
            if len(self.seen) > 1000:
                self.seen.clear()
            return {'text': text, 'time': datetime.now()}
        return None

class AIEngine:
    def __init__(self):
        self.model = None
        self.cache = {}
        self.last_call = 0

    def init(self):
        if not config.GOOGLE_API_KEY:
            return False
        genai.configure(api_key=config.GOOGLE_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        return True

    def answer(self, question):
        if not self.model and not self.init():
            return {'ans': 'AI not ready', 'exp': 'Configure API key', 'conf': 'Low'}

        now = time.time()
        if now - self.last_call < 1:
            time.sleep(1 - (now - self.last_call))

        ck = hash(question[:100])
        if ck in self.cache:
            return self.cache[ck]

        try:
            prompt = f"""Question: {question}
Give short Answer, brief Explanation, and Confidence (High/Medium/Low).
Format: Answer: ...
Explanation: ...
Confidence: ..."""

            resp = self.model.generate_content(prompt)
            self.last_call = time.time()

            txt = resp.text
            ans = self._extract(txt, 'Answer')
            exp = self._extract(txt, 'Explanation')
            conf = self._extract(txt, 'Confidence')

            result = {'ans': ans or txt[:200], 'exp': exp or '', 'conf': conf or 'Medium'}
            self.cache[ck] = result

            if len(self.cache) > 100:
                self.cache.pop(next(iter(self.cache)))

            return result
        except Exception as e:
            healer.log(e, "AI")
            return {'ans': 'Error', 'exp': str(e)[:100], 'conf': 'Low'}

    def _extract(self, txt, sec):
        for line in txt.split('\n'):
            if line.strip().lower().startswith(sec.lower() + ':'):
                return line.split(':', 1)[1].strip()
        return ""

class StreamHandler:
    def __init__(self):
        self.url = None
        self.cap = None
        self.running = False
        self.q = queue.Queue(maxsize=5)
        self.last_ans = 0
        self.stats = {'frames': 0, 'questions': 0, 'answers': 0, 'start': None}

    def get_stream_url(self, yt_url):
        try:
            opts = {'format': f'best[height<={config.STREAM_QUALITY[:-1]}]', 'quiet': True}
            with YoutubeDL(opts) as ydl:
                return ydl.extract_info(yt_url, download=False)['url']
        except Exception as e:
            healer.log(e, "Stream URL")
            return None

    def start(self, yt_url):
        try:
            self.url = self.get_stream_url(yt_url)
            if not self.url:
                return False

            self.cap = cv2.VideoCapture(self.url)
            if not self.cap.isOpened():
                raise Exception("Cannot open stream")

            self.running = True
            self.stats['start'] = datetime.now()

            threading.Thread(target=self._reader, daemon=True).start()
            threading.Thread(target=self._processor, daemon=True).start()

            logger.info(f"Stream started: {yt_url}")
            return True
        except Exception as e:
            healer.log(e, "Start Stream")
            return False

    def _reader(self):
        cnt = 0
        while self.running:
            try:
                ret, frame = self.cap.read()
                if not ret:
                    time.sleep(0.1)
                    continue
                cnt += 1
                if cnt % config.FRAME_SKIP != 0:
                    continue

                if self.q.full():
                    try:
                        self.q.get_nowait()
                    except:
                        pass
                self.q.put(frame)
            except Exception as e:
                healer.log(e, "Reader")
                time.sleep(1)

    def _processor(self):
        while self.running:
            try:
                frame = self.q.get(timeout=1)
                self.stats['frames'] += 1

                ocr = ocr_engine.extract(frame)
                if ocr['ok'] and ocr['conf'] > config.CONFIDENCE_THRESHOLD:
                    q = ocr_engine.is_question(ocr['text'])
                    if q:
                        self.stats['questions'] += 1
                        self._handle(q)
            except queue.Empty:
                continue
            except Exception as e:
                healer.log(e, "Processor")

    def _handle(self, q):
        now = time.time()
        if now - self.last_ans < config.ANSWER_COOLDOWN:
            return

        ai = ai_engine.answer(q['text'])
        msg = f"""📝 Question Detected

❓ {q['text'][:200]}...

✅ Answer: {ai['ans']}
📖 Explanation: {ai['exp']}
🎯 Confidence: {ai['conf']}"""

        asyncio.create_task(notify_admins(msg))
        self.last_ans = now
        self.stats['answers'] += 1
        logger.info(f"Answered: {q['text'][:50]}...")

    def stop(self):
        self.running = False
        if self.cap:
            self.cap.release()
        logger.info("Stream stopped")

class TelegramManager:
    def __init__(self):
        self.app = None
        self.stream = None

    async def start(self):
        if not config.TELEGRAM_TOKEN:
            print("❌ Set TELEGRAM_TOKEN first!")
            return False

        self.app = Application.builder().token(config.TELEGRAM_TOKEN).build()

        handlers = [
            ('start', self.cmd_start), ('join', self.cmd_join), ('stop', self.cmd_stop),
            ('status', self.cmd_status), ('stats', self.cmd_stats), ('heal', self.cmd_heal),
            ('pause', self.cmd_pause), ('resume', self.cmd_resume),
        ]

        for cmd, handler in handlers:
            self.app.add_handler(CommandHandler(cmd, handler))

        logger.info("Bot started")
        await self.app.initialize()
        await self.app.start()
        await self.app.run_polling()

    def is_admin(self, uid):
        return uid in config.ADMIN_USER_IDS

    async def cmd_start(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("""🤖 LiveGuru - YouTube Live AI Bot

Commands:
📺 /join <url> - Join stream
🛑 /stop - Stop bot
📊 /status - Health check
📈 /stats - Statistics
🔧 /heal - Healing status
⏸ /pause - Pause
▶️ /resume - Resume

By: Suman Mehta | github.com/sumanmehta/liveguru""")

    async def cmd_join(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("⛔ Unauthorized")
            return

        if not ctx.args:
            await update.message.reply_text("❌ Usage: /join <youtube_url>")
            return

        url = ctx.args[0]
        await update.message.reply_text(f"🔍 Joining: {url[:50]}...")

        ai_engine.init()
        self.stream = StreamHandler()

        if self.stream.start(url):
            await update.message.reply_text("✅ Stream joined! Monitoring...")
        else:
            await update.message.reply_text("❌ Failed to join")

    async def cmd_stop(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if self.stream:
            self.stream.stop()
            self.stream = None
        await update.message.reply_text("🛑 Stopped")

    async def cmd_status(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        h = healer.errors
        await update.message.reply_text(f"🏥 Health\nErrors: {sum(h.values())}\nHealing: {'ON' if config.HEALING_ENABLED else 'OFF'}")

    async def cmd_stats(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not self.stream:
            await update.message.reply_text("No active stream")
            return
        s = self.stream.stats
        uptime = datetime.now() - s['start'] if s['start'] else timedelta(0)
        await update.message.reply_text(f"📈 Stats\nUptime: {uptime}\nFrames: {s['frames']}\nQuestions: {s['questions']}\nAnswers: {s['answers']}")

    async def cmd_heal(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(f"🔧 Healing\nEnabled: {config.HEALING_ENABLED}\nRecent fixes: {len(healer.actions)}")

    async def cmd_pause(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if self.stream:
            self.stream.running = False
            await update.message.reply_text("⏸ Paused")

    async def cmd_resume(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if self.stream:
            self.stream.running = True
            await update.message.reply_text("▶️ Resumed")

async def notify_admins(msg):
    for admin in config.ADMIN_USER_IDS:
        try:
            await telegram_mgr.app.bot.send_message(admin, msg)
        except:
            pass

def setup():
    if not os.path.exists('.env'):
        print("\n🚀 LiveGuru First-Time Setup\n")
        token = input("1. Telegram Bot Token: ").strip()
        api = input("2. Google Gemini API Key: ").strip()
        admins = input("3. Your Telegram User ID: ").strip()

        with open('.env', 'w') as f:
            f.write(f"TELEGRAM_TOKEN={token}\n")
            f.write(f"GOOGLE_API_KEY={api}\n")
            f.write(f"ADMIN_USER_IDS={admins}\n")
        print("\n✅ Config saved!")

config = Config.load()
healer = SelfHealing()
ocr_engine = OCREngine()
ai_engine = AIEngine()
telegram_mgr = TelegramManager()

def main():
    setup()

    load_dotenv()
    config.TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '')
    config.GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')
    config.ADMIN_USER_IDS = [int(x) for x in os.getenv('ADMIN_USER_IDS', '').split(',') if x]
    config.save()

    print("🤖 Starting LiveGuru by Suman Mehta...")
    print(f"Admins: {config.ADMIN_USER_IDS}")

    try:
        asyncio.run(telegram_mgr.start())
    except Exception as e:
        logger.critical(f"Fatal: {e}")
        if config.AUTO_RESTART:
            print("🔄 Restarting in 5s...")
            time.sleep(5)
            os.execv(sys.executable, [sys.executable] + sys.argv)

if __name__ == "__main__":
    main()
