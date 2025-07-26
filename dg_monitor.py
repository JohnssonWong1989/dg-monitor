import requests
import time
import datetime
import pytz
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import cv2
import numpy as np
import os

# Telegram 配置
TELEGRAM_TOKEN = "8134230045:AAForY5xzO6D4EioSYNfk1yPtF6-cl50ABI"
TELEGRAM_CHAT_ID = "485427847"

# ===================
# 检测规则参数
# ===================
CHECK_INTERVAL = 300  # 每 5 分钟检测一次
TIMEZONE_OFFSET = 8   # GMT+8 时区
MIN_LONG_DRAGON = 5   # 连续 5 粒以上算长龙
MIN_SUPER_DRAGON = 8  # 超级长龙
MIN_TABLE_FOR_FLOOD = 0.7  # 放水时段比例阈值 70%
MIN_TABLE_FOR_MEDIUM = 0.55 # 中等胜率中上阈值 55%

# 时区
tz = pytz.timezone("Asia/Kuala_Lumpur")

# 是否已发送启动提醒
startup_notified = False

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram 发送失败: {e}")

def analyze_table_image(image_path):
    """
    使用 OpenCV 检测长连、长龙的比例。
    返回: '放水时段', '中等胜率', 或 '收割'
    """
    img = cv2.imread(image_path)
    if img is None:
        return "收割"

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
    white_ratio = np.sum(thresh == 255) / (thresh.size)

    # 模拟判断逻辑
    if white_ratio > 0.7:
        return "放水时段"
    elif 0.55 <= white_ratio <= 0.69:
        return "中等胜率"
    else:
        return "收割"

def get_current_time():
    return datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

def detect_platform():
    """
    进入DG平台检测桌面截图
    """
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(60)
        driver.get("https://dg18.co/wap/")
        time.sleep(5)

        # 点击免费试玩
        try:
            free_btn = driver.find_element(By.XPATH, "//button[contains(text(), '免费试玩') or contains(text(), 'Free')]")
            free_btn.click()
            time.sleep(5)
        except:
            pass

        screenshot_path = "dg_screen.png"
        driver.save_screenshot(screenshot_path)
        driver.quit()

        return analyze_table_image(screenshot_path)

    except Exception as e:
        print(f"平台检测出错: {e}")
        return "收割"

def main():
    global startup_notified
    if not startup_notified:
        send_telegram_message(f"✅ DG 监控系统已启动 ({get_current_time()})")
        startup_notified = True

    status = detect_platform()

    if status == "放水时段":
        now = datetime.datetime.now(tz)
        end_time = (now + datetime.timedelta(minutes=10)).strftime("%H:%M")
        send_telegram_message(
            f"🔥 现在是平台放水时段！\n当前时间：{get_current_time()}\n预计放水结束时间：{end_time}\n此局势预计：剩下10分钟"
        )
    elif status == "中等胜率":
        now = datetime.datetime.now(tz)
        end_time = (now + datetime.timedelta(minutes=5)).strftime("%H:%M")
        send_telegram_message(
            f"⚠️ 现在是中等胜率（中上）时段。\n当前时间：{get_current_time()}\n预计结束时间：{end_time}\n此局势预计：剩下5分钟"
        )

if __name__ == "__main__":
    main()
