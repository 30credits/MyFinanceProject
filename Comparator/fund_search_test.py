import requests
import urllib3

# 讓跳過安全檢查的警告文字閉嘴
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 🎯 拿你剛剛抓到的網址來當實驗對象
# 我們先用中文關鍵字「安聯」來丟過去看看
keyword = "安聯"
url = f"https://www.moneydj.com/funddj/djjson/YFundSearchJSON.djjson?q={keyword}"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

print(f"🕵️‍♂️ 正在發動測試，使用 Will 抓到的新密道搜尋：[{keyword}]...")
response = requests.get(url, headers=headers, verify=False)

if response.status_code == 200:
    print("✅ 成功連上新水管！")
    print("================== 【 照妖鏡：新 API 吐出來的原始資料 】 ==================")
    
    # 叫 Python 把後台噴出來的文字直接印出來
    print(response.text)
    
    print("======================================================================")
else:
    print(f"❌ 連線失敗，伺服器回應代碼: {response.status_code}")