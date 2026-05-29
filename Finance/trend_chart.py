import json
import matplotlib.pyplot as plt
from datetime import datetime

# 1. 讀取 v2 資料
try:
    with open("data_v2.json", "r") as file:
        data = json.load(file)
except FileNotFoundError:
    print("Please run finance_with_time.py first to generate some data!")
    exit()

# 2. 處理歷史紀錄
history = data["history"]

# 我們需要兩個清單：一個存時間，一個存當時的總餘額
dates = []
balances = []
current_total = 0

# 假設初始金額（這部分可以根據需求調整，這裡我們先從歷史紀錄的第一筆開始累加）
for record in history:
    # 把字串轉回 Python 的時間物件，這樣繪圖工具才認得先後順序
    date_obj = datetime.strptime(record["date"], "%Y-%m-%d %H:%M:%S")
    dates.append(date_obj)
    
    current_total += record["change"]
    balances.append(current_total)

# 3. 開始繪圖
plt.figure(figsize=(10, 5))
plt.plot(dates, balances, marker='o', linestyle='-', color='b') # b 代表藍色，o 代表有點點

# 4. 美化圖表
plt.title("My Wealth Growth Trend")
plt.xlabel("Date and Time")
plt.ylabel("Total Balance ($)")
plt.grid(True) # 加入格線，比較好讀

# 自動旋轉日期標籤，避免疊在一起
plt.gcf().autofmt_xdate()

plt.show()