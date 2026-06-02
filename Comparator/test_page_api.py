import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

headers = {"User-Agent": "Mozilla/5.0"}

# 🎯 實驗一：試試看 B=1 (第 1 頁)
url_page1 = "https://www.moneydj.com/funddj/djjson/YFundSearchJSON.djjson?q=安聯&B=1"
res1 = requests.get(url_page1, headers=headers, verify=False)

# 🎯 實驗二：試試看 B=2 (第 2 頁)
url_page2 = "https://www.moneydj.com/funddj/djjson/YFundSearchJSON.djjson?q=安聯&B=2"
res2 = requests.get(url_page2, headers=headers, verify=False)

print("================== 【 第 1 頁 (B=1) 的前 150 個字 】 ==================")
print(res1.text[:150])

print("\n================== 【 第 2 頁 (B=2) 的前 150 個字 】 ==================")
print(res2.text[:150])