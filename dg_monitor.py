import time
import requests
import datetime
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# ========== 配置 ==========
BOT_TOKEN = "8134230045:AAForY5xzO6D4EioSYNfk1yPtF6-cl50ABI"
CHAT_ID = "485427847"
CHECK_INTERVAL = 300  # 每5分钟检测一次
TIMEZONE_OFFSET = 8  # GMT+8

# ========== 提醒函数 ==========
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"发送Telegram消息失败: {e}")

# ========== 检测 DG 平台牌路 ==========
def check_dg_tables():
    """
    模拟访问DG平台，抓取全部桌面牌路信息
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            page.goto("https://dg18.co/wap/")
            page.click("text=免费试玩")
            page.wait_for_timeout(3000)

            html = page.content()
            browser.close()
        return html
    except Exception as e:
        print(f"DG平台检测失败: {e}")
        return ""

# ========== 牌路解析和放水判断 ==========
def analyze_tables(html):
    """
    分析DG桌面是否进入放水时段、中等胜率，或收割时段
    """
    soup = BeautifulSoup(html, "html.parser")
    # 模拟：根据你的规则判断是否有70%桌面是长龙/长连
    # 这里用关键词匹配替代实际复杂牌路识别逻辑（真实部署需接入OCR/图像检测）
    table_text = soup.get_text()
    
    # 假设检测逻辑
    count_long = table_text.count("庄庄庄庄") + table_text.count("闲闲闲闲")
    count_total = table_text.count("庄") + table_text.count("闲")

    if count_total == 0:
        return "收割时段"

    ratio = (count_long / count_total) * 100
    print(f"检测结果：长连比例 {ratio:.2f}%")

    if ratio >= 70:
        return "放水时段"
    elif 55 <= ratio < 70:
        return "中等胜率（中上）"
    else:
        return "收割时段"

# ========== 放水时段追踪 ==========
class StateTracker:
    def __init__(self):
        self.state = "收割时段"
        self.start_time = None

    def update(self, new_state):
        now = datetime.datetime.utcnow() + datetime.timedelta(hours=TIMEZONE_OFFSET)

        if new_state == "放水时段":
            if self.state != "放水时段":
                self.start_time = now
                send_telegram_message(f"当前平台：放水时段（胜率提高）\n预计放水结束时间：未知\n此局势预计：持续中")
        elif self.state == "放水时段" and new_state != "放水时段":
            duration = (now - self.start_time).seconds // 60
            send_telegram_message(f"放水已结束，共持续 {duration} 分钟")

        elif new_state == "中等胜率（中上）":
            if self.state != "中等胜率（中上）":
                self.start_time = now
                send_telegram_message(f"当前平台：中等胜率（中上）\n预计结束时间：未知\n此局势预计：持续中")
        elif self.state == "中等胜率（中上）" and new_state != "中等胜率（中上）":
            duration = (now - self.start_time).seconds // 60
            send_telegram_message(f"中等胜率已结束，共持续 {duration} 分钟")

        self.state = new_state

# ========== 主循环 ==========
if __name__ == "__main__":
    send_telegram_message("DG百家乐放水检测系统已启动 (Version 4.1)")

    tracker = StateTracker()

    while True:
        html = check_dg_tables()
        if html:
            state = analyze_tables(html)
            tracker.update(state)
        else:
            print("无法获取DG桌面信息")
        time.sleep(CHECK_INTERVAL)
