import time
import requests
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Telegram 配置
TELEGRAM_TOKEN = "8134230045:AAForY5xzO6D4EioSYNfk1yPtF6-cl50ABI"
TELEGRAM_CHAT_ID = "485427847"

def send_telegram_message(message: str):
    """发送 Telegram 消息"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        requests.post(url, data=data)
    except Exception as e:
        print(f"[错误] 无法发送Telegram消息: {e}")

def init_driver():
    """初始化 Selenium Chrome Driver"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        return driver
    except Exception as e:
        send_telegram_message(f"❌ [DG监控错误] Chrome初始化失败: {e}")
        raise

def enter_dg_platform():
    """进入DG平台并点击免费试玩"""
    driver = init_driver()
    try:
        driver.get("https://dg18.co/")
        time.sleep(5)
        try:
            free_button = driver.find_element(By.XPATH, "//a[contains(text(), '免费试玩') or contains(text(), 'Free')]")
            free_button.click()
            time.sleep(5)  # 等待跳转
        except:
            pass
        return driver
    except Exception as e:
        send_telegram_message(f"❌ [DG监控错误] 进入DG平台失败: {e}")
        driver.quit()
        raise

def analyze_tables(driver):
    """分析 DG 桌面局势"""
    try:
        tables = driver.find_elements(By.CSS_SELECTOR, ".table-item")
        total_tables = len(tables)
        if total_tables == 0:
            return "收割时段", 0

        # 假设class中包含 'long' 代表长连 (需按DG页面实际HTML调整)
        long_trends = [t for t in tables if "long" in t.get_attribute("class")]
        long_count = len(long_trends)
        ratio = (long_count / total_tables) * 100

        if ratio >= 70:
            return "放水时段", ratio
        elif 55 <= ratio < 70:
            return "中等胜率（中上）", ratio
        else:
            return "收割时段", ratio
    except Exception as e:
        send_telegram_message(f"❌ [DG监控错误] 分析桌面失败: {e}")
        return "收割时段", 0

def monitor():
    send_telegram_message("✅ [DG检测系统已启动]（马来西亚 GMT+8）")
    last_status = None
    start_time = None

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
            send_telegram_message(f"❌ [DG监控循环错误]: {e}")

        time.sleep(300)  # 每5分钟检测一次

if __name__ == "__main__":
    monitor()
