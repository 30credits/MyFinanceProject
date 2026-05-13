print("--- Professional Finance Tool ---")

# 使用 while True 建立一個「無限循環」，直到我們主動說停止
while True:
    bank_input = input("Enter bank balance (or type 'exit' to quit): ")

    # 1. 先檢查使用者是不是想結束程式
    if bank_input.lower() == 'exit':
        print("Exiting... Goodbye!")
        break  # 跳出迴圈，結束程式

    # 2. 檢查輸入的是不是數字
    if bank_input.isdigit():
        balance = int(bank_input)
        print(f"Recorded! Your balance is: {balance}")
        
        # 這裡可以加入你之前的判斷邏輯
        if balance > 1000000:
            print("Status: Millionaire!")
        
        # 成功處理完一筆，我們可以問下一筆，或者也可以在這裡用 break 結束
        # 為了讓你練習，我們讓它繼續跑，直到你輸入 exit
        print("---------------------------------")
        
    else:
        # 如果輸入錯誤，不使用 break，它就會回到迴圈開頭重新要求輸入
        print("Invalid input! Please enter numbers only.")
        print("Try again...")