import requests
from bs4 import BeautifulSoup
import datetime
import asyncio

# Telegram 配置
TELEGRAM_TOKEN = "8134230045:AAForY5xzO6D4EioSYNfk1yPtF6-cl50ABI"
TELEGRAM_CHAT_ID = "485427847"
TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

# DG 平台链接
DG_URLS = [
    "https://dg18.co/wap/",
    "https://dg18.co/"
]

# 放水判断阈值
WATER_THRESHOLD = 0.70   # 70% 以上放水结构
MEDIUM_THRESHOLD = 0.55  # 55%-69% 中等胜率（中上）

# 全局状态
last_state = None
last_start_time = None

def send_telegram_message(message: str):
    """发送 Telegram 消息"""
    try:
        requests.post(TELEGRAM_URL, data={"chat_id": TELEGRAM_CHAT_ID, "text": message})
    except Exception as e:
        print(f"Telegram 发送失败: {e}")

async def fetch_dg_tables():
    """抓取 DG 平台页面内容"""
    try:
        for url in DG_URLS:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.text
        return ""
    except Exception as e:
        print(f"获取 DG 页面失败: {e}")
        return ""

def analyze_tables(html: str) -> str:
    """
    分析 DG 桌面 HTML，判断是放水时段、中等胜率、胜率中等或收割时段。
    """
    if not html:
        return "low"

    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("div", class_="road-container")

    if not tables:
        return "low"

    total_tables = len(tables)
    water_like = 0  # 类似放水结构的桌面数量

    for t in tables:
        road_text = t.get_text()
        # 判断是否有长连/长龙（连续庄或闲 >=5 次）
        if "庄庄庄庄庄" in road_text or "闲闲闲闲闲" in road_text:
            water_like += 1
        # 检查多连（例如 3庄3闲连续）
        elif "庄庄庄闲闲闲" in road_text or "闲闲闲庄庄庄" in road_text:
            water_like += 0.5  # 适当加权

    ratio = water_like / total_tables
    print(f"检测结果: 放水桌面比例 = {ratio:.2f}")

    if ratio >= WATER_THRESHOLD:
        return "water"
    elif ratio >= MEDIUM_THRESHOLD:
        return "medium"
    else:
        return "low"

async def main():
    global last_state, last_start_time
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    # 第一次运行提醒
    if last_state is None:
        send_telegram_message(f"【DG检测系统已启动】\n时间：{now_str}")

    html = await fetch_dg_tables()
    state = analyze_tables(html)

    if state == "water":
        if last_state != "water":
            last_state = "water"
            last_start_time = now
            send_telegram_message(f"【放水时段】\n时间：{now_str}\n预计放水中...")
        else:
            elapsed = (now - last_start_time).seconds // 60
            send_telegram_message(f"【放水持续中】\n已持续：{elapsed} 分钟\n时间：{now_str}")

    elif state == "medium":
        if last_state != "medium":
            last_state = "medium"
            last_start_time = now
            send_telegram_message(f"【中等胜率（中上）】\n时间：{now_str}\n接近放水结构。")
        else:
            elapsed = (now - last_start_time).seconds // 60
            send_telegram_message(f"【中等胜率持续中】\n已持续：{elapsed} 分钟\n时间：{now_str}")

    else:  # low
        if last_state in ["water", "medium"] and last_start_time:
            elapsed = (now - last_start_time).seconds // 60
            send_telegram_message(f"【放水/中等胜率已结束】\n结束时间：{now_str}\n本轮共持续：{elapsed} 分钟")
        last_state = "low"

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
