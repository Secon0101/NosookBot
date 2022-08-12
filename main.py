import discord
from utility import get_cogs, log
from dotenv import load_dotenv
from os import getenv
from sys import argv


log("로딩...", newline=True)

dev = len(argv) >= 2 and argv[1] == "dev"
bot = discord.Bot(owner_ids=[540481950763319317, 718285849888030720], debug_guilds=[741194068939243531] if dev else None)

log("Cogs 로드 중...")
bot.load_extensions(*get_cogs())
log("Cogs 로드 완료")

log("토큰 읽는 중...")
load_dotenv()
token = getenv('TOKEN_ALPHA' if dev else 'TOKEN')
log("토큰 읽기 완료")

log("로그인 중...")
bot.run(token)
