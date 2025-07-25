import os
import asyncio
import datetime
from playwright.async_api import async_playwright
import requests

# Telegram配置
TELEGRAM_TOKEN = "8134230045:AAForY5xzO6D4EioSYNfk1yPtF6-cl50ABI"
TELEGRAM_CHAT_ID = "485427847"

DG_URLS = [
    "https://dg18.co/",
    "https://dg18.co/wap/"
]

# 全局状态记录
last_state = "none"
last_start_time = None

# Telegram发送消息
def send_telegram_message(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message})

# 分析DG桌面HTML结构 (这里用简单逻辑模拟)
def analyze_tables(html: str) -> str:
    """
    返回状态：
    - 'water'  : 放水时段
    - 'medium' : 中等胜率（中上）
    - 'low'    : 胜率中等 / 收割
    """
    # 模拟规则判断：这里用 "庄庄庄庄" 和 "闲闲闲闲" 出现次数估算
    long_count = html.count("庄庄庄庄") + html.count("闲闲闲闲")
    if long_count > 15:  # 模拟 >=70%
        return 'water'
    elif 8 <= long_count <= 15:  # 模拟 55-69%
        return 'medium'
    return 'low'

async def fetch_dg_tables():
    combined_html = ""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        for url in DG_URLS:
            await page.goto(url, timeout=60000)
            # 点击“免费试玩” / “Free”
            try:
                await page.click("text=免费试玩")
            except:
                try:
                    await page.click("text=Free")
                except:
                    pass
            await page.wait_for_timeout(5000)  # 等待跳转加载
            combined_html += await page.content()
        await browser.close()
    return combined_html

async def main():
    global last_state, last_start_time
    html = await fetch_dg_tables()
    state = analyze_tables(html)

    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    if state == 'water':
        if last_state != 'water':
            last_state = 'water'
            last_start_time = now
            send_telegram_message(f"【放水时段】\n时间：{now_str}\n预计持续中...")
        else:
            # 更新预计剩余时间
            elapsed = (now - last_start_time).seconds // 60
            send_telegram_message(f"【放水持续中】\n已持续：{elapsed} 分钟\n时间：{now_str}")

    elif state == 'medium':
        if last_state != 'medium':
            last_state = 'medium'
            send_telegram_message(f"【中等胜率（中上）】\n时间：{now_str}\n请注意观察，接近放水结构。")

    else:  # low
        if last_state == 'water' and last_start_time:
            elapsed = (now - last_start_time).seconds // 60
            send_telegram_message(f"【放水已结束】\n结束时间：{now_str}\n本轮共持续：{elapsed} 分钟")
        last_state = 'low'

if __name__ == "__main__":
    asyncio.run(main())
