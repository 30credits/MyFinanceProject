import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import json
from datetime import datetime

# --- 【就加在這裡！】 ---
print(f"目前程式的工作目錄是: {os.getcwd()}")
# -----------------------

FILE_NAME = "data_v2.json"

# --- 1. 資料處理 ---
def load_data():
    try:
        with open("data_v2.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {"balance": {"Cash": 0, "Bank": 0}, "history": []}

def save_data(data):
    with open("data_v2.json", "w") as file:
        json.dump(data, file, indent=4)

data = load_data()

# --- 2. 邏輯函數 ---
def handle_submit():
    # 這裡要抓的是 tab1 裡面的輸入框
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
        
        # 清空輸入框
        entry_amount.delete(0, tk.END)
        entry_note.delete(0, tk.END)
        
    except ValueError:
        messagebox.showerror("錯誤", "請輸入正確數字")

def refresh_history():
    global data
    data = load_data() # 重新從檔案抓取最新資料
    history_text.delete("1.0", tk.END)
    for log in reversed(data["history"][-15:]): # 顯示最近 15 筆
        line = f"{log['date']} | {log['account']} | {log['change']} | {log['note']}\n"
        history_text.insert(tk.END, line)

# --- 3. UI 介面 ---
root = tk.Tk()
root.title("Will's Finance Pro v2")
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

# 【關鍵】執行按鈕放在 tab1
btn_submit = tk.Button(tab1, text="確認送出", command=handle_submit, bg="#2ecc71", fg="white", width=20)
btn_submit.grid(row=4, column=0, columnspan=2, pady=30)

# --- 分頁二內容 ---
tk.Label(tab2, text="歷史明細", font=("Arial", 14, "bold")).pack(pady=10)
history_text = tk.Text(tab2, height=15, width=55)
history_text.pack(padx=20, pady=10)

btn_refresh = tk.Button(tab2, text="刷新紀錄", command=refresh_history)
btn_refresh.pack(pady=5)

# 當切換到分頁二時自動刷新 (選配)
def on_tab_change(event):
    if notebook.index("current") == 1: # 如果選中的是索引為 1 的分頁 (即第二頁)
        refresh_history()

notebook.bind("<<NotebookTabChanged>>", on_tab_change)

root.mainloop()