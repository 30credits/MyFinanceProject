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
        
        # 資產防爆鎖
        if amount == 0:
            messagebox.showwarning("提示", "交易金額不能為 $0 元！")
            entry_amount.focus()
            return 
            
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 由帳戶選項直接分流轉帳
        if acc_name == "提款":
            actual_amount = abs(amount) 
            data["balance"]["Bank"] -= actual_amount
            data["balance"]["Cash"] += actual_amount
            
            log = {"date": now, "account": "Transfer", "change": actual_amount, "note": f"[提款] {note_str}"}
            data["history"].append(log)
            messagebox.showinfo("成功", f"【內部轉帳】\n已從 銀行 提領 ${actual_amount} 至 現金！")

        elif acc_name == "存款":
            actual_amount = abs(amount)
            data["balance"]["Cash"] -= actual_amount
            data["balance"]["Bank"] += actual_amount
            
            log = {"date": now, "account": "Transfer", "change": -actual_amount, "note": f"[存款] {note_str}"}
            data["history"].append(log)
            messagebox.showinfo("成功", f"【內部轉帳】\n已將 現金 ${actual_amount} 存入 銀行！")

        # 原有的普通記帳邏輯
        else:
            data["balance"][acc_name] += amount
            log = {"date": now, "account": acc_name, "change": amount, "note": note_str}
            data["history"].append(log)
            
            action_text = "存入" if amount > 0 else "支出"
            messagebox.showinfo("成功", f"已成功記錄 {acc_name} {action_text}: ${abs(amount)}")
        
        save_data(data)
        update_balance_labels()
        
        entry_amount.delete(0, tk.END)
        entry_note.delete(0, tk.END)
        entry_amount.focus() 
        
    except ValueError:
        messagebox.showerror("錯誤", "金額請輸入正確的整數數字！\n(支出請在數字前加上減號，例如: -500)")
        entry_amount.focus()

def update_balance_labels():
    cash_val = data['balance']['Cash']
    bank_val = data['balance']['Bank']
    total_val = cash_val + bank_val
    
    label_cash_val.config(text=f"${cash_val}")
    label_bank_val.config(text=f"${bank_val}")
    label_total_val.config(text=f"${total_val}")

def refresh_history_tree():
    global data
    data = load_data() 
    for item in tree.get_children():
        tree.delete(item)
        
    # 年度時間篩選機制
    current_year = datetime.now().strftime("%Y") 
    label_income_title.config(text=f"【{current_year}年度】總收入:")
    label_expense_title.config(text=f"【{current_year}年度】總支出:")

    total_income = 0
    total_expense = 0

    for log in data["history"]:
        if log['account'] == "Transfer":
            continue
        if not log['date'].startswith(current_year):
            continue 
            
        if log['change'] > 0:
            total_income += log['change']
        else:
            total_expense += log['change']
            
    label_summary_income.config(text=f"+${total_income}")
    label_summary_expense.config(text=f"-${abs(total_expense)}")

    # 渲染表格內容
    for log in reversed(data["history"][-20:]): 
        if log['change'] > 0:
            change_str = f"+${log['change']}"
        else:
            change_str = f"-${abs(log['change'])}"
        tree.insert("", tk.END, values=(log['date'], log['account'], change_str, log['note']))

    # ─── 【今日全新核心：純數學圓餅圖繪製】 ───
    draw_asset_pie_chart()

