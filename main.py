import discord
from utility import get_cogs, log
import dotenv, os, sys


log("로딩...", newline=True)

dev = len(sys.argv) >= 2 and sys.argv[1] == "dev"
bot = discord.Bot(owner_ids=[540481950763319317, 718285849888030720], debug_guilds=[741194068939243531] if dev else None)


@bot.event
async def on_ready():
    log(f"{bot.user}(으)로 로그인 (서버 {len(bot.guilds)}개)\n")
    await bot.change_presence(activity=discord.Game(name="노숙"))


log("Cogs 로드 중...")
bot.load_extensions(*get_cogs())
log("Cogs 로드 완료")


log("토큰 읽는 중...")
dotenv.load_dotenv()
token = os.getenv('TOKEN_ALPHA' if dev else 'TOKEN')
log("토큰 읽기 완료")

log("로그인 중...")
bot.run(token)
