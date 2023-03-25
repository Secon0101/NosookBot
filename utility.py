from datetime import datetime
from pytz import timezone
from os import listdir


def log(ctx: str, newline: int = 0):
    time = datetime.now(timezone('Asia/Seoul')).strftime("%y/%m/%d %H:%M:%S")
    if newline: print()
    print(f"[{time}] {ctx}")

def get_cogs() -> list[str]:
    cogs = []
    for file in listdir("Cogs"):
        if file.endswith('.py') and not file.startswith('_'):
            cogs.append(f"Cogs.{file[:-3]}")
    return cogs
