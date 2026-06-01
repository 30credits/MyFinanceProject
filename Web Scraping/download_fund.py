import requests
import csv
import urllib3

# 強迫跳過安全檢查時的警告文字閉嘴
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = "https://www.moneydj.com/funddj/bcd/tBCDNavList.djbcd?a=ACCA98&B=2025-6-1&C=2026-6-1&D="

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

print("📥 開始向 Moneydj 秘密通道請求一整年的基金數據...")
response = requests.get(url, headers=headers, verify=False)

if response.status_code == 200:
    raw_data = response.text.strip()
    
    # 🛠️ 【全新加入：跨時空修補術】
    # 發現 Yahoo/Moneydj 工程師在日期尾巴漏了逗號，我們主動幫它補上！
    raw_data = raw_data.replace("20260529", "20260529,")
    
    print("✅ 成功攔截原始數據流！開始進行對稱攔腰切片...")
    all_elements = raw_data.split(",")
    
    # 2. 🧮 算出這條龍總共有幾個東西（例如 480 個）
    total_count = len(all_elements)
    
    # 3. 🎯 找到正中間的黃金分水嶺（總數除以 2，例如 240）
    half_index = total_count // 2
    
    # 4. 🚀 降維打擊：利用 Python 的切片功能，直接分成左右兩半！
    date_list = all_elements[:half_index]  # 從頭到中間 ➔ 全日期
    value_list = all_elements[half_index:] # 從中間到尾巴 ➔ 全數字
    
    # 5. 🎬 開始寫入 CSV 檔案
    file_name = "fund_history.csv"
    with open(file_name, mode="w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(["序號", "淨值日期", "基金淨值"])
        
        counter = 0
        # 運用 zip() 讓左半邊的日期與右半邊的數字，一對一拉鏈扣合！
        for date_str, value_str in zip(date_list, value_list):
            date_str = date_str.strip()
            value_str = value_str.strip()
            
            if date_str and value_str:
                counter += 1
                # 把 20250602 格式化成漂亮的 2025/06/02
                formatted_date = f"{date_str[0:4]}/{date_str[4:6]}/{date_str[6:8]}"
                writer.writerow([counter, formatted_date, f"${value_str} 元"])
                
    print(f"🎉【大功告成】已成功將一整年共 {counter} 天的歷史淨值對齊，安全存入 '{file_name}' 檔案中！")
else:
    print(f"❌ 請求失敗，伺服器回應代碼: {response.status_code}")