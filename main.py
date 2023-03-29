import discord
from sys import argv
from os import getenv
from os.path import exists
from base64 import b64decode
import firebase_admin as firebase
from dotenv import load_dotenv
from utility import log_print, get_cogs


log_print("Preparing Bot...", newline=True)

# 테스트 모드이면 True (> python main.py dev)
dev = len(argv) >= 2 and argv[1] == "dev"
bot = discord.Bot(owner_ids=[540481950763319317, 718285849888030720],
    debug_guilds=[1086542872607723550] if dev else None, intents=discord.Intents.all())

# 환경 변수
load_dotenv()

# 파이어베이스
log_print("Loading Firebase...")
fb_admin_file = "firebase-admin.json"
if not exists(fb_admin_file):
    log_print("firebase-admin.json not found, creating...")
    with open(fb_admin_file, 'w') as f:
        f.write(b64decode(getenv("FIREBASE_ADMIN_BASE64")).decode("utf-8"))
    log_print("Created firebase-admin.json")

cred = firebase.credentials.Certificate(fb_admin_file)
options = { "databaseURL": getenv("DATABASE_URL") }
firebase.initialize_app(cred, options)
log_print("Firebase loaded")

# 커맨드 불러오기
bot.load_extensions(*get_cogs())

# 토큰
token = getenv("TOKEN_ALPHA" if dev else "TOKEN")

# 봇 실행
log_print("Logging in...")
bot.run(token)
