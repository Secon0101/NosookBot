import discord
from utility import get_cogs, log
from dotenv import load_dotenv
from os import getenv
from sys import argv
import firebase_admin as firebase


log("로딩...", newline=True)

dev = len(argv) >= 2 and argv[1] == "dev"
bot = discord.Bot(owner_ids=[540481950763319317, 718285849888030720], debug_guilds=[741194068939243531] if dev else None, intents=discord.Intents.all())

# 데이터베이스 로드
cred = firebase.credentials.Certificate('firebase-admin.json')
firebase.initialize_app(cred, { "databaseURL": "https://nosookbot-default-rtdb.firebaseio.com" })

# Cogs 로드
bot.load_extensions(*get_cogs())

# 토큰 로드
load_dotenv()
token = getenv('TOKEN_ALPHA' if dev else 'TOKEN')

log("로그인 중...")
bot.run(token)
