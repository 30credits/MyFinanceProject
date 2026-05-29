import json  # 引入 Python 內建的 JSON 處理工具

FILE_NAME = "data.json"

# 1. 嘗試讀取 JSON 檔案
try:
    with open(FILE_NAME, "r") as file:
        accounts = json.load(file)  # 把 JSON 格式轉回 Python 字典
    print("--- Welcome Back! Current Data ---")
except FileNotFoundError:
    # 如果沒檔案，就建立一組初始資料
    accounts = {"Cash": 0, "Bank": 0}
    print("--- Initializing New Data ---")

# 2. 顯示帳戶狀況
for name, balance in accounts.items():
    print(f"{name}: ${balance}")

# 3. 簡單的修改邏輯
print("-" * 25)
target = input("Which account to update? (Cash/Bank):").strip().lower()
mapping = {k.lower(): k for k in accounts.keys()}
if target in mapping:
    original_key = mapping[target] # 抓回原始的大寫標籤
    amount = int(input(f"Updating {original_key}, enter amount: "))
    accounts[original_key] += amount
    
    # 4. 儲存成 JSON 檔案
    with open(FILE_NAME, "w") as file:
        json.dump(accounts, file, indent=4) # indent=4 讓存出來的檔案排版漂亮、好讀
    print("Update saved successfully!")
else:
    print("Account not found.")