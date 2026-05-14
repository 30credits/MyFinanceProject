import tkinter as tk
from tkinter import messagebox
import json
from datetime import datetime

FILE_NAME = "data_v2.json"

# --- 1. 資料處理函數 ---
def load_data():
    try:
        with open(FILE_NAME, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {"balance": {"Cash": 0, "Bank": 0}, "history": []}

def save_data(data):
    with open(FILE_NAME, "w") as file:
        json.dump(data, file, indent=4)

# --- 2. 視窗按鈕邏輯 ---
def update_finance():
    amount_str = entry_amount.get()
    note_str = entry_note.get()
    acc_name = acc_var.get() # 取得下拉選單選中的帳戶

    try:
        amount = int(amount_str)
        # 更新資料
        data["balance"][acc_name] += amount
        
        # 紀錄歷史
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log = {"date": now, "account": acc_name, "change": amount, "note": note_str}
        data["history"].append(log)
        
        # 存檔
        save_data(data)
        
        # 更新介面
        label_cash.config(text=f"Cash: ${data['balance']['Cash']}")
        label_bank.config(text=f"Bank: ${data['balance']['Bank']}")
        messagebox.showinfo("Success", f"Recorded: {note_str} (${amount})")
        
        # 清空輸入
        entry_amount.delete(0, tk.END)
        entry_note.delete(0, tk.END)
        
    except ValueError:
        messagebox.showerror("Error", "Please enter a valid number for amount!")

# --- 3. 建立 UI 介面 ---
data = load_data()
root = tk.Tk()
root.title("Will's Finance Pro")
root.geometry("400x450")

# 顯示各帳戶餘額
label_cash = tk.Label(root, text=f"Cash: ${data['balance']['Cash']}", font=("Arial", 12), fg="blue")
label_cash.pack(pady=5)
label_bank = tk.Label(root, text=f"Bank: ${data['balance']['Bank']}", font=("Arial", 12), fg="blue")
label_bank.pack(pady=5)

# 下拉選單 (選擇帳戶)
tk.Label(root, text="Select Account:").pack(pady=5)
acc_var = tk.StringVar(value="Cash") # 預設選 Cash
acc_menu = tk.OptionMenu(root, acc_var, "Cash", "Bank")
acc_menu.pack()

# 輸入金額
tk.Label(root, text="Amount:").pack(pady=5)
entry_amount = tk.Entry(root)
entry_amount.pack()

# 輸入備註
tk.Label(root, text="Note:").pack(pady=5)
entry_note = tk.Entry(root)
entry_note.pack()

# 更新按鈕
btn_update = tk.Button(root, text="Submit Transaction", command=update_finance, bg="green", fg="white")
btn_update.pack(pady=20)

root.mainloop()