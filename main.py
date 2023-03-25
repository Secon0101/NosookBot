import discord
import sys
import os
import firebase_admin as firebase
from dotenv import load_dotenv
from utility import get_cogs, log


log("Loading...", newline=True)

# 테스트 모드이면 True (> python main.py dev)
dev = len(sys.argv) >= 2 and sys.argv[1] == "dev"
bot = discord.Bot(owner_ids=[540481950763319317, 718285849888030720],
    debug_guilds=[1086542872607723550] if dev else None, intents=discord.Intents.all())

# 환경 변수
load_dotenv()

# 파이어베이스
filename = "firebase-admin.json"
if not os.path.exists(filename):
    from base64 import b64decode
    with open(filename, 'w') as f:
        text = b64decode(os.getenv("FIREBASE_ADMIN")).decode("utf-8")
        f.write(text)

cred = firebase.credentials.Certificate(filename)
options = { "databaseURL": "https://nosookbot-default-rtdb.firebaseio.com" }
firebase.initialize_app(cred, options)

# 커맨드 불러오기
bot.load_extensions(*get_cogs())

# 토큰
token = os.getenv("TOKEN_ALPHA" if dev else "TOKEN")

# 봇 실행
log("Logging in...")
bot.run(token)
