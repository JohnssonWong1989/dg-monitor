import time
import datetime
import pytz
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
import io
import cv2
import numpy as np

# ================================
# Telegram 配置
# ================================
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

# ================================
# 通知函数
# ================================
def send_telegram_message(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"Telegram 发送失败: {e}")

# ================================
# 时间函数（GMT+8）
# ================================
def get_current_time():
    tz = pytz.timezone("Asia/Kuala_Lumpur")
    return datetime.datetime.now(tz)

# ================================
# 检测桌面牌路核心逻辑
# ================================
def analyze_table_image(image):
    """
    分析牌路截图，识别放水/中等胜率
    """
    img_gray = cv2.cvtColor(np.array(image), cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(img_gray, 200, 255, cv2.THRESH_BINARY_INV)

    white_area = cv2.countNonZero(thresh)
    total_area = thresh.shape[0] * thresh.shape[1]
    ratio = white_area / total_area

    # 70% 以上为放水
    if ratio >= 0.7:
        return "放水时段（提高胜率）"
    elif 0.55 <= ratio < 0.7:
        return "中等胜率（中上）"
    else:
        return "收割/无放水"

# ================================
# 自动化流程：进入 DG 平台并截图
# ================================
def get_dg_screenshot():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)
    driver.get("https://dg18.co/wap/")

    try:
        # 等待 "免费试玩" 或 "Free" 按钮
        free_btn = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '免费试玩') or contains(text(), 'Free')]"))
        )
        free_btn.click()

        # 等待验证码 (假设有滚动验证)
        time.sleep(5)  # 这里可以加入验证码处理逻辑

        # 等待页面加载
        time.sleep(8)

        # 截图
        screenshot = driver.get_screenshot_as_png()
        driver.quit()
        return Image.open(io.BytesIO(screenshot))

    except Exception as e:
        print(f"DG 访问失败: {e}")
        driver.quit()
        return None

# ================================
# 主检测逻辑
# ================================
def monitor_loop():
    send_telegram_message("✅ DG 监控系统已启动 (V5.2) - 马来西亚 GMT+8 时间")

    current_status = None
    start_time = None

    while True:
        now = get_current_time()
        print(f"检测时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")

        screenshot = get_dg_screenshot()
        if screenshot is None:
            time.sleep(300)
            continue

        result = analyze_table_image(screenshot)
        print(f"检测结果: {result}")

        if result in ["放水时段（提高胜率）", "中等胜率（中上）"]:
            if current_status != result:
                # 计算预计结束时间（假设 20 分钟放水期）
                end_time = now + datetime.timedelta(minutes=20)
                duration = 20

                message = (
                    f"🔥【{result}】\n"
                    f"检测时间：{now.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"预计放水结束时间：{end_time.strftime('%H:%M')}\n"
                    f"此局势预计：剩下 {duration} 分钟"
                )
                send_telegram_message(message)
                current_status = result
                start_time = now
        else:
            if current_status is not None:
                elapsed = int((now - start_time).total_seconds() / 60)
                send_telegram_message(f"⚠️ 放水已结束，共持续 {elapsed} 分钟。")
                current_status = None
                start_time = None

        # 每 5 分钟检测一次
        time.sleep(300)

if __name__ == "__main__":
    monitor_loop()
