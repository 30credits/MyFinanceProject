# 設定存檔的檔名
FILE_NAME = "balance.txt"

print("--- Data Persistence Tool ---")

# 1. 嘗試讀取舊有的資料 (Read)
try:
    with open(FILE_NAME, "r") as file:
        current_balance = int(file.read())
        print(f"Welcome back! Your last saved balance is: {current_balance}")
except FileNotFoundError:
    # 如果是第一次執行，還沒有檔案，就設定初始值為 0
    current_balance = 0
    print("No previous record found. Starting at 0.")

# 2. 進行計算邏輯
while True:
    user_input = input("Enter new income/expense (or type 'save' to finish): ")

    if user_input.lower() == 'save':
        # 3. 儲存並離開 (Write)
        with open(FILE_NAME, "w") as file:
            file.write(str(current_balance))
        print(f"Data saved to {FILE_NAME}. Goodbye!")
        break

    if user_input.lstrip('-').isdigit(): # lstrip('-') 讓程式也看得懂負數
        amount = int(user_input)
        current_balance += amount
        print(f"Current Balance: {current_balance}")
    else:
        print("Invalid input. Please enter a number.")