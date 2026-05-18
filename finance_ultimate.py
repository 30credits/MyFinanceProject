import tkinter as tk
from tkinter import ttk, messagebox
import json
from datetime import datetime
import os
import sys

# =====================================================================
# 0. 系統環境設定 (系統安全鎖，確保資料夾不迷路)
# =====================================================================
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable) # 執行 .exe 時的資料夾
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # 在 VS Code 開發時的資料夾

FILE_NAME = os.path.join(BASE_DIR, "data_v2.json")

# =====================================================================
# 1. 資料處理層 (Data Layer)
# =====================================================================
def load_data():
    try:
        with open(FILE_NAME, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        # 如果找不到檔案，自動建立一個標準的初始資料結構
        initial_data = {"balance": {"Cash": 0, "Bank": 0}, "history": []}
        with open(FILE_NAME, "w", encoding="utf-8") as file:
            json.dump(initial_data, file, indent=4, ensure_ascii=False)
        return initial_data

def save_data(data):
    with open(FILE_NAME, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

# 初始化載入資料
data = load_data()

# =====================================================================
# 2. 核心動作邏輯層 (Business Logic)
# =====================================================================
def handle_submit():
    amount_str = entry_amount.get()
    note_str = entry_note.get()
    acc_name = acc_var.get()

    try:
        amount = int(amount_str)
        # 1. 更新資料庫餘額
        data["balance"][acc_name] += amount
        
        # 2. 建立時間戳記與紀錄
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log = {"date": now, "account": acc_name, "change": amount, "note": note_str}
        data["history"].append(log)
        
        # 3. 存入 JSON 檔案
        save_data(data)
        
        # 4. 即時更新分頁一的餘額標籤
        update_balance_labels()
        
        messagebox.showinfo("成功", f"已成功記錄 {acc_name}: ${amount}")
        
        # 5. 清空輸入框
        entry_amount.delete(0, tk.END)
        entry_note.delete(0, tk.END)
        
    except ValueError:
        messagebox.showerror("錯誤", "金額請輸入正確的整數數字！")

def update_balance_labels():
    # 刷新分頁一上方的餘額顯示
    label_cash_val.config(text=f"${data['balance']['Cash']}")
    label_bank_val.config(text=f"${data['balance']['Bank']}")

def refresh_history_tree():
    global data
    data = load_data() # 強制從硬碟同步最新資料
    
    # 清空表格舊資料
    for item in tree.get_children():
        tree.delete(item)
        
    # 將資料逐筆插入 Excel 表格中
    for log in reversed(data["history"][-20:]): # 顯示最近 20 筆紀錄
        # 幫正數加上 "+" 號，讓記帳報表更直覺
        if log['change'] > 0:
            change_str = f"+${log['change']}"
        else:
            change_str = f"${log['change']}" # 負數自帶 "-" 號
            
        tree.insert("", tk.END, values=(log['date'], log['account'], change_str, log['note']))

# =====================================================================
# 3. 視覺介面層 (UI Layer)
# =====================================================================
root = tk.Tk()
root.title("Will's Wealth Manager Pro v3.0")
root.geometry("520x580") # 調整寬度與高度以完美容納表格
root.configure(bg="#f8f9fa")

# 建立分頁控制器
notebook = ttk.Notebook(root)
notebook.pack(pady=10, expand=True, fill="both")

tab1 = ttk.Frame(notebook)
tab2 = ttk.Frame(notebook)

notebook.add(tab1, text="  資產記帳錄入  ")
notebook.add(tab2, text="  歷史明細報表  ")

# --- 【分頁一：記帳主介面】 ---
tk.Label(tab1, text="FINANCE DASHBOARD", font=("Helvetica", 16, "bold"), fg="#2c3e50").grid(row=0, column=0, columnspan=2, pady=20)

# 餘額展示
tk.Label(tab1, text="現金目前餘額 (Cash):", font=("Arial", 10)).grid(row=1, column=0, sticky="e", padx=15, pady=5)
label_cash_val = tk.Label(tab1, text="", font=("Arial", 12, "bold"), fg="#27ae60")
label_cash_val.grid(row=1, column=1, sticky="w", padx=5)

tk.Label(tab1, text="銀行目前餘額 (Bank):", font=("Arial", 10)).grid(row=2, column=0, sticky="e", padx=15, pady=5)
label_bank_val = tk.Label(tab1, text="", font=("Arial", 12, "bold"), fg="#2980b9")
label_bank_val.grid(row=2, column=1, sticky="w", padx=5)

# 初始化餘額標籤文字
update_balance_labels()

tk.Label(tab1, text=" 記 錄 新 交 易 ", fg="#95a5a6").grid(row=3, column=0, columnspan=2, pady=20)

# 下拉選單
tk.Label(tab1, text="選擇帳戶:", font=("Arial", 10)).grid(row=4, column=0, sticky="e", padx=15, pady=8)
acc_var = tk.StringVar(value="Cash")
acc_menu = tk.OptionMenu(tab1, acc_var, "Cash", "Bank")
acc_menu.grid(row=4, column=1, sticky="w", padx=5)

# 金額輸入
tk.Label(tab1, text="交易金額:", font=("Arial", 10)).grid(row=5, column=0, sticky="e", padx=15, pady=8)
entry_amount = tk.Entry(tab1, font=("Arial", 10), bd=1, relief="solid", width=22)
entry_amount.grid(row=5, column=1, sticky="w", padx=5)

# 備註輸入
tk.Label(tab1, text="備註說明:", font=("Arial", 10)).grid(row=6, column=0, sticky="e", padx=15, pady=8)
entry_note = tk.Entry(tab1, font=("Arial", 10), bd=1, relief="solid", width=22)
entry_note.grid(row=6, column=1, sticky="w", padx=5)

# 送出按鈕
btn_submit = tk.Button(tab1, text="確認送出並儲存", command=handle_submit, bg="#2c3e50", fg="white", font=("Helvetica", 10, "bold"), width=22, pady=5)
btn_submit.grid(row=7, column=0, columnspan=2, pady=25)


# --- 【分頁二：Excel 級歷史報表介面】 ---
tk.Label(tab2, text="歷史交易明細表", font=("Arial", 14, "bold"), fg="#2c3e50").pack(pady=15)

# Treeview 表格設定
columns = ("date", "account", "change", "note")
tree = ttk.Treeview(tab2, columns=columns, show="headings", height=16)

# 定義欄位標題與財務專業對齊
tree.heading("date", text="交易時間")
tree.column("date", width=140, anchor="center")

tree.heading("account", text="帳戶")
tree.column("account", width=70, anchor="center")

tree.heading("change", text="金額變動")
tree.column("change", width=90, anchor="e") # 金額靠右對齊，方便對齊位數

tree.heading("note", text="備註說明")
tree.column("note", width=160, anchor="w")     # 文字靠左對齊

tree.pack(padx=15, pady=5, fill="both", expand=True)

# 手動刷新按鈕
btn_refresh = tk.Button(tab2, text="手動刷新報表", command=refresh_history_tree, font=("Arial", 9))
btn_refresh.pack(pady=10)


# =====================================================================
# 4. 自動化事件綁定與啟動
# =====================================================================
def on_tab_change(event):
    # 當使用者切換到第二個分頁 (歷史紀錄) 時，自動觸發刷新，不需手動按按鈕
    if notebook.index("current") == 1: 
        refresh_history_tree()

notebook.bind("<<NotebookTabChanged>>", on_tab_change)

root.mainloop()