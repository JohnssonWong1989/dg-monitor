import time
import requests
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Telegram 配置
TELEGRAM_TOKEN = "8134230045:AAForY5xzO6D4EioSYNfk1yPtF6-cl50ABI"
TELEGRAM_CHAT_ID = "485427847"

# 发送 Telegram 消息
def send_telegram_message(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"发送Telegram消息失败: {e}")

# 启动浏览器（无头模式）
def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=chrome_options)
    return driver

# 进入DG平台
def enter_dg_platform():
    driver = init_driver()
    driver.get("https://dg18.co/")
    try:
        free_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), '免费试玩') or contains(text(), 'Free')]"))
        )
        free_button.click()
        # 等待滚动验证
        time.sleep(5)
    except:
        pass
    return driver

# 分析桌面局势
def analyze_tables(driver):
    # 示例逻辑（需根据DG页面结构调整）
    tables = driver.find_elements(By.CSS_SELECTOR, ".table-item")
    total_tables = len(tables)
    if total_tables == 0:
        return "收割时段", 0

    # 假设通过class检测长连 (需按实际HTML结构优化)
    long_trends = [t for t in tables if "long" in t.get_attribute("class")]
    long_count = len(long_trends)
    ratio = (long_count / total_tables) * 100

    if ratio >= 70:
        return "放水时段", ratio
    elif 55 <= ratio < 70:
        return "中等胜率（中上）", ratio
    else:
        return "收割时段", ratio

# 主检测逻辑
def monitor():
    send_telegram_message("✅ DG检测系统已启动（马来西亚 GMT+8）")
    last_status = None
    start_time = None

    while True:
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
        time.sleep(300)  # 每5分钟检测一次

if __name__ == "__main__":
    monitor()
