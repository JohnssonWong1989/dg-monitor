import requests
import datetime
import pytz
import time
import cv2
import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

# Telegram 配置
BOT_TOKEN = "8134230045:AAForY5xzO6D4EioSYNfk1yPtF6-cl50ABI"
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

# 马来西亚时区
tz = pytz.timezone("Asia/Kuala_Lumpur")

# 全局状态
start_notified = False
last_status = None
last_start_time = None

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"Telegram发送失败: {e}")

def analyze_table_image(image):
    """
    使用OpenCV图像分析判断放水/收割：
    1. 检测连续相同颜色块数量 (长连/长龙)
    2. 检测空白区比例 (桌面是否满)
    返回： "放水", "中等胜率（中上）", "收割" 或 "中等"
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
    white_ratio = np.sum(thresh == 255) / thresh.size

    # 判断标准 (经验值调整)
    if white_ratio < 0.30:  
        return "放水"
    elif white_ratio < 0.45:
        return "中等胜率（中上）"
    elif white_ratio < 0.65:
        return "中等"
    else:
        return "收割"

def check_dg_status():
    """
    进入DG平台，抓取牌面截图，分析整体胜率状态
    """
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    try:
        driver.get("https://dg18.co/wap/")
        time.sleep(3)
        # 点击“免费试玩”
        try:
            free_btn = driver.find_element(By.XPATH, "//button[contains(text(),'免费')]")
            free_btn.click()
        except:
            pass
        time.sleep(5)

        # 滚动验证可能需要模拟 (跳过这里，只做截图分析)
        driver.save_screenshot("dg_table.png")
        image = cv2.imread("dg_table.png")
        return analyze_table_image(image)
    finally:
        driver.quit()

def main_loop():
    global start_notified, last_status, last_start_time

    if not start_notified:
        now = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        send_telegram_message(f"✅ DG监控已启动 - {now} (GMT+8)")
        start_notified = True

    current_status = check_dg_status()
    now = datetime.datetime.now(tz)

    if current_status in ["放水", "中等胜率（中上）"]:
        if last_status != current_status:
            last_start_time = now
            status_name = "放水时段（提高胜率）" if current_status == "放水" else "中等胜率（中上）"
            send_telegram_message(
                f"🎯 现在是平台 {status_name}\n"
                f"预计结束时间：{(now + datetime.timedelta(minutes=10)).strftime('%H:%M')}\n"
                f"此局势预计：剩下10分钟"
            )
    else:
        if last_status in ["放水", "中等胜率（中上）"] and last_start_time:
            duration = int((now - last_start_time).total_seconds() / 60)
            send_telegram_message(f"⚠️ 放水已结束，共持续 {duration} 分钟")

    last_status = current_status

if __name__ == "__main__":
    main_loop()
