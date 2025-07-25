import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import pytz

# Telegram 配置
BOT_TOKEN = "8134230045:AAForY5xzO6D4EioSYNfk1yPtF6-cl50ABI"
CHAT_ID = "485427847"

# DG 平台免费试玩链接
DG_URL = "https://dg18.co/wap/"

# 马来西亚时区
tz = pytz.timezone("Asia/Kuala_Lumpur")

def send_telegram_message(message: str):
    """发送 Telegram 通知"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"发送 Telegram 消息失败: {e}")

def fetch_dg_page():
    """获取 DG 页面 HTML"""
    try:
        response = requests.get(DG_URL, timeout=10)
        response.encoding = 'utf-8'
        if response.status_code == 200:
            return response.text
        else:
            print(f"获取 DG 页面失败: 状态码 {response.status_code}")
            return None
    except Exception as e:
        print(f"请求 DG 出错: {e}")
        return None

def analyze_tables(html: str):
    """分析 DG 页面牌桌走势"""
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("div")
    total_tables = len(tables)

    # 模拟检测：统计含有“连”、“长龙”等关键词的桌子
    long_count = sum(1 for t in tables if "连" in t.get_text() or "龙" in t.get_text())
    if total_tables == 0:
        return "收割时段"

    ratio = (long_count / total_tables) * 100
    if ratio >= 70:
        return "放水时段"
    elif 55 <= ratio < 70:
        return "中等胜率（中上）"
    else:
        return "收割时段"

def estimate_end_time():
    """估计放水结束时间"""
    current_time = datetime.now(tz)
    end_time = current_time + timedelta(minutes=10)
    return end_time.strftime("%I:%M%p"), "剩下10分钟"

def main():
    current_time = datetime.now(tz).strftime("%Y-%m-%d %I:%M:%S %p")
    html = fetch_dg_page()
    if not html:
        return

    status = analyze_tables(html)

    if status == "放水时段":
        end_time, remain = estimate_end_time()
        send_telegram_message(
            f"🔥 现在是平台【放水时段】（胜率高）！\n"
            f"预计放水结束时间：{end_time}\n"
            f"此局势预计：{remain}\n"
            f"检测时间：{current_time}"
        )
    elif status == "中等胜率（中上）":
        end_time, remain = estimate_end_time()
        send_telegram_message(
            f"⚡ 平台【中等胜率（中上）】\n"
            f"预计结束时间：{end_time}\n"
            f"此局势预计：{remain}\n"
            f"检测时间：{current_time}"
        )
    else:
        print(f"{current_time} - 当前为收割时段，不提醒")

if __name__ == "__main__":
    main()
