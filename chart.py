import matplotlib.pyplot as plt
import json

# 1. 讀取你存好的 JSON 資料
try:
    with open("data.json", "r") as file:
        accounts = json.load(file)
except FileNotFoundError:
    accounts = {"No Data": 1}

# 2. 準備繪圖需要的資料
names = list(accounts.keys())   # 帳戶名稱 (例如: Cash, Bank)
values = list(accounts.values()) # 帳戶金額 (例如: 1000, 50000)

# 3. 建立圓餅圖 (Pie Chart)
plt.figure(figsize=(8, 6)) # 設定圖表大小
plt.pie(values, labels=names, autopct='%1.1f%%', startangle=140)

# 4. 設定標題
plt.title("My Asset Allocation")

# 5. 顯示圖表
print("Generating chart... please wait.")
plt.show()