import discord
from discord.ext import commands
from utility import get_cogs, log


class Core(commands.Cog):
    """ 노숙봇 핵심 기능들 """
    def __init__(self, bot: discord.Bot):
        self.bot = bot
    
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.change_presence(activity=discord.Game(name="노숙"))
        log(f"Logged in as {self.bot.user} ({len(self.bot.guilds)} server(s))\n")
    
    
    @commands.slash_command(name="리로드", description="(Owner 전용)")
    @commands.is_owner()
    async def slash_reload(self, ctx: discord.ApplicationContext):
        log("Reloading...")
        for cog in get_cogs():
            self.bot.unload_extension(cog)
            self.bot.load_extension(cog)
        respond = await ctx.respond("🔄 봇을 리로드하였습니다.")
        await respond.delete_original_message(delay=2)
        log("Reload completed", newline=True)
    
    
    @commands.slash_command(name="노숙봇", description="노숙 하는 중")
    async def slash_info(self, ctx: discord.ApplicationContext):
        log(f"{Core.__name__} - {ctx.author.name}({ctx.author.id}) used /{ctx.command.name}")
        embed = discord.Embed(title="노숙봇", color=0x78b159)  # 봇 버전
        embed.add_field(name="v0.3.1", value="- 24시간 호스팅!")
        embed.add_field(name="v0.3", value="- 시간 구간 내에 통화 기록이 없는 사용자 숨김 \n- 임베드에 타임스탬프 추가")
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text=f"Made by {self.bot.get_user(self.bot.owner_ids[0])}",
                         icon_url=self.bot.get_user(self.bot.owner_ids[0]).avatar.url)
        await ctx.respond(embed=embed)


def setup(bot: discord.Bot):
    try:
        bot.add_cog(Core(bot))
        log(f"Module {Core.__name__} loaded")
    except Exception as e:
        log(f"Failed to load module {Core.__name__}: \n{e}")
