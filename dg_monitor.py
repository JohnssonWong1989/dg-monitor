import requests
import time
import pytz
from datetime import datetime
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

# 检测标记
first_start = True
in_fangshui = False
fangshui_start_time = None

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print("Telegram发送失败：", e)

def get_current_time():
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

def analyze_tables(image):
    """
    用OpenCV分析桌面截图，判断是否放水时段或中等胜率（中上）。
    这里模拟逻辑：
    - 如果检测到“长连/长龙”数量超过阈值，返回 'fangshui'
    - 如果检测到中等数量长连，返回 'medium_high'
    - 否则返回 'normal'
    """
    # 真实检测需要基于图片颜色/连珠模式，这里假设分析逻辑
    # TODO: 在真实环境下替换此逻辑
    return np.random.choice(["fangshui", "medium_high", "normal"], p=[0.1, 0.2, 0.7])

def monitor_dg():
    global first_start, in_fangshui, fangshui_start_time

    if first_start:
        send_telegram_message(f"✅ DG监控已启动 ({get_current_time()})，开始每5分钟检测一次...")
        first_start = False

    # 使用 Selenium 进入 DG 平台
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(options=chrome_options)
        driver.get("https://dg18.co/wap/")

        time.sleep(5)  # 等待页面加载
        screenshot_path = "/tmp/dg_screen.png"
        driver.save_screenshot(screenshot_path)
        driver.quit()

        # OpenCV 检测
        img = cv2.imread(screenshot_path)
        status = analyze_tables(img)

        if status == "fangshui":
            if not in_fangshui:
                fangshui_start_time = datetime.now(tz)
                in_fangshui = True
                send_telegram_message(
                    f"🔥 [放水时段] 检测到DG平台胜率提高！\n"
                    f"当前时间：{get_current_time()}\n"
                    f"预计持续中，请立即关注入场机会。"
                )
        elif status == "medium_high":
            send_telegram_message(
                f"🔔 [中等胜率（中上）] 当前DG平台部分桌面有长连/多连迹象。\n"
                f"当前时间：{get_current_time()}"
            )
        else:
            if in_fangshui:
                duration = int((datetime.now(tz) - fangshui_start_time).total_seconds() / 60)
                send_telegram_message(
                    f"⚠️ 放水已结束，共持续 {duration} 分钟。\n"
                    f"当前时间：{get_current_time()}"
                )
                in_fangshui = False

    except Exception as e:
        send_telegram_message(f"❌ DG监控异常：{str(e)}")

def main_loop():
    while True:
        monitor_dg()
        time.sleep(300)  # 每5分钟检测一次

if __name__ == "__main__":
    main_loop()
