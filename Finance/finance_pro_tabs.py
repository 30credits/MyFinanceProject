import tkinter as tk
from tkinter import ttk, messagebox
import json
from datetime import datetime
import os
import sys

# --- 【核心升級：萬用絕對路徑導航】 ---
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FILE_NAME = os.path.join(BASE_DIR, "data_v2.json")

# 可以在終端機印出來給自己看，確認檔案被鎖在哪裡
print(f"【系統提示】資料庫已鎖定在：{FILE_NAME}")


# --- 1. 資料處理 (Data Layer) ---
def load_data():
    try:
        with open(FILE_NAME, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        # 如果檔案不存在，直接在程式旁邊建一個乾淨的
        initial_data = {"balance": {"Cash": 0, "Bank": 0}, "history": []}
        with open(FILE_NAME, "w", encoding="utf-8") as file:
            json.dump(initial_data, file, indent=4)
        return initial_data

def save_data(data):
    with open(FILE_NAME, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


# --- 2. 動作邏輯 (Business Logic) ---
data = load_data()

def handle_submit():
    amount_str = entry_amount.get()
    note_str = entry_note.get()
    acc_name = acc_var.get()

    try:
        amount = int(amount_str)
        data["balance"][acc_name] += amount
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log = {"date": now, "account": acc_name, "change": amount, "note": note_str}
        data["history"].append(log)
        
        save_data(data)
        
        messagebox.showinfo("成功", f"已記錄 {acc_name}: ${amount}")
        
        entry_amount.delete(0, tk.END)
        entry_note.delete(0, tk.END)
        
    except ValueError:
        messagebox.showerror("錯誤", "請輸入正確數字")

def refresh_history():
    global data
    data = load_data() 
    history_text.delete("1.0", tk.END)
    for log in reversed(data["history"][-15:]): 
        line = f"{log['date']} | {log['account']} | {log['change']} | {log['note']}\n"
        history_text.insert(tk.END, line)


# --- 3. UI 介面 (UI Layer) ---
root = tk.Tk()
root.title("Will's Finance Pro v2.1 (Stable)")
root.geometry("500x550")

notebook = ttk.Notebook(root)
notebook.pack(pady=10, expand=True, fill="both")

tab1 = ttk.Frame(notebook)
tab2 = ttk.Frame(notebook)

notebook.add(tab1, text="  記帳錄入  ")
notebook.add(tab2, text="  歷史紀錄  ")

# --- 分頁一內容 ---
tk.Label(tab1, text="新增交易", font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=2, pady=20)

tk.Label(tab1, text="選擇帳戶:").grid(row=1, column=0, sticky="e", padx=10, pady=10)
acc_var = tk.StringVar(value="Cash")
acc_menu = tk.OptionMenu(tab1, acc_var, "Cash", "Bank")
acc_menu.grid(row=1, column=1, sticky="w")

tk.Label(tab1, text="金額:").grid(row=2, column=0, sticky="e", padx=10, pady=10)
entry_amount = tk.Entry(tab1)
entry_amount.grid(row=2, column=1, sticky="w")

tk.Label(tab1, text="備註:").grid(row=3, column=0, sticky="e", padx=10, pady=10)
entry_note = tk.Entry(tab1)
entry_note.grid(row=3, column=1, sticky="w")

btn_submit = tk.Button(tab1, text="確認送出", command=handle_submit, bg="#2ecc71", fg="white", width=20)
btn_submit.grid(row=4, column=0, columnspan=2, pady=30)

# --- 分頁二內容 (Treeview 升級版) ---
tk.Label(tab2, text="歷史明細 (表格版)", font=("Arial", 14, "bold")).pack(pady=10)

# 1. 定義欄位名稱
columns = ("date", "account", "change", "note")
tree = ttk.Treeview(tab2, columns=columns, show="headings", height=15)

# 2. 設定每一欄的標題文字與寬度
tree.heading("date", text="交易時間")
tree.column("date", width=150, anchor="center")

tree.heading("account", text="帳戶")
tree.column("account", width=80, anchor="center")

tree.heading("change", text="金額變動")
tree.column("change", width=100, anchor="right") # 金額通常靠右對齊 (Right-aligned)

tree.heading("note", text="備註說明")
tree.column("note", width=150, anchor="w")      # 文字備註靠左對齊 (West)

tree.pack(padx=20, pady=10, fill="both", expand=True)


# 3. 重新寫一個專屬於 Treeview 的刷新函數，替換掉舊的
def refresh_history():
    global data
    data = load_data()
    
    # 清空 Treeview 舊資料
    for item in tree.get_children():
        tree.delete(item)
        
    # 將資料逐筆插入表格
    for log in reversed(data["history"][-20:]): # 顯示最近 20 筆
        # 根據金額正負，決定給它加上正號
        change_str = f"+${log['change']}" if log['change'] > 0 else f"${log['change']}"
        
        # 塞入表格
        tree.insert("", tk.END, values=(log['date'], log['account'], change_str, log['note']))

# 刷新按鈕依舊保留
btn_refresh = tk.Button(tab2, text="刷新紀錄", command=refresh_history)
btn_refresh.pack(pady=5)


root.mainloop()