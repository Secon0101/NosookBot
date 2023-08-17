import discord
from discord.ext import commands
from datetime import datetime
from pytz import timezone
from utility import log, get_cogs, cog_logger


class Core(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.log_channel: discord.TextChannel = None
        self.owner_mention: str = None
    
    
    @commands.Cog.listener()
    async def on_ready(self):
        log_channel_id = 1138430000442384454
        self.log_channel = self.bot.get_channel(log_channel_id) or await self.bot.fetch_channel(log_channel_id)
        self.owner_mention = self.bot.get_user(self.bot.owner_ids[0]).mention
        
        await self.bot.change_presence(activity=discord.Game(name="노숙"))
        
        guild_count = len(self.bot.guilds)
        log(f"{self.bot.user.display_name} 온라인! (서버 {guild_count}개)")
        await self.log_channel.send(f"온라인! (서버 {guild_count}개)")
    
    
    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        log(f"{guild.name}({guild.id}) 서버에 초대됨")
        await self.log_channel.send(f"{self.owner_mention} `{guild.name}({guild.id})` 서버에 초대되었습니다!!!!")
    
    
    @commands.Cog.listener()
    async def on_application_command(self, ctx: discord.ApplicationContext):
        log(f"{ctx.user.name}({ctx.user.id})(이)가 /{ctx.command.name} 사용")
    
    
    @commands.slash_command(name="노숙봇", description="봇 정보를 표시합니다.")
    async def slash_info(self, ctx: discord.ApplicationContext):
        embed = discord.Embed(title="🟢 노숙봇", description="https://github.com/Secon0101/NosookBot", color=0x78b159)
        embed.add_field(name="v0.5.1", value="""
* 서버 아이콘이 없으면 타임라인이 생성되지 않는 버그 수정
            """, inline=False)
        embed.add_field(name="v0.5", value="""
* 리얼타임 채널 메시지 삭제 대기 시간 5분에서 60분으로 변경
            """, inline=False)
        embed.add_field(name="v0.4", value="""
* 전체 코드 리메이크!
* **`/리얼타임`** 명령어로 실시간 타임라인 채널을 설정할 수 있습니다. 이름 그대로 실시간으로 업데이트됩니다! 그 채널에 올라오는 메시지는 5분 뒤에 삭제됩니다.
* **`/타임라인`** 명령어로 타임라인을 확인할 수 있습니다. 시간 구간 매개변수를 사용해서 그 시간 동안의 타임라인을 볼 수 있습니다.
* 봇 실행 시 실시간 타임라인을 업데이트하고 채널 메시지를 삭제합니다.
* 모든 리얼타임 채널은 한 시간 간격으로 업데이트됩니다.
            """, inline=False)
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text=f"Made by {self.bot.get_user(self.bot.owner_ids[0]).display_name}",
                         icon_url=self.bot.get_user(self.bot.owner_ids[0]).avatar.url)
        await ctx.respond(embed=embed)
    
    
    @commands.slash_command(name="리로드", description="Cogs를 새로고침합니다.", guild_ids=[741194068939243531])
    @commands.is_owner()
    async def slash_reload(self, ctx: discord.ApplicationContext):
        log("리로드 중")
        for cog in get_cogs():
            self.bot.unload_extension(cog)
            self.bot.load_extension(cog)
        log("리로드 완료")
        await ctx.respond("🔄 봇을 리로드하였습니다.", ephemeral=True)
    
    
    @commands.Cog.listener()
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error: discord.DiscordException):
        if isinstance(error, commands.errors.MissingPermissions):
            await ctx.respond(f"`{', '.join(error.missing_permissions)}` 권한이 필요합니다.", ephemeral=True)
            return
        
        embed = discord.Embed(title="❌ 오류가 발생했습니다.", description=f"```py\n{error}```", color=0xff0000)
        embed.set_footer(text=f"디스코드 {self.bot.get_user(self.bot.owner_ids[0]).display_name}(으)로 문의해주세요.",
                         icon_url=self.bot.user.display_avatar.url)
        embed.timestamp = datetime.now(timezone('Asia/Seoul'))
        await ctx.respond(embed=embed, ephemeral=True)
        
        await self.log_channel.send(f"{self.owner_mention} `/{ctx.command.name}` 실행 오류! 당장 로그를 확인하세요!")
        log(f"/{ctx.command.name} 실행 오류! 아래 예외를 확인하세요.")
        raise error
    


@cog_logger
def setup(bot: discord.Bot):
    bot.add_cog(Core(bot))