def draw_asset_pie_chart():
    # 1. 先把舊的圖畫全部擦乾淨，避免重複疊加
    canvas.delete("all")
    
    cash_val = data['balance']['Cash']
    bank_val = data['balance']['Bank']
    total_val = cash_val + bank_val
    
    # 防呆：如果總資產是 0 或者是負數，沒辦法畫圓餅圖，直接寫一行提示字
    if total_val <= 0:
        canvas.create_text(110, 110, text="目前尚無淨資產資料\n無法繪製佔比圖", fill=TEXT_MUTED, font=("Arial", 10), justify="center")
        return

    # 2. 計算各自佔比與角度
    cash_percent = max(0, cash_val / total_val) # 用 max 避免單一帳戶為負數時破壞圖形
    bank_percent = max(0, bank_val / total_val)
    
    # 如果兩個帳戶一正一負，重新校正比例
    if cash_val > 0 and bank_val <= 0:
        cash_percent, bank_percent = 1.0, 0.0
    elif bank_val > 0 and cash_val <= 0:
        cash_percent, bank_percent = 0.0, 1.0

    cash_angle = cash_percent * 360
    bank_angle = bank_percent * 360

    # 3. 在畫布上勾勒扇形 (create_arc)
    # 參數說明：(左上X, 左上Y, 右下X, 右下Y) 代表圓形的外切正方形範圍
    # start 是起始角度，extent 是旋轉半徑角度
    
    current_start = 0
    
    if cash_angle > 0:
        canvas.create_arc(20, 20, 200, 200, start=current_start, extent=cash_angle, fill="#a6e3a1", outline=CARD_DARK, width=2)
        current_start += cash_angle
        
    if bank_angle > 0:
        canvas.create_arc(20, 20, 200, 200, start=current_start, extent=bank_angle, fill="#89b4fa", outline=CARD_DARK, width=2)

    # 4. 繪製精緻的右側小圖例 (Legend)
    # 現金圖例
    canvas.create_rectangle(20, 225, 32, 237, fill="#a6e3a1", outline="")
    canvas.create_text(42, 231, text=f"現金 Cash ({cash_percent*100:.1f}%)", fill=TEXT_LIGHT, font=("Arial", 9), anchor="w")
    
    # 銀行圖例
    canvas.create_rectangle(20, 249, 32, 261, fill="#89b4fa", outline="")
    canvas.create_text(42, 255, text=f"銀行 Bank ({bank_percent*100:.1f}%)", fill=TEXT_LIGHT, font=("Arial", 9), anchor="w")

def show_context_menu(event):
    clicked_item = tree.identify_row(event.y)
    if clicked_item:
        tree.selection_set(clicked_item)
        right_click_menu.post(event.x_root, event.y_root)

def delete_selected_item():
    selected_item = tree.selection()
    if not selected_item: return
        
    item_values = tree.item(selected_item, "values")
    log_date = item_values[0]
    log_account = item_values[1]
    
    raw_change_str = item_values[2].replace("$", "")
    if raw_change_str.startswith("+"):
        log_change = int(raw_change_str.replace("+", ""))
    else:
        log_change = int(raw_change_str.replace("-", "")) * -1

    confirm = messagebox.askyesno("確認刪除", f"你確定要刪除這筆紀錄嗎？\n時間: {log_date}\n金額: {item_values[2]}")
    
    if confirm:
        if log_account == "Transfer":
            if log_change > 0: 
                data["balance"]["Bank"] += log_change
                data["balance"]["Cash"] -= log_change
            else: 
                data["balance"]["Cash"] -= log_change
                data["balance"]["Bank"] += log_change
        else:
            data["balance"][log_account] -= log_change
        
        for log in data["history"]:
            if log["date"] == log_date and log["account"] == log_account and log["change"] == log_change:
                data["history"].remove(log)
                break
                
        save_data(data)
        update_balance_labels()
        refresh_history_tree() 
        messagebox.showinfo("成功", "紀錄已刪除，餘額已修正。")

# =====================================================================
# 3. 視覺介面層 (UI Layer)
# =====================================================================
root = tk.Tk()
root.title("Will's Wealth Manager Visual-Pro v7.8")
root.geometry("780x660") # 👈 寬度橫向大升級！從 520 拓寬到 780 像素

