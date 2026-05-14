import tkinter as tk
from tkinter import messagebox

root = tk.Tk()
root.title("Finance Manager")
root.geometry("400x350")

# 1. 顯示餘額的標籤
balance = 5000
label_balance = tk.Label(root, text=f"Current Balance: ${balance}", font=("Arial", 14))
label_balance.pack(pady=20)

# 2. 提示文字
label_instruction = tk.Label(root, text="Enter amount to add/subtract:")
label_instruction.pack()

# 3. 【核心】輸入框元件
# 我們建立一個 Entry 物件，並把它放在 root 上
entry_amount = tk.Entry(root, font=("Arial", 12))
entry_amount.pack(pady=10)

# 4. 按鈕執行的邏輯
def update_finance():
    global balance # 告訴程式我們要修改外部的 balance 變數
    
    # 從輸入框抓取文字內容
    input_value = entry_amount.get()
    
    try:
        # 將文字轉為整數
        change = int(input_value)
        balance += change
        
        # 更新畫面的標籤內容
        label_balance.config(text=f"Current Balance: ${balance}", fg="green")
        
        # 清空輸入框，方便下次輸入
        entry_amount.delete(0, tk.END)
        
    except ValueError:
        # 如果使用者輸入的不是數字，彈出警告
        messagebox.showerror("Error", "Please enter a valid number!")

# 5. 更新按鈕
btn_update = tk.Button(root, text="Update Balance", command=update_finance)
btn_update.pack(pady=20)

root.mainloop()