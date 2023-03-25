import discord
import sys
import os
import firebase_admin as firebase
from dotenv import load_dotenv
from utility import get_cogs, log


log("로딩...", newline=2)
log(f"pwd - {os.getcwd()}")
log(f"path - {sys.path}")
log(f"argv - {sys.argv}")

dev = len(sys.argv) >= 2 and sys.argv[1] == "dev"
bot = discord.Bot(owner_ids=[540481950763319317, 718285849888030720],
    debug_guilds=[1086542872607723550] if dev else None, intents=discord.Intents.all())

# 데이터베이스 로드
os.chdir(sys.path[0])
cred = firebase.credentials.Certificate('firebase-admin.json')
firebase.initialize_app(cred, { "databaseURL": "https://nosookbot-default-rtdb.firebaseio.com" })

# Cogs 로드
bot.load_extensions(*get_cogs())

# 토큰 로드
load_dotenv()
token = os.getenv('TOKEN_ALPHA' if dev else 'TOKEN')

log("로그인 중...")
bot.run(token)
