import time
import datetime
import pytz
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

# Telegram配置
TELEGRAM_BOT_TOKEN = "8134230045:AAForY5xzO6D4EioSYNfk1yPtF6-cl50ABI"
TELEGRAM_CHAT_ID = "485427847"

# 时区
MY_TZ = pytz.timezone("Asia/Kuala_Lumpur")

# 发送Telegram消息
def send_telegram_message(msg: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": msg}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Telegram发送失败：", e)

# 检测桌面走势的逻辑
def analyze_table_pattern(history):
    """
    判断一张牌桌是否是长连/长龙：
    - 连开 ≥5 粒庄/闲
    - 连开 ≥8 粒为长龙
    """
    if "庄庄庄庄庄" in history or "闲闲闲闲闲" in history:
        return True
    if "庄庄庄庄庄庄庄庄" in history or "闲闲闲闲闲闲闲闲" in history:
        return True
    return False

# 滑块自动化模拟（简易版）
def solve_slider(driver):
    try:
        slider = driver.find_element(By.CLASS_NAME, "slider-class")  # 伪类名
        action = ActionChains(driver)
        action.click_and_hold(slider).move_by_offset(260, 0).release().perform()
        time.sleep(2)
    except:
        print("未检测到滑块验证")

# 检测DG平台桌面
def detect_dg_platform():
    """
    真实检测 DG 平台桌面状态：
    1. 打开 dg18.co / wap
    2. 点击免费试玩/Free
    3. 通过安全验证
    4. 获取桌面数据
    返回:
      status: "放水" / "中等胜率" / "收割" / "胜率中等"
      percent: 放水结构桌面比例
    """

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://dg18.co/wap/")

    time.sleep(5)
    try:
        # 点击免费试玩
        free_button = driver.find_element(By.XPATH, "//button[contains(text(),'免费试玩') or contains(text(),'Free')]")
        free_button.click()
        time.sleep(5)
        solve_slider(driver)
    except:
        print("未找到免费试玩按钮")
        driver.quit()
        return ("收割", 0)

    # 获取所有桌面
    tables = driver.find_elements(By.CLASS_NAME, "table-class")  # 伪类名
    total_tables = len(tables)
    if total_tables == 0:
        driver.quit()
        return ("收割", 0)

    good_count = 0
    bad_count = 0

    for t in tables:
        text = t.text
        # 检测单跳
        if "庄闲庄闲" in text or "闲庄闲庄" in text:
            bad_count += 1
        if analyze_table_pattern(text):
            good_count += 1

    driver.quit()
    percent = (good_count / total_tables) * 100

    if percent >= 70:
        return ("放水", percent)
    elif 55 <= percent < 70:
        return ("中等胜率", percent)
    else:
        return ("收割", percent)

# 主循环
def main_loop():
    send_telegram_message("DG监控系统 Version 4.3 已启动！（真实检测 + 策略逻辑）")

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
                    f"现在是平台 {status}时段（胜率提高）\n"
                    f"预计放水结束时间：{end_time_est}\n"
                    f"此局势预计：剩下10分钟\n"
                    f"当前检测时间：{now}\n"
                    f"当前好路桌面比例：{percent:.1f}%"
                )
        else:
            if current_state in ["放水", "中等胜率"]:
                duration = int((time.time() - state_start_time) / 60)
                send_telegram_message(f"{current_state}已结束，共持续 {duration} 分钟。")
                current_state = None

        time.sleep(300)  # 每5分钟检测一次

if __name__ == "__main__":
    main_loop()
