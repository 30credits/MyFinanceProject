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
        
        # ─── 【資產防爆鎖 2.0：解鎖負數，但禁止 0 元】 ───
        if amount == 0:
            messagebox.showwarning("提示", "交易金額不能為 $0 元！")
            entry_amount.focus()
            return 
        # ──────────────────────────────────────────────────
        
        # 正數負數皆放行，直接加進資產（加負數等於扣錢，邏輯完全自洽！）
        data["balance"][acc_name] += amount
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log = {"date": now, "account": acc_name, "change": amount, "note": note_str}
        data["history"].append(log)
        
        save_data(data)
        update_balance_labels()
        
        # 根據正負號，彈出不同的親切提示
        action_text = "存入" if amount > 0 else "支出"
        abs_amount = abs(amount) # 取絕對值，讓提示寫 $500 而不是 $-500
        messagebox.showinfo("成功", f"已成功記錄 {acc_name} {action_text}: ${abs_amount}")
        
        entry_amount.delete(0, tk.END)
        entry_note.delete(0, tk.END)
        entry_amount.focus() # UX 焦點自動回歸
        
    except ValueError:
        messagebox.showerror("錯誤", "金額請輸入正確的整數數字！\n(支出請在數字前加上減號，例如: -500)")
        entry_amount.focus()

def update_balance_labels():
    # 讀取個別資產
    cash_val = data['balance']['Cash']
    bank_val = data['balance']['Bank']
    total_val = cash_val + bank_val # 👈 自動計算總資產！
    
    label_cash_val.config(text=f"${cash_val}")
    label_bank_val.config(text=f"${bank_val}")
    label_total_val.config(text=f"${total_val}") # 👈 刷新總資產看板

def refresh_history_tree():
    global data
    data = load_data() 
    
    for item in tree.get_children():
        tree.delete(item)
        
    for log in reversed(data["history"][-20:]): 
        # ─── 【視覺優化：正數顯示 +$ 號，負數顯示 -$ 號】 ───
        if log['change'] > 0:
            change_str = f"+${log['change']}"
        else:
            change_str = f"-${abs(log['change'])}" # 把 $-500 格式化成更美麗的 -$500
            
        tree.insert("", tk.END, values=(log['date'], log['account'], change_str, log['note']))

def show_context_menu(event):
    clicked_item = tree.identify_row(event.y)
    if clicked_item:
        tree.selection_set(clicked_item)
        right_click_menu.post(event.x_root, event.y_root)

def delete_selected_item():
    selected_item = tree.selection()
    if not selected_item:
        return
        
    item_values = tree.item(selected_item, "values")
    log_date = item_values[0]
    log_account = item_values[1]
    
    # 還原金額的防錯解析（需要同時相容 +$ 和 -$ 的字串）
    raw_change_str = item_values[2].replace("$", "")
    if raw_change_str.startswith("+"):
        log_change = int(raw_change_str.replace("+", ""))
    else:
        log_change = int(raw_change_str.replace("-", "")) * -1 # 保持負數本色

    confirm = messagebox.askyesno("確認刪除", f"你確定要刪除這筆紀錄嗎？\n時間: {log_date}\n金額: {item_values[2]}\n\n(刪除後資產餘額將會自動做逆向補償)")
    
    if confirm:
        # 逆向補償：減去原本的變動（減去負數等於加回來，邏輯依然完美！）
        data["balance"][log_account] -= log_change
        
        for log in data["history"]:
            if log["date"] == log_date and log["account"] == log_account and log["change"] == log_change:
                data["history"].remove(log)
                break
                
        save_data(data)
        update_balance_labels()
        refresh_history_tree()
        messagebox.showinfo("成功", "該筆紀錄已徹底刪除，餘額已修正。")

# =====================================================================
# 3. 視覺介面層 (UI Layer)
# =====================================================================
root = tk.Tk()
root.title("Will's Wealth Manager Pro v5.5")
root.geometry("520x660") # 再稍微加高 40 像素安放總資產看板

BG_DARK = "#1e1e2e"      
CARD_DARK = "#252538"    
TEXT_LIGHT = "#cdd6f4"   
TEXT_MUTED = "#a6adc8"   
ACCENT_PURPLE = "#cba6f7" 
ACCENT_GOLD = "#f9e2af"   # 新增：代表財富的黃金亮黃色

root.configure(bg=BG_DARK)

style = ttk.Style()
style.theme_use("default")

style.configure("TNotebook", background=BG_DARK, borderwidth=0)
style.configure("TNotebook.Tab", background="#313244", foreground=TEXT_LIGHT, padding=[15, 5], font=("Arial", 10))
style.map("TNotebook.Tab", background=[("selected", CARD_DARK)], foreground=[("selected", ACCENT_PURPLE)])
style.configure("TFrame", background=CARD_DARK)

style.configure("Treeview", background=CARD_DARK, fieldbackground=CARD_DARK, foreground=TEXT_LIGHT, rowheight=25)
style.configure("Treeview.Heading", background="#313244", foreground=ACCENT_PURPLE, borderwidth=0, font=("Arial", 10, "bold"))
style.map("Treeview", background=[("selected", "#45475a")], foreground=[("selected", "#ffffff")])

right_click_menu = tk.Menu(root, tearoff=0, bg=CARD_DARK, fg=TEXT_LIGHT, activebackground=ACCENT_PURPLE, activeforeground=BG_DARK, bd=0)
right_click_menu.add_command(label="❌ 刪除此筆交易", command=delete_selected_item)

notebook = ttk.Notebook(root)
notebook.pack(pady=15, expand=True, fill="both", padx=15)

tab1 = ttk.Frame(notebook)
tab2 = ttk.Frame(notebook)

