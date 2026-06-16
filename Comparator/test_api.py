import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 拿一檔確定存在的基金代碼測試
test_url = "https://www.moneydj.com/funddj/bcd/tBCDNavList.djbcd?a=ACNC18&B=2025-6-2&C=2026-6-2&D="
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

try:
    print("📡 正在發送特種連線測試...")
    res = requests.get(test_url, headers=headers, verify=False, timeout=10)
    print(f"狀態碼 (Status Code): {res.status_code}")
    print("內部前 200 個字元內容：")
    print(res.text[:200]) # 印出前200個字看有沒有抓到真貨
except Exception as e:
    print(f"💥 連線當場崩潰，原因: {e}")