BG_DARK = "#1e1e2e"      
CARD_DARK = "#252538"    
TEXT_LIGHT = "#cdd6f4"   
TEXT_MUTED = "#a6adc8"   
ACCENT_PURPLE = "#cba6f7" 
ACCENT_GOLD = "#f9e2af"   

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
# 為了在大寬度畫面居中，我們稍微調整格子佈局
tab1.columnconfigure(0, weight=1)
tab1.columnconfigure(1, weight=1)

tk.Label(tab1, text="FINANCE DASHBOARD", font=("Impact", 24), bg=CARD_DARK, fg=ACCENT_PURPLE).grid(row=0, column=0, columnspan=2, pady=25)

tk.Label(tab1, text="淨資產總計 (Total Wealth):", font=("Arial", 13, "bold"), bg=CARD_DARK, fg=ACCENT_GOLD).grid(row=1, column=0, sticky="e", padx=15, pady=10)
label_total_val = tk.Label(tab1, text="", font=("Courier New", 20, "bold"), bg=CARD_DARK, fg=ACCENT_GOLD)
label_total_val.grid(row=1, column=1, sticky="w", padx=5)

tk.Label(tab1, text="現金目前餘額 (Cash):", font=("Arial", 11), bg=CARD_DARK, fg=TEXT_LIGHT).grid(row=2, column=0, sticky="e", padx=15, pady=6)
label_cash_val = tk.Label(tab1, text="", font=("Courier New", 15, "bold"), bg=CARD_DARK, fg="#a6e3a1") 
label_cash_val.grid(row=2, column=1, sticky="w", padx=5)

tk.Label(tab1, text="銀行目前餘額 (Bank):", font=("Arial", 11), bg=CARD_DARK, fg=TEXT_LIGHT).grid(row=3, column=0, sticky="e", padx=15, pady=6)
label_bank_val = tk.Label(tab1, text="", font=("Courier New", 15, "bold"), bg=CARD_DARK, fg="#89b4fa") 
label_bank_val.grid(row=3, column=1, sticky="w", padx=5)

update_balance_labels()

tk.Label(tab1, text=" ─── 記錄交易 (常規收支請用正負號判定) ─── ", fg=TEXT_MUTED, bg=CARD_DARK, font=("Arial", 10)).grid(row=4, column=0, columnspan=2, pady=25)

tk.Label(tab1, text="選擇類型/帳戶:", font=("Arial", 11), bg=CARD_DARK, fg=TEXT_LIGHT).grid(row=5, column=0, sticky="e", padx=15, pady=8)
acc_var = tk.StringVar(value="Cash")
acc_menu = tk.OptionMenu(tab1, acc_var, "Cash", "Bank", "提款", "存款")
acc_menu.config(bg="#313244", fg=TEXT_LIGHT, highlightbackground=CARD_DARK, activebackground="#45475a", activeforeground=TEXT_LIGHT)
acc_menu["menu"].config(bg=CARD_DARK, fg=TEXT_LIGHT, activebackground=ACCENT_PURPLE)
acc_menu.grid(row=5, column=1, sticky="w", padx=5)

tk.Label(tab1, text="交易金額:", font=("Arial", 11), bg=CARD_DARK, fg=TEXT_LIGHT).grid(row=6, column=0, sticky="e", padx=15, pady=8)
entry_amount = tk.Entry(tab1, font=("Arial", 12), bg="#313244", fg="#ffffff", insertbackground="white", bd=0, width=22)
entry_amount.grid(row=6, column=1, sticky="w", padx=5, ipady=4)

tk.Label(tab1, text="備註說明:", font=("Arial", 11), bg=CARD_DARK, fg=TEXT_LIGHT).grid(row=7, column=0, sticky="e", padx=15, pady=8)
entry_note = tk.Entry(tab1, font=("Arial", 12), bg="#313244", fg="#ffffff", insertbackground="white", bd=0, width=22)
entry_note.grid(row=7, column=1, sticky="w", padx=5, ipady=4)