notebook.add(tab1, text="  資產記帳錄入  ")
notebook.add(tab2, text="  歷史明細報表  ")

# ----------------- 分頁一：記帳主介面 -----------------
tk.Label(tab1, text="FINANCE DASHBOARD", font=("Impact", 20), bg=CARD_DARK, fg=ACCENT_PURPLE).grid(row=0, column=0, columnspan=2, pady=20)

# --- 【全新黃金大看板：總資產總計】 ---
tk.Label(tab1, text="淨資產總計 (Total Wealth):", font=("Arial", 12, "bold"), bg=CARD_DARK, fg=ACCENT_GOLD).grid(row=1, column=0, sticky="e", padx=15, pady=10)
label_total_val = tk.Label(tab1, text="", font=("Courier New", 18, "bold"), bg=CARD_DARK, fg=ACCENT_GOLD)
label_total_val.grid(row=1, column=1, sticky="w", padx=5)

# 原有帳戶餘額下移
tk.Label(tab1, text="現金目前餘額 (Cash):", font=("Arial", 10), bg=CARD_DARK, fg=TEXT_LIGHT).grid(row=2, column=0, sticky="e", padx=15, pady=6)
label_cash_val = tk.Label(tab1, text="", font=("Courier New", 13, "bold"), bg=CARD_DARK, fg="#a6e3a1") 
label_cash_val.grid(row=2, column=1, sticky="w", padx=5)

tk.Label(tab1, text="銀行目前餘額 (Bank):", font=("Arial", 10), bg=CARD_DARK, fg=TEXT_LIGHT).grid(row=3, column=0, sticky="e", padx=15, pady=6)
label_bank_val = tk.Label(tab1, text="", font=("Courier New", 13, "bold"), bg=CARD_DARK, fg="#89b4fa") 
label_bank_val.grid(row=3, column=1, sticky="w", padx=5)

update_balance_labels()

tk.Label(tab1, text=" ─── 記錄新交易 (支出請輸入負數) ─── ", fg=TEXT_MUTED, bg=CARD_DARK, font=("Arial", 9)).grid(row=4, column=0, columnspan=2, pady=20)

tk.Label(tab1, text="選擇帳戶:", font=("Arial", 10), bg=CARD_DARK, fg=TEXT_LIGHT).grid(row=5, column=0, sticky="e", padx=15, pady=8)
acc_var = tk.StringVar(value="Cash")
acc_menu = tk.OptionMenu(tab1, acc_var, "Cash", "Bank")
acc_menu.config(bg="#313244", fg=TEXT_LIGHT, highlightbackground=CARD_DARK, activebackground="#45475a", activeforeground=TEXT_LIGHT)
acc_menu["menu"].config(bg=CARD_DARK, fg=TEXT_LIGHT, activebackground=ACCENT_PURPLE)
acc_menu.grid(row=5, column=1, sticky="w", padx=5)

tk.Label(tab1, text="交易金額:", font=("Arial", 10), bg=CARD_DARK, fg=TEXT_LIGHT).grid(row=6, column=0, sticky="e", padx=15, pady=8)
entry_amount = tk.Entry(tab1, font=("Arial", 11), bg="#313244", fg="#ffffff", insertbackground="white", bd=0, width=20)
entry_amount.grid(row=6, column=1, sticky="w", padx=5, ipady=4)

tk.Label(tab1, text="備註說明:", font=("Arial", 10), bg=CARD_DARK, fg=TEXT_LIGHT).grid(row=7, column=0, sticky="e", padx=15, pady=8)
entry_note = tk.Entry(tab1, font=("Arial", 11), bg="#313244", fg="#ffffff", insertbackground="white", bd=0, width=20)
entry_note.grid(row=7, column=1, sticky="w", padx=5, ipady=4)

btn_submit = tk.Button(tab1, text="確認送出並儲存", command=handle_submit, bg=ACCENT_PURPLE, fg=BG_DARK, activebackground="#b4befe", font=("Arial", 11, "bold"), width=20, bd=0, cursor="hand2")
btn_submit.grid(row=8, column=0, columnspan=2, pady=25)


# ----------------- 分頁二：歷史報表介面 -----------------
tk.Label(tab2, text="歷史交易明細表 (右鍵可刪除錯帳)", font=("Arial", 13, "bold"), bg=CARD_DARK, fg=TEXT_LIGHT).pack(pady=15)

columns = ("date", "account", "change", "note")
tree = ttk.Treeview(tab2, columns=columns, show="headings", height=14)

tree.heading("date", text="交易時間")
tree.column("date", width=140, anchor="center")

tree.heading("account", text="帳戶")
tree.column("account", width=70, anchor="center")

tree.heading("change", text="金額變動")
tree.column("change", width=90, anchor="e") 

tree.heading("note", text="備註說明")
tree.column("note", width=160, anchor="w")

tree.pack(padx=15, pady=5, fill="both", expand=True)

tree.bind("<Button-3>", show_context_menu)

btn_refresh = tk.Button(tab2, text="🔄 手動刷新報表", command=refresh_history_tree, bg="#313244", fg=TEXT_LIGHT, activebackground="#45475a", activeforeground=TEXT_LIGHT, bd=0, font=("Arial", 9), padx=10, pady=4)
btn_refresh.pack(pady=15)


# =====================================================================
# 4. 自動化事件綁定與啟動
# =====================================================================
def on_tab_change(event):
    if notebook.index("current") == 1: 
        refresh_history_tree()

notebook.bind("<<NotebookTabChanged>>", on_tab_change)

# 鍵盤 Enter 鍵流暢綁定
entry_amount.bind("<Return>", lambda e: handle_submit())
entry_note.bind("<Return>", lambda e: handle_submit())

# 初始讓焦點停留在金額輸入框
entry_amount.focus()

root.mainloop()