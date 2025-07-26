import time
import requests
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# Telegram 配置
TELEGRAM_TOKEN = "8134230045:AAForY5xzO6D4EioSYNfk1yPtF6-cl50ABI"
TELEGRAM_CHAT_ID = "485427847"

# 状态变量
INITIAL_START = True   # 用于首次启动提醒

# Telegram 消息发送
def send_telegram_message(message: str):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        requests.post(url, data=data)
    except Exception as e:
        print(f"[错误] 无法发送Telegram消息: {e}")

# 初始化 Selenium
def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

# 进入DG平台
def enter_dg_platform():
    driver = init_driver()
    driver.get("https://dg18.co/")
    time.sleep(5)
    try:
        free_button = driver.find_element(By.XPATH, "//a[contains(text(), '免费试玩') or contains(text(), 'Free')]")
        free_button.click()
        time.sleep(5)
    except:
        pass
    return driver

# 分析桌面局势
def analyze_tables(driver):
    try:
        tables = driver.find_elements(By.CSS_SELECTOR, ".table-item")
        total_tables = len(tables)
        if total_tables == 0:
            return "收割时段", 0

        # 检查“长连 / 长龙”桌子
        long_trends = []
        for t in tables:
            classes = t.get_attribute("class").lower()
            # 假设 class 包含 'long' 或 'streak' 表示长龙（需按DG实际结构改）
            if "long" in classes or "streak" in classes:
                long_trends.append(t)

        long_count = len(long_trends)
        ratio = (long_count / total_tables) * 100

        # 假信号过滤：如果仅有1桌长连且其他桌混乱，不算放水
        if long_count <= 1 and ratio < 55:
            return "收割时段", ratio

        # 判断时段
        if ratio >= 70:
            return "放水时段", ratio
        elif 55 <= ratio < 70:
            return "中等胜率（中上）", ratio
        else:
            return "收割时段", ratio
    except Exception as e:
        print(f"分析桌面时出错: {e}")
        return "收割时段", 0

# 监控函数
def monitor():
    global INITIAL_START
    last_status = None
    start_time = None

    if INITIAL_START:
        send_telegram_message("✅ DG监控系统已启动（马来西亚 GMT+8）。")
        INITIAL_START = False

    while True:
        try:
            driver = enter_dg_platform()
            status, ratio = analyze_tables(driver)
            driver.quit()

            now = datetime.now()
            if status in ["放水时段", "中等胜率（中上）"]:
                if last_status != status:
                    start_time = now
                    end_time = now + timedelta(minutes=10)
                    msg = f"🔥 现在是平台【{status}】！\n预计放水结束时间：{end_time.strftime('%H:%M')}\n此局势预计：剩下10分钟"
                    send_telegram_message(msg)
            else:
                if last_status in ["放水时段", "中等胜率（中上）"] and start_time:
                    duration = int((now - start_time).total_seconds() / 60)
                    send_telegram_message(f"⚠️ {last_status}已结束，共持续 {duration} 分钟。")
                    start_time = None

            last_status = status
        except Exception as e:
            send_telegram_message(f"❌ [DG监控错误]: {e}")

        time.sleep(300)  # 每5分钟检测一次

if __name__ == "__main__":
    monitor()
