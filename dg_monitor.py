import requests
import datetime
import time
from bs4 import BeautifulSoup

BOT_TOKEN = "8134230045:AAForY5xzO6D4EioSYNfk1yPtF6-cl50ABI"
CHAT_ID = "485427847"

DEFAULT_DURATION = 15  # 初始预计时长（分钟）

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except Exception as e:
        print("Telegram发送失败：", e)

def check_dg():
    try:
        url = "https://dg18.co/wap/"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code != 200:
            return "收割"

        soup = BeautifulSoup(response.text, "html.parser")
        tables = soup.get_text()

        score = tables.count("连开") + tables.count("长龙") + tables.count("长连")

        if score >= 7:
            return "放水"
        elif score >= 4:
            return "中等胜率"
        else:
            return "收割"
    except:
        return "收割"

def format_time(minutes_from_now):
    end_time = (datetime.datetime.now() + datetime.timedelta(minutes=minutes_from_now))
    return end_time.strftime("%H:%M")

def main():
    send_telegram("✅ DG检测系统已启动（马来西亚时区 GMT+8）")
    current_status = None
    start_time = None
    estimated_end = None

    while True:
        now = datetime.datetime.now()
        now_time = now.strftime("%Y-%m-%d %H:%M:%S")
        status = check_dg()

        if status == "放水":
            if current_status != "放水":
                start_time = now
                estimated_end = now + datetime.timedelta(minutes=DEFAULT_DURATION)
                send_telegram(
                    f"🔥 现在是平台【放水时段】（胜率高）！\n"
                    f"预计放水结束时间：{estimated_end.strftime('%H:%M')}\n"
                    f"此局势预计：剩下 {DEFAULT_DURATION} 分钟"
                )
            else:
                # 延长预计时间（如果仍在放水）
                if (now > estimated_end - datetime.timedelta(minutes=5)):
                    estimated_end = now + datetime.timedelta(minutes=DEFAULT_DURATION)
            current_status = "放水"

        elif status == "中等胜率":
            if current_status != "中等胜率":
                start_time = now
                estimated_end = now + datetime.timedelta(minutes=DEFAULT_DURATION)
                send_telegram(
                    f"📡 检测到【中等胜率（中上）】时段\n"
                    f"预计结束时间：{estimated_end.strftime('%H:%M')}\n"
                    f"此局势预计：剩下 {DEFAULT_DURATION} 分钟"
                )
            else:
                if (now > estimated_end - datetime.timedelta(minutes=5)):
                    estimated_end = now + datetime.timedelta(minutes=DEFAULT_DURATION)
            current_status = "中等胜率"

        else:
            if current_status in ["放水", "中等胜率"]:
                end_time = now
                duration = (end_time - start_time).seconds // 60 if start_time else 0
                send_telegram(f"⚠️ 放水已结束，共持续 {duration} 分钟。")
            current_status = "收割"

        time.sleep(300)

if __name__ == "__main__":
    main()