btn_submit = tk.Button(tab1, text="確認送出並儲存", command=handle_submit, bg=ACCENT_PURPLE, fg=BG_DARK, activebackground="#b4befe", font=("Arial", 12, "bold"), width=22, bd=0, cursor="hand2")
btn_submit.grid(row=8, column=0, columnspan=2, pady=30)


# ----------------- 分頁二：歷史報表與圖表雙拼介面 -----------------
# 運用橫向排版：左邊放表格與統計，右邊放圓餅圖
frame_left = tk.Frame(tab2, bg=CARD_DARK)
frame_left.pack(side="left", fill="both", expand=True, padx=(10, 5), pady=10)

frame_right = tk.Frame(tab2, bg=CARD_DARK)
frame_right.pack(side="right", fill="both", padx=(5, 10), pady=10)

# 左側：明細與統計
tk.Label(frame_left, text="歷史交易明細表 (右鍵可刪除)", font=("Arial", 12, "bold"), bg=CARD_DARK, fg=TEXT_LIGHT).pack(pady=8)

columns = ("date", "account", "change", "note")
tree = ttk.Treeview(frame_left, columns=columns, show="headings", height=12) 
tree.heading("date", text="交易時間")
tree.column("date", width=130, anchor="center")
tree.heading("account", text="帳戶")
tree.column("account", width=60, anchor="center")
tree.heading("change", text="金額變動")
tree.column("change", width=80, anchor="e") 
tree.heading("note", text="備註說明")
tree.column("note", width=140, anchor="w")
tree.pack(padx=5, pady=5, fill="both", expand=True)

tree.bind("<Button-3>", show_context_menu)

# 左側下方收支統計
frame_summary = tk.Frame(frame_left, bg="#313244", padx=10, pady=6)
frame_summary.pack(padx=5, pady=5, fill="x")

label_income_title = tk.Label(frame_summary, text="年度總收入:", font=("Arial", 9), bg="#313244", fg=TEXT_MUTED)
label_income_title.grid(row=0, column=0, sticky="e", pady=1)
label_summary_income = tk.Label(frame_summary, text="+$0", font=("Courier New", 10, "bold"), bg="#313244", fg="#a6e3a1")
label_summary_income.grid(row=0, column=1, sticky="w", padx=10, pady=1)

label_expense_title = tk.Label(frame_summary, text="年度總支出:", font=("Arial", 9), bg="#313244", fg=TEXT_MUTED)
label_expense_title.grid(row=1, column=0, sticky="e", pady=1)
label_summary_expense = tk.Label(frame_summary, text="-$0", font=("Courier New", 10, "bold"), bg="#313244", fg="#f38ba8")
label_summary_expense.grid(row=1, column=1, sticky="w", padx=10, pady=1)

btn_refresh = tk.Button(frame_left, text="🔄 手動刷新報表", command=refresh_history_tree, bg="#313244", fg=TEXT_LIGHT, activebackground="#45475a", activeforeground=TEXT_LIGHT, bd=0, font=("Arial", 9), padx=10, pady=4)
btn_refresh.pack(pady=5)

# 右側：圖表畫布區
tk.Label(frame_right, text="目前資產分佈佔比", font=("Arial", 12, "bold"), bg=CARD_DARK, fg=ACCENT_GOLD).pack(pady=8)

# 建立畫布元件：設定寬高為 220x260，背景色保持與卡片一致
canvas = tk.Canvas(frame_right, width=220, height=260, bg=CARD_DARK, highlightthickness=0)
canvas.pack(padx=10, pady=10, fill="both", expand=True)


# =====================================================================
# 4. 自動化事件綁定與啟動
# =====================================================================
def on_tab_change(event):
    if notebook.index("current") == 1: 
        refresh_history_tree()

notebook.bind("<<NotebookTabChanged>>", on_tab_change)

entry_amount.bind("<Return>", lambda e: handle_submit())
entry_note.bind("<Return>", lambda e: handle_submit())

entry_amount.focus()
root.mainloop()