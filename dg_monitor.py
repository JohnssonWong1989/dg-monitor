import time
import requests
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Telegram 配置
TELEGRAM_TOKEN = "8134230045:AAForY5xzO6D4EioSYNfk1yPtF6-cl50ABI"
TELEGRAM_CHAT_ID = "485427847"

# 全局状态
LAST_STATUS = None
START_TIME = None
FIRST_RUN = True

def send_telegram_message(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Telegram发送失败: {e}")

def enter_dg_platform():
    """ 打开 DG 平台并自动进入免费试玩页面 """
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    driver.get("https://dg18.co/wap/")
    time.sleep(3)

    try:
        btn = driver.find_element(By.XPATH, "//button[contains(text(), '免费试玩') or contains(text(), 'Free')]")
        btn.click()
        time.sleep(3)
    except:
        print("未找到【免费试玩】按钮")

    # 模拟滚动验证
    time.sleep(5)
    return driver

def analyze_tables(driver):
    """
    分析 DG 桌面，返回当前状态:
    - 放水时段（提高胜率）
    - 中等胜率（中上）
    - 收割时段
    """
    tables = driver.find_elements(By.CLASS_NAME, "road")
    if not tables:
        return "无数据", 0.0

    total_tables = len(tables)
    good_tables = 0
    long_dragon_tables = 0

    for t in tables:
        text = t.text
        if "庄庄庄庄" in text or "闲闲闲闲" in text:
            good_tables += 1
        if "庄庄庄庄庄庄庄庄" in text or "闲闲闲闲闲闲闲闲" in text:
            good_tables += 2
            long_dragon_tables += 1

    # 假信号过滤：如果只有1桌长龙且整体少于50%
    ratio = (good_tables / total_tables) * 100
    if long_dragon_tables == 1 and ratio < 55:
        return "收割时段", ratio

    if ratio >= 70:
        return "放水时段（提高胜率）", ratio
    elif 55 <= ratio < 70:
        return "中等胜率（中上）", ratio
    else:
        return "收割时段", ratio

def main():
    global LAST_STATUS, START_TIME, FIRST_RUN
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] 开始检测...")

    driver = enter_dg_platform()
    status, ratio = analyze_tables(driver)
    driver.quit()

    if FIRST_RUN:
        send_telegram_message(f"✅ DG监控已启动 (GMT+8) - 当前时间：{now}")
        FIRST_RUN = False

    if status in ["放水时段（提高胜率）", "中等胜率（中上）"]:
        if status != LAST_STATUS:
            START_TIME = datetime.now()
            end_time = START_TIME + timedelta(minutes=10)
            send_telegram_message(
                f"🔥 现在是平台【{status}】\n预计放水结束时间：{end_time.strftime('%H:%M')}\n此局势预计：剩下10分钟"
            )
        LAST_STATUS = status
    else:
        if LAST_STATUS in ["放水时段（提高胜率）", "中等胜率（中上）"]:
            duration = (datetime.now() - START_TIME).seconds // 60
            send_telegram_message(f"⚠ 放水已结束，共持续 {duration} 分钟")
        LAST_STATUS = status

if __name__ == "__main__":
    main()
