import time
import datetime
import pytz
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# ========== 配置 ==========
TELEGRAM_BOT_TOKEN = "8134230045:AAForY5xzO6D4EioSYNfk1yPtF6-cl50ABI"
TELEGRAM_CHAT_ID = "485427847"
TIMEZONE = pytz.timezone("Asia/Kuala_Lumpur")  # GMT+8 马来西亚时区
CHECK_INTERVAL = 300  # 每5分钟检测一次

# ========== 发送Telegram消息 ==========
def send_telegram_message(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"[错误] Telegram发送失败：{e}")

# ========== 判断牌面结构 ==========
def is_good_pattern(history_text):
    """
    判断当前牌路是否属于放水结构：
    - >=5连庄 或 >=5连闲
    - >=8连庄 或 >=8连闲 (长龙)
    """
    if "庄庄庄庄庄" in history_text or "闲闲闲闲闲" in history_text:
        return True
    if "庄庄庄庄庄庄庄庄" in history_text or "闲闲闲闲闲闲闲闲" in history_text:
        return True
    return False

# ========== 检测DG平台 ==========
def detect_dg_platform():
    """
    1. 打开 DG 网站 (https://dg18.co/wap/)
    2. 点击 免费试玩 / Free
    3. 读取所有牌桌走势
    4. 统计“放水结构”桌面比例
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get("https://dg18.co/wap/")
    time.sleep(6)

    try:
        free_button = driver.find_element(By.XPATH, "//button[contains(text(),'免费试玩') or contains(text(),'Free')]")
        free_button.click()
        time.sleep(6)
    except:
        driver.quit()
        return "收割", 0

    tables = driver.find_elements(By.CLASS_NAME, "table-class")  # 这里需要替换成真实的class
    total = len(tables)
    if total == 0:
        driver.quit()
        return "收割", 0

    good_count = 0
    for t in tables:
        text = t.text
        if is_good_pattern(text):
            good_count += 1

    driver.quit()

    ratio = (good_count / total) * 100
    if ratio >= 70:
        return "放水", ratio
    elif 55 <= ratio < 70:
        return "中等胜率", ratio
    else:
        return "收割", ratio

# ========== 主监控循环 ==========
def main():
    send_telegram_message("✅ DG监控系统启动 (Version 4.6) – 24小时检测模式。")

    current_status = None
    state_start = None

    while True:
        now_str = datetime.datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")
        status, percent = detect_dg_platform()

        if status in ["放水", "中等胜率"]:
            if current_status != status:
                current_status = status
                state_start = time.time()
                estimated_end = (datetime.datetime.now(TIMEZONE) + datetime.timedelta(minutes=10)).strftime("%H:%M")
                send_telegram_message(
                    f"⚡ 现在是平台 {status} 时段\n"
                    f"预计放水结束时间：{estimated_end}\n"
                    f"此局势预计：剩下10分钟\n"
                    f"当前时间：{now_str}\n"
                    f"好路桌面比例：{percent:.1f}%"
                )
        else:
            if current_status in ["放水", "中等胜率"]:
                duration = int((time.time() - state_start) / 60)
                send_telegram_message(f"❌ {current_status} 已结束，共持续 {duration} 分钟。")
                current_status = None

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
