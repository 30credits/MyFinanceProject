import json
from datetime import datetime # 引入時間模組

FILE_NAME = "data_v2.json"

# 1. 讀取或初始化資料
try:
    with open(FILE_NAME, "r") as file:
        data = json.load(file)
except FileNotFoundError:
    data = {
        "balance": {"Cash": 0, "Bank": 0},
        "history": []
    }

# 2. 取得輸入
print(f"Current Cash: ${data['balance']['Cash']}")
acc_name = input("Which account to update? (Cash/Bank): ").capitalize()
amount = int(input("Enter amount: "))
note = input("What is this for? (e.g. Lunch, Salary): ")

# 3. 更新餘額
if acc_name in data["balance"]:
    data["balance"][acc_name] += amount
    
    # 4. 【核心重點】記錄時間與細節
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S") # 格式化時間
    log = {
        "date": now,
        "account": acc_name,
        "change": amount,
        "note": note
    }
    data["history"].append(log) # 把新紀錄推入歷史清單

    # 5. 儲存
    with open(FILE_NAME, "w") as file:
        json.dump(data, file, indent=4)
    print(f"Successfully recorded at {now}!")
else:
    print("Account not found.")