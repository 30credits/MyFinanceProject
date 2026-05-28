import requests
from bs4 import BeautifulSoup
import time  # 引進時間守護者，負責讓程式「休息防當機」

# 1. 定義你想追蹤的股票清單（用字典順便存名字，方便對照）
stock_targets = {
    "2330": "台積電",
    "2317": "鴻 海",
    "2454": "聯發科",
    "2882": "國泰金"
}

# 2. 戴上萬用隱身斗篷（User-Agent）
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

print("🚀 【大數據股市追蹤器】啟動...")
print("----------------------------------------")

# 3. 發動解包迴圈，一檔一檔自動點名抓取
for code, name in stock_targets.items():
    # 利用 f-string 動態組裝出每一檔股票的專屬網址
    url = f"https://tw.stock.yahoo.com/quote/{code}.TW"
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 精準暗殺定位：尋找 Yahoo 股價的特徵標籤
            price_tag = soup.find("span", class_="Fz(32px)")
            
            if price_tag:
                # 剥殼拿到乾淨的股價純文字
                current_price = price_tag.text
                print(f"📊  [{code}] {name}  ➔  目前的即時股價是: ${current_price} 元")
            else:
                print(f"❌  [{code}] {name}  ➔  找不到股價標籤，Yahoo 可能偷偷改版了！")
        else:
            print(f"⚠️  [{code}] {name}  ➔  連線失敗，錯誤代碼: {response.status_code}")
            
    except Exception as e:
        print(f"🚨  [{code}] {name}  ➔  發生靈異災難: {e}")
        
    # 🛑 【最重要的安全防線】 🛑
    # 每抓完一檔股票，強迫 Python 原地泡杯咖啡休息 2 秒鐘，絕對不對伺服器造成負擔
    print("⏳ 安全防禦：休息 2 秒鐘...")
    time.sleep(2)

print("----------------------------------------")
print("🏁 全數追蹤完畢！安全收工。")