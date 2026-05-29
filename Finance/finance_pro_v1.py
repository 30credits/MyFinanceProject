import tkinter as tk
from tkinter import messagebox
import json
from datetime import datetime

FILE_NAME = "data_v2.json"

# --- 1. 資料存取邏輯 (Data Layer) ---
def load_data():
    try:
        with open(FILE_NAME, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {"balance": {"Cash": 0, "Bank": 0}, "history": []}

def save_data(data):
    with open(FILE_NAME, "w") as file:
        json.dump(data, file, indent=4)

# --- 2. 動作邏輯 (Business Logic) ---
def handle_submit():
    # 抓取視窗輸入的值
    amount_str = entry_amount.get()
    note_str = entry_note.get()
    acc_name = acc_var.get()

    try:
        amount = int(amount_str)
        # 更新記憶體中的資料
        data["balance"][acc_name] += amount
        
        # 紀錄時間與歷史
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log = {"date": now, "account": acc_name, "change": amount, "note": note_str}
        data["history"].append(log)
        
        # 存入硬碟 (JSON)
        save_data(data)
        
        # 更新畫面的數字標籤
        update_ui_labels()
        
        messagebox.showinfo("Success", f"Recorded ${amount} to {acc_name}")
        entry_amount.delete(0, tk.END)
        entry_note.delete(0, tk.END)

    except ValueError:
        messagebox.showerror("Error", "Please enter a valid number!")

def update_ui_labels():
    # 這個函數專門用來刷新畫面上的餘額文字
    label_cash_val.config(text=f"${data['balance']['Cash']}")
    label_bank_val.config(text=f"${data['balance']['Bank']}")

# --- 3. 介面佈局 (UI Layer) ---
data = load_data()
root = tk.Tk()
root.title("Will's Wealth Manager Pro")
root.geometry("400x400")
root.configure(bg="#f8f9fa") # 現代淺灰白背景

# 標題
tk.Label(root, text="FINANCE DASHBOARD", font=("Helvetica", 16, "bold"), bg="#f8f9fa", fg="#2c3e50").grid(row=0, column=0, columnspan=2, pady=20)

# 餘額顯示區 (使用 grid 分兩欄顯示)
tk.Label(root, text="Cash Balance:", bg="#f8f9fa").grid(row=1, column=0, sticky="e", padx=10)
label_cash_val = tk.Label(root, text="", font=("Arial", 12, "bold"), bg="#f8f9fa", fg="#27ae60")
label_cash_val.grid(row=1, column=1, sticky="w")

tk.Label(root, text="Bank Balance:", bg="#f8f9fa").grid(row=2, column=0, sticky="e", padx=10)
label_bank_val = tk.Label(root, text="", font=("Arial", 12, "bold"), bg="#f8f9fa", fg="#2980b9")
label_bank_val.grid(row=2, column=1, sticky="w")

# 初始化標籤文字
update_ui_labels()

# 分隔線感 (利用 pady 創造空間)
tk.Label(root, text="--- New Transaction ---", bg="#f8f9fa", fg="#95a5a6").grid(row=3, column=0, columnspan=2, pady=15)

# 輸入區
tk.Label(root, text="Select Account:", bg="#f8f9fa").grid(row=4, column=0, sticky="e", padx=10, pady=5)
acc_var = tk.StringVar(value="Cash")
acc_menu = tk.OptionMenu(root, acc_var, "Cash", "Bank")
acc_menu.grid(row=4, column=1, sticky="w")

tk.Label(root, text="Amount:", bg="#f8f9fa").grid(row=5, column=0, sticky="e", padx=10, pady=5)
entry_amount = tk.Entry(root, bd=1, relief="solid")
entry_amount.grid(row=5, column=1, sticky="w")

tk.Label(root, text="Note:", bg="#f8f9fa").grid(row=6, column=0, sticky="e", padx=10, pady=5)
entry_note = tk.Entry(root, bd=1, relief="solid")
entry_note.grid(row=6, column=1, sticky="w")

# 送出按鈕
btn_submit = tk.Button(root, text="CONFIRM & SAVE", command=handle_submit, bg="#2c3e50", fg="white", font=("Helvetica", 10, "bold"), padx=20)
btn_submit.grid(row=7, column=0, columnspan=2, pady=25)

root.mainloop()