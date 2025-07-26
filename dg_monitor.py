import os
import time
import requests
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# ===================
# Telegram 配置
# ===================
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

# ===================
# 状态变量
# ===================
first_run = True
last_status = "unknown"  # 记录上次状态（防止重复提醒）
flood_start_time = None   # 放水时段开始时间


# ===================
# Telegram 发送函数
# ===================
def send_telegram_message(message: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"[ERROR] Telegram发送失败: {e}")


# ===================
# 模拟登录 DG 平台
# ===================
def init_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    return driver


# ===================
# 检测 DG 平台桌面状况
# ===================
def check_dg_platform():
    """
    返回值：'flood'（放水时段），'medium_high'（中等胜率中上），'bad'（收割或胜率中等）
    """
    driver = init_driver()
    try:
        driver.get("https://dg18.co/")
        time.sleep(2)

        # 点击“免费试玩”
        try:
            free_button = driver.find_element(By.XPATH, "//button[contains(text(),'免费试玩') or contains(text(),'Free')]")
            free_button.click()
            time.sleep(2)
        except:
            print("[WARN] 找不到 '免费试玩' 按钮。")

        # 滚动验证略过（假设自动通过）
        time.sleep(3)

        # 模拟读取桌面情况
        tables = driver.find_elements(By.CLASS_NAME, "table-class")  # 假设 class 为 table-class
        total_tables = len(tables)
        if total_tables == 0:
            return 'bad'

        # 分析“放水”桌面
        flood_like_tables = 0
        for t in tables:
            text = t.text
            # 简化规则：只要出现连续5+ 或8+ 的“庄”或“闲”
            if "庄庄庄庄庄" in text or "闲闲闲闲闲" in text:
                flood_like_tables += 1

        flood_ratio = flood_like_tables / total_tables
        print(f"[INFO] 检测桌面: {flood_like_tables}/{total_tables} 类似放水 ({flood_ratio:.2f})")

        if flood_ratio >= MIN_TABLE_FOR_FLOOD:
            return 'flood'
        elif flood_ratio >= MIN_TABLE_FOR_MEDIUM:
            return 'medium_high'
        else:
            return 'bad'

    except Exception as e:
        print(f"[ERROR] 检测DG平台失败: {e}")
        return 'bad'
    finally:
        driver.quit()


# ===================
# 计算当前时间
# ===================
def current_time():
    return datetime.utcnow() + timedelta(hours=TIMEZONE_OFFSET)


# ===================
# 主监控循环
# ===================
def monitor():
    global first_run, last_status, flood_start_time

    now = current_time()

    # 首次启动提醒
    if first_run:
        send_telegram_message("DG监控系统已启动 (GMT+8)")
        first_run = False

    # 检测平台
    status = check_dg_platform()

    if status == 'flood':
        if last_status != 'flood':
            flood_start_time = now
            send_telegram_message(
                f"【放水时段（提高胜率）】\n检测时间：{now.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"预计放水结束时间：{(now + timedelta(minutes=10)).strftime('%H:%M')}\n此局势预计：剩下10分钟"
            )
        last_status = 'flood'

    elif status == 'medium_high':
        if last_status != 'medium_high':
            send_telegram_message(
                f"【中等胜率（中上）】\n检测时间：{now.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"预计放水结束时间：{(now + timedelta(minutes=5)).strftime('%H:%M')}\n此局势预计：剩下5分钟"
            )
        last_status = 'medium_high'

    else:  # bad
        if last_status == 'flood' and flood_start_time:
            duration = (now - flood_start_time).seconds // 60
            send_telegram_message(f"放水已结束，共持续 {duration} 分钟。")
            flood_start_time = None
        last_status = 'bad'

if __name__ == "__main__":
    monitor()
