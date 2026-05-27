import requests
from bs4 import BeautifulSoup

# 1. 定義我們要爬取的目標網址（這裡用一個簡單的測試網頁）
url = "https://example.com"

try:
    # 2. 讓 Python 偽裝成瀏覽器，發送網路請求
    response = requests.get(url)
    
    # 3. 如果網頁順利連上（狀態碼 200），就繼續往下
    if response.status_code == 200:
        print("🎉 成功連上網路！正在解析網頁...")
        
        # 4. 把搬回家的純文字原始碼，交給 BeautifulSoup 這位「網頁解構大師」
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 5. 精準挖寶：抓取網頁的大標題 <h1> 標籤
        title_tag = soup.find("h1")
        
        if title_tag:
            print(f"📌 抓到的網頁大標題是: {title_tag.text}")
        else:
            print("❌ 找不到 <h1> 標籤")
            
    else:
        print(f"⚠️ 連線失敗，錯誤代碼: {response.status_code}")

except Exception as e:
    print(f"🚨 發生靈異災難: {e}")