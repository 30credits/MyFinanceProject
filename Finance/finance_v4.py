import tkinter as tk
from tkinter import ttk, messagebox
import json
from datetime import datetime
import os
import sys

# =====================================================================
# 0. 系統環境設定
# =====================================================================
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FILE_NAME = os.path.join(BASE_DIR, "data_v2.json")

# =====================================================================
# 1. 資料處理層 (Data Layer)
# =====================================================================
def load_data():
    try:
        with open(FILE_NAME, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        initial_data = {"balance": {"Cash": 0, "Bank": 0}, "history": []}
        with open(FILE_NAME, "w", encoding="utf-8") as file:
            json.dump(initial_data, file, indent=4, ensure_ascii=False)
        return initial_data

def save_data(data):
    with open(FILE_NAME, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

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
        data["balance"][acc_name] += amount
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log = {"date": now, "account": acc_name, "change": amount, "note": note_str}
        data["history"].append(log)
        
        save_data(data)
        update_balance_labels()
        
        messagebox.showinfo("成功", f"已成功記錄 {acc_name}: ${amount}")
        
        entry_amount.delete(0, tk.END)
        entry_note.delete(0, tk.END)
        
    except ValueError:
        messagebox.showerror("錯誤", "金額請輸入正確的整數數字！")

def update_balance_labels():
    label_cash_val.config(text=f"${data['balance']['Cash']}")
    label_bank_val.config(text=f"${data['balance']['Bank']}")

def refresh_history_tree():
    global data
    data = load_data() 
    
    for item in tree.get_children():
        tree.delete(item)
        
    for log in reversed(data["history"][-20:]): 
        if log['change'] > 0:
            change_str = f"+${log['change']}"
        else:
            change_str = f"${log['change']}"
            
        tree.insert("", tk.END, values=(log['date'], log['account'], change_str, log['note']))

# --- 【今日全新亮點：右鍵刪除邏輯】 ---

def show_context_menu(event):
    """當使用者在表格點選右鍵時，彈出選單"""
    # 1. 自動選取滑鼠點擊的那一個橫列 (Row)
    clicked_item = tree.identify_row(event.y)
    if clicked_item:
        tree.selection_set(clicked_item) # 強制聚焦選取該列
        # 2. 在滑鼠點擊的絕對座標 (x_root, y_root) 彈出右鍵選單
        right_click_menu.post(event.x_root, event.y_root)

def delete_selected_item():
    """執行刪除邏輯：不只要在畫面上刪除，還要扣回 JSON 的錢"""
    # 1. 取得目前被選取的橫列
    selected_item = tree.selection()
    if not selected_item:
        return
        
    # 2. 抓取這列在畫面上的數值
    item_values = tree.item(selected_item, "values")
    # item_values 會是一個陣列，對應我們定義的欄位：(時間, 帳戶, 金額變動, 備註)
    log_date = item_values[0]
    log_account = item_values[1]
    log_change = int(item_values[2].replace("$", "").replace("+", "")) # 把 +$5000 還原成 5000 數字

    # 3. 跳出確認視窗，防止手滑
    confirm = messagebox.askyesno("確認刪除", f"你確定要刪除這筆紀錄嗎？\n時間: {log_date}\n金額: {item_values[2]}\n\n(刪除後資產餘額將會同步自動逆向扣回)")
    
    if confirm:
        # 4. 逆向校正資產帳戶的餘額 (原本加的就減掉，原本減的就加回來)
        data["balance"][log_account] -= log_change
        
        # 5. 從 JSON 歷史紀錄陣列中剔除這一筆 (比對時間與帳戶)
        for log in data["history"]:
            if log["date"] == log_date and log["account"] == log_account and log["change"] == log_change:
                data["history"].remove(log)
                break # 刪到一筆就收工，防止時間完全相同的帳一起被刪
                
        # 6. 存檔並同步刷新所有介面
        save_data(data)
        update_balance_labels()
        refresh_history_tree()
        messagebox.showinfo("成功", "該筆紀錄已徹底刪除，餘額已修正。")

# =====================================================================
# 3. 視覺介面層 (UI Layer)
# =====================================================================
root = tk.Tk()
root.title("Will's Wealth Manager Pro v4.0")
root.geometry("520x580")
root.configure(bg="#f8f9fa")

# --- 右鍵選單元件初始化 ---
right_click_menu = tk.Menu(root, tearoff=0)
right_click_menu.add_command(label="❌ 刪除此筆交易", command=delete_selected_item)

notebook = ttk.Notebook(root)
notebook.pack(pady=10, expand=True, fill="both")

tab1 = ttk.Frame(notebook)
tab2 = ttk.Frame(notebook)

notebook.add(tab1, text="  資產記帳錄入  ")
notebook.add(tab2, text="  歷史明細報表  ")

# --- 分頁一：記帳主介面 ---
tk.Label(tab1, text="FINANCE DASHBOARD", font=("Helvetica", 16, "bold"), fg="#2c3e50").grid(row=0, column=0, columnspan=2, pady=20)

tk.Label(tab1, text="現金目前餘額 (Cash):", font=("Arial", 10)).grid(row=1, column=0, sticky="e", padx=15, pady=5)
label_cash_val = tk.Label(tab1, text="", font=("Arial", 12, "bold"), fg="#27ae60")
label_cash_val.grid(row=1, column=1, sticky="w", padx=5)

tk.Label(tab1, text="銀行目前餘額 (Bank):", font=("Arial", 10)).grid(row=2, column=0, sticky="e", padx=15, pady=5)
label_bank_val = tk.Label(tab1, text="", font=("Arial", 12, "bold"), fg="#2980b9")
label_bank_val.grid(row=2, column=1, sticky="w", padx=5)

update_balance_labels()

tk.Label(tab1, text=" 記 錄 新 交 易 ", fg="#95a5a6").grid(row=3, column=0, columnspan=2, pady=20)

tk.Label(tab1, text="選擇帳戶:", font=("Arial", 10)).grid(row=4, column=0, sticky="e", padx=15, pady=8)
acc_var = tk.StringVar(value="Cash")
acc_menu = tk.OptionMenu(tab1, acc_var, "Cash", "Bank")
acc_menu.grid(row=4, column=1, sticky="w", padx=5)

tk.Label(tab1, text="交易金額:", font=("Arial", 10)).grid(row=5, column=0, sticky="e", padx=15, pady=8)
entry_amount = tk.Entry(tab1, font=("Arial", 10), bd=1, relief="solid", width=22)
entry_amount.grid(row=5, column=1, sticky="w", padx=5)

tk.Label(tab1, text="備註說明:", font=("Arial", 10)).grid(row=6, column=0, sticky="e", padx=15, pady=8)
entry_note = tk.Entry(tab1, font=("Arial", 10), bd=1, relief="solid", width=22)
entry_note.grid(row=6, column=1, sticky="w", padx=5)

btn_submit = tk.Button(tab1, text="確認送出並儲存", command=handle_submit, bg="#2c3e50", fg="white", font=("Helvetica", 10, "bold"), width=22, pady=5)
btn_submit.grid(row=7, column=0, columnspan=2, pady=25)


# --- 分頁二：歷史報表介面 ---
tk.Label(tab2, text="歷史交易明細表 (右鍵可刪除錯帳)", font=("Arial", 14, "bold"), fg="#2c3e50").pack(pady=15)

columns = ("date", "account", "change", "note")
tree = ttk.Treeview(tab2, columns=columns, show="headings", height=16)

tree.heading("date", text="交易時間")
tree.column("date", width=140, anchor="center")

tree.heading("account", text="帳戶")
tree.column("account", width=70, anchor="center")

tree.heading("change", text="金額變動")
tree.column("change", width=90, anchor="e")

tree.heading("note", text="備註說明")
tree.column("note", width=160, anchor="w")

tree.pack(padx=15, pady=5, fill="both", expand=True)

# 【關鍵綁定】當在 Treeview 表格上點擊滑鼠右鍵 (<Button-3>) 時，發動 show_context_menu 函數
tree.bind("<Button-3>", show_context_menu)

btn_refresh = tk.Button(tab2, text="手動刷新報表", command=refresh_history_tree, font=("Arial", 9))
btn_refresh.pack(pady=10)


# =====================================================================
# 4. 自動化事件綁定與啟動
# =====================================================================
def on_tab_change(event):
    if notebook.index("current") == 1: 
        refresh_history_tree()

notebook.bind("<<NotebookTabChanged>>", on_tab_change)

root.mainloop()