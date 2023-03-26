""" 전역적으로 쓰이는 함수 모음 """

from datetime import datetime
from pytz import timezone
from os import listdir
from discord.abc import Messageable


log_channel: Messageable

def set_log_channel(channel: Messageable):
    """ log() 함수가 사용할 로그 채널을 설정한다. """
    global log_channel
    log_channel = channel

def log_print(ctx: str, newline: int = 0) -> str:
    """ 로그를 콘솔에 출력한다. """
    time = datetime.now(timezone('Asia/Seoul')).strftime("%y/%m/%d %H:%M:%S")
    if newline: print()
    text = f"[{time}] {ctx}"
    print(text)
    return text

async def log(ctx, newline: int = 0):
    """ 로그를 콘솔에 출력하고, 노숙봇 로그 채널에 채팅을 올린다. """
    text = log_print(ctx, newline)
    if log_channel is not None:
        await log_channel.send(text)

def get_cogs() -> map:
    """ Cogs 폴더에 있는 모든 Cog 목록을 반환한다. """
    return map(lambda cog: f"Cogs.{cog[:-3]}",
        filter(lambda file: file.endswith(".py"), listdir("Cogs")))
    # cogs = []
    # for file in listdir("Cogs"):
    #     if file.endswith('.py') and not file.startswith('_'):
    #         cogs.append(f"Cogs.{file[:-3]}")
    # return cogs
