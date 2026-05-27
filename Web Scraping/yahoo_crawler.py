import requests
from bs4 import BeautifulSoup

# 1. 目標：Yahoo 股市 - 台積電(2330)的網址
url = "https://tw.stock.yahoo.com/quote/2330.TW"

# 2. 🔥 【超級偽裝術】 🔥
# 真實網站都有「反爬蟲機制」，如果發現你是 Python 程式，它會直接拒絕連線（噴 403 錯誤）。
# 所以我們必須加上 "Headers"，戴上密碼面具，假裝自己是一台標準的 Mac 電腦跟 Chrome 瀏覽器！
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

try:
    # 3. 把面具（headers）帶著，一起發送請求
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        print("🎉 成功攻破 Yahoo 股市伺服器！正在尋找台積電股價...")
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 4. 🥷 【精準暗殺定位】 🥷
        # 叫 BeautifulSoup 幫我們找：標籤是 "span"，且 class 身分證「包含」下面這串特徵的元件
        # (備註：Yahoo 的 class 很長，我們通常只要抓前面最關鍵的特徵，例如 Fz(32px) 代表字體32像素)
        price_tag = soup.find("span", class_="Fz(32px)")
        
        if price_tag:
            # 5. 用你最會的「的.text」剥殼，拿走純文字！
            real_price = price_tag.text
            print(f"📈 【台積電 2330】目前的即時股價是:  ${real_price} 元")
        else:
            print("❌ 慘了！Yahoo 可能改版了，找不到對應的 class 身分證！")
            
    else:
        print(f"⚠️ 被伺服器攔截拒絕了！錯誤代碼: {response.status_code}")

except Exception as e:
    print(f"🚨 發生網路斷線災難: {e}")