import requests
import time
import datetime
import pytz
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

# Telegram配置
TELEGRAM_BOT_TOKEN = "8134230045:AAForY5xzO6D4EioSYNfk1yPtF6-cl50ABI"
TELEGRAM_CHAT_ID = "485427847"

# 马来西亚时区
MY_TZ = pytz.timezone("Asia/Kuala_Lumpur")

# 发送Telegram消息
def send_telegram_message(msg: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": msg}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Telegram发送失败：", e)

# 启动无头浏览器
def start_browser():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=chrome_options)
    return driver

# 检测DG平台牌桌
def detect_dg_platform():
    driver = start_browser()
    try:
        driver.get("https://dg18.co/")
        time.sleep(3)
        # 点击“免费试玩”按钮
        try:
            free_btn = driver.find_element(By.XPATH, "//a[contains(text(),'免费试玩') or contains(text(),'Free')]")
            free_btn.click()
            time.sleep(5)
        except:
            print("未找到免费试玩按钮")
            return ("收割", 0)
        
        # 等待安全验证 (此处可加入自动化滑块逻辑)
        # 模拟直接进入牌桌页面
        tables = driver.find_elements(By.CLASS_NAME, "table-road")
        if not tables:
            return ("收割", 0)
        
        # 统计长连/长龙比例
        long_tables = 0
        total_tables = len(tables)
        for t in tables:
            road_text = t.text
            if "庄庄庄庄" in road_text or "闲闲闲闲" in road_text or "庄庄庄庄庄庄" in road_text:
                long_tables += 1
        
        percent = int((long_tables / total_tables) * 100)
        if percent >= 70:
            return ("放水", percent)
        elif 55 <= percent < 70:
            return ("中等胜率", percent)
        else:
            return ("收割", percent)
    finally:
        driver.quit()

# 主循环
def main_loop():
    send_telegram_message("DG监控系统 Version 4.2 已启动！")

    current_state = None
    state_start_time = None

    while True:
        now = datetime.datetime.now(MY_TZ).strftime("%Y-%m-%d %H:%M:%S")
        status, percent = detect_dg_platform()

        if status in ["放水", "中等胜率"]:
            if current_state != status:
                current_state = status
                state_start_time = time.time()
                end_time_est = (datetime.datetime.now(MY_TZ) + datetime.timedelta(minutes=10)).strftime("%H:%M")
                send_telegram_message(
                    f"当前平台：{status}时段（胜率提高）\n"
                    f"预计放水结束时间：{end_time_est}\n"
                    f"此局势预计：剩下10分钟\n"
                    f"当前检测时间：{now}\n"
                    f"当前放水桌面比例：{percent}%"
                )
        else:
            if current_state in ["放水", "中等胜率"]:
                duration = int((time.time() - state_start_time) / 60)
                send_telegram_message(f"{current_state}已结束，共持续 {duration} 分钟。")
                current_state = None

        time.sleep(300)  # 每5分钟检测一次

if __name__ == "__main__":
    main_loop()
