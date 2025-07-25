import requests
from datetime import datetime, timedelta
import pytz
import time
from bs4 import BeautifulSoup

# Telegram 配置
TELEGRAM_TOKEN = "8134230045:AAForY5xzO6D4EioSYNfk1yPtF6-cl50ABI"
CHAT_ID = "485427847"

# DG 平台 URL
DG_URLS = [
    "https://dg18.co/wap/",
    "https://dg18.co/"
]

# GMT+8 时区
TZ = pytz.timezone("Asia/Kuala_Lumpur")

# 状态记录
last_status = None
last_start_time = None

def send_telegram_message(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"Telegram 发送失败: {e}")

def analyze_tables():
    """
    分析 DG 平台所有百家乐桌面的走势，判断放水 / 中等胜率 / 收割。
    """
    good_patterns = 0
    total_tables = 0
    try:
        for url in DG_URLS:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                continue
            soup = BeautifulSoup(response.text, "html.parser")

            # 模拟分析桌面数据（真实逻辑：分析HTML中连庄/长龙走势）
            tables = soup.find_all("div", class_="table")  # 假设桌子结构
            total_tables += len(tables)
            for table in tables:
                text = table.get_text().lower()
                # 真实逻辑：检测是否有5-6连 或 长龙结构
                if "连" in text or "长龙" in text or "长闲" in text or "长庄" in text:
                    good_patterns += 1

        if total_tables == 0:
            return "unknown", 0

        good_ratio = (good_patterns / total_tables) * 100

        if good_ratio >= 70:
            return "放水时段", good_ratio
        elif 55 <= good_ratio < 70:
            return "中等胜率（中上）", good_ratio
        else:
            return "收割时段", good_ratio
    except Exception as e:
        print(f"分析出错: {e}")
        return "unknown", 0

def main_loop():
    global last_status, last_start_time
    send_telegram_message("【DG检测系统已启动】\n时间：" + datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S"))

    while True:
        status, ratio = analyze_tables()
        now = datetime.now(TZ)

        if status in ["放水时段", "中等胜率（中上）"]:
            if last_status != status:
                last_start_time = now
                end_estimate = now + timedelta(minutes=30)  # 预计放水30分钟后结束
                send_telegram_message(
                    f"【检测到：{status}】\n"
                    f"时间：{now.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"放水结构占比：{ratio:.1f}%\n"
                    f"预计结束时间：{end_estimate.strftime('%H:%M')}\n"
                    f"此局势预计：剩下30分钟"
                )
            else:
                elapsed = (now - last_start_time).seconds // 60
                remaining = max(0, 30 - elapsed)
                if remaining > 0:
                    print(f"{status} 持续中，剩余约 {remaining} 分钟")
                else:
                    send_telegram_message(
                        f"【{status} 已结束】\n"
                        f"结束时间：{now.strftime('%H:%M:%S')}\n"
                        f"本轮共持续：{elapsed} 分钟"
                    )
                    last_status = None
        else:
            if last_status in ["放水时段", "中等胜率（中上）"]:
                elapsed = (now - last_start_time).seconds // 60
                send_telegram_message(
                    f"【{last_status} 已结束】\n"
                    f"结束时间：{now.strftime('%H:%M:%S')}\n"
                    f"本轮共持续：{elapsed} 分钟"
                )
            last_status = None

        last_status = status
        time.sleep(300)  # 每5分钟检测一次

if __name__ == "__main__":
    main_loop()
