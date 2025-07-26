import time
import cv2
import numpy as np
import pytz
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Telegram 配置
TELEGRAM_TOKEN = "8134230045:AAForY5xzO6D4EioSYNfk1yPtF6-cl50ABI"
CHAT_ID = "485427847"

# ===================
# 检测规则参数
# ===================
CHECK_INTERVAL = 300  # 每 5 分钟检测一次
TIMEZONE_OFFSET = 8   # GMT+8 时区
MIN_LONG_DRAGON = 5   # 连续 5 粒以上算长龙
MIN_SUPER_DRAGON = 8  # 超级长龙
MIN_TABLE_FOR_FLOOD = 0.7  # 放水时段比例阈值 70%
MIN_TABLE_FOR_MEDIUM = 0.55 # 中等胜率中上阈值 55%

# 时区设置
MY_TZ = pytz.timezone("Asia/Kuala_Lumpur")

# 放水时段提醒状态
active_alert = False
alert_start_time = None

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"Telegram发送失败: {e}")

def get_current_time():
    return datetime.now(MY_TZ).strftime("%Y-%m-%d %H:%M:%S")

# 图像特征检测（放水、胜率中上、收割）
def analyze_table_image(image_path):
    img = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if img is None:
        return "unknown"

    # 转灰度
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
    white_pixel_ratio = np.sum(thresh == 255) / (thresh.size)

    # 基于白色像素比例粗略判定
    if white_pixel_ratio > 0.70:
        return "放水时段"
    elif 0.55 < white_pixel_ratio <= 0.69:
        return "中等胜率（中上）"
    elif 0.35 < white_pixel_ratio <= 0.55:
        return "胜率中等"
    else:
        return "收割时段"

# 自动访问 DG 平台并截图
def fetch_dg_screenshot():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)

    try:
        driver.get("https://dg18.co/wap/")
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.LINK_TEXT, "免费试玩"))).click()
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "canvas")))

        screenshot_path = "/tmp/dg_table.png"
        driver.save_screenshot(screenshot_path)
        driver.quit()
        return screenshot_path
    except Exception as e:
        driver.quit()
        print(f"DG截图失败: {e}")
        return None

def monitor_dg_tables():
    global active_alert, alert_start_time
    while True:
        print(f"[{get_current_time()}] 正在检测DG牌面...")
        screenshot = fetch_dg_screenshot()
        if screenshot:
            status = analyze_table_image(screenshot)
            print(f"识别结果：{status}")

            if status in ["放水时段", "中等胜率（中上）"]:
                if not active_alert:
                    active_alert = True
                    alert_start_time = time.time()
                    send_telegram_message(
                        f"🔥当前平台状态：{status}\n时间：{get_current_time()}\n预计放水结束时间：{(datetime.now(MY_TZ) + timedelta(minutes=10)).strftime('%H:%M')}\n此局势预计：剩下10分钟"
                    )
            else:
                if active_alert:
                    duration = int((time.time() - alert_start_time) / 60)
                    send_telegram_message(f"⚠️放水已结束，共持续 {duration} 分钟。")
                    active_alert = False

        time.sleep(300)  # 每5分钟检测一次

if __name__ == "__main__":
    send_telegram_message(f"✅检测系统已启动！时间：{get_current_time()}")
    monitor_dg_tables()
