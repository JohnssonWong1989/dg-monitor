import requests
import cv2
import numpy as np
import time
from datetime import datetime, timedelta
import pytz
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Telegram config
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


# 时区转换为 GMT+8（马来西亚）
tz = pytz.timezone("Asia/Kuala_Lumpur")
current_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=payload)

# 首次启动提醒（只运行一次）
with open("startup_flag.txt", "a+") as f:
    f.seek(0)
    if not f.read():
        send_telegram(f"✅ [系统启动成功] DG监控系统已启动（马来西亚时间：{current_time}）")
        f.write("started")

# 设定放水结构判断标准（图像匹配）
def is_fangshui(table_img):
    hsv = cv2.cvtColor(table_img, cv2.COLOR_BGR2HSV)
    blue_mask = cv2.inRange(hsv, (100, 50, 50), (130, 255, 255))
    red_mask = cv2.inRange(hsv, (0, 50, 50), (10, 255, 255))
    total = cv2.countNonZero(blue_mask) + cv2.countNonZero(red_mask)
    return total > 1000  # 判断为“长龙”结构阈值（可调）

# 实际执行分析流程
def run_monitor():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get("https://dg18.co/wap/")
        wait = WebDriverWait(driver, 15)

        # 点击“免费试玩”
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), '免费试玩') or contains(text(), 'Free')]"))).click()

        # 滚动验证
        time.sleep(5)
        driver.switch_to.frame(driver.find_element(By.TAG_NAME, "iframe"))
        slider = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "secsdk-captcha-drag-icon")))
        action = ActionChains(driver)
        action.click_and_hold(slider).move_by_offset(300, 0).release().perform()

        time.sleep(8)
        driver.switch_to.default_content()
        time.sleep(6)

        # 截取所有桌面（模拟）
        driver.save_screenshot("full_screen.png")
        img = cv2.imread("full_screen.png")

        # 模拟分割多个桌子图片区域
        table_imgs = [img[100:300, 100:400], img[300:500, 100:400], img[500:700, 100:400],
                      img[100:300, 500:800], img[300:500, 500:800], img[500:700, 500:800]]

        match_count = sum(is_fangshui(table) for table in table_imgs)
        match_ratio = match_count / len(table_imgs)

        now = datetime.now(tz)
        ending_time = now + timedelta(minutes=10)
        remaining = (ending_time - now).seconds // 60

        if match_ratio >= 0.70:
            send_telegram(
                f"🔥 [放水时段] 目前符合放水结构\n马来西亚时间：{now.strftime('%H:%M:%S')}\n预计结束时间：{ending_time.strftime('%H:%M')}\n此局势预计：剩下 {remaining} 分钟")
        elif 0.55 <= match_ratio < 0.70:
            send_telegram(
                f"⚠️ [中等胜率（中上）] 目前接近放水结构\n马来西亚时间：{now.strftime('%H:%M:%S')}\n预计结束时间：{ending_time.strftime('%H:%M')}\n此局势预计：剩下 {remaining} 分钟")
        else:
            pass  # 胜率中等或收割时段，不提醒

    except Exception as e:
        send_telegram(f"❌ 系统运行出错：{str(e)}")
    finally:
        driver.quit()

run_monitor()
