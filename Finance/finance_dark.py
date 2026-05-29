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
        if amount == 0:
            messagebox.showwarning("提示", "交易金額不能為 $0 元！")
            return # 👈 攔截！直接在這裡結束函數，不讓程式往下存檔
            
        if amount < 0:
            messagebox.showwarning("提示", "請輸入正數金額！\n(若為支出，未來將由系統分類，或請確保輸入邏輯正確)")
            return # 👈 攔截！   
        data["balance"][acc_name] += amount
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log = {"date": now, "account": acc_name, "change": amount, "note": note_str}
        data["history"].append(log)
        
        save_data(data)
        update_balance_labels()
        
        messagebox.showinfo("成功", f"已成功記錄 {acc_name}: ${amount}")
        
        entry_amount.delete(0, tk.END)
        entry_note.delete(0, tk.END)
        entry_amount.focus()
        
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
    log_change = int(item_values[2].replace("$", "").replace("+", ""))

    confirm = messagebox.askyesno("確認刪除", f"你確定要刪除這筆紀錄嗎？\n時間: {log_date}\n金額: {item_values[2]}\n\n(刪除後資產餘額將會同步自動逆向扣回)")
    
    if confirm:
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
# 3. 視覺介面層 (UI Layer) —— 【今日改造重點】
# =====================================================================
root = tk.Tk()
root.title("Will's Wealth Manager Dark v5.0")
root.geometry("520x620") # 稍微加高一點讓排版更舒服

# 定義深色主題顏色常數
BG_DARK = "#1e1e2e"      # 整個視窗的背景色
CARD_DARK = "#252538"    # 分頁內部的背景色
TEXT_LIGHT = "#cdd6f4"   # 主要文字顏色
TEXT_MUTED = "#a6adc8"   # 次要提示文字顏色
ACCENT_PURPLE = "#cba6f7" # 亮點按鈕顏色

root.configure(bg=BG_DARK)

# --- 配置 ttk 元件的深色樣式 (Style) ---
style = ttk.Style()
style.theme_use("default") # 先切換到預設主題，方便我們客製化

# 1. 改造 Notebook (分頁標籤)
style.configure("TNotebook", background=BG_DARK, borderwidth=0)
style.configure("TNotebook.Tab", background="#313244", foreground=TEXT_LIGHT, padding=[15, 5], font=("Arial", 10))
style.map("TNotebook.Tab", background=[("selected", CARD_DARK)], foreground=[("selected", ACCENT_PURPLE)])

# 2. 改造 Frame (分頁畫布)
style.configure("TFrame", background=CARD_DARK)

# 3. 改造 Treeview (歷史報表表格)
style.configure("Treeview", background=CARD_DARK, fieldbackground=CARD_DARK, foreground=TEXT_LIGHT, rowheight=25)
style.configure("Treeview.Heading", background="#313244", foreground=ACCENT_PURPLE, borderwidth=0, font=("Arial", 10, "bold"))
style.map("Treeview", background=[("selected", "#45475a")], foreground=[("selected", "#ffffff")])

# --- 右鍵選單元件深色化 ---
right_click_menu = tk.Menu(root, tearoff=0, bg=CARD_DARK, fg=TEXT_LIGHT, activebackground=ACCENT_PURPLE, activeforeground=BG_DARK, bd=0)
right_click_menu.add_command(label="❌ 刪除此筆交易", command=delete_selected_item)

# 初始化分頁
notebook = ttk.Notebook(root)
notebook.pack(pady=15, expand=True, fill="both", padx=15)

tab1 = ttk.Frame(notebook)
tab2 = ttk.Frame(notebook)

notebook.add(tab1, text="  資產記帳錄入  ")
notebook.add(tab2, text="  歷史明細報表  ")

# ----------------- 分頁一：記帳主介面 -----------------
tk.Label(tab1, text="FINANCE DASHBOARD", font=("Impact", 20), bg=CARD_DARK, fg=ACCENT_PURPLE).grid(row=0, column=0, columnspan=2, pady=25)

tk.Label(tab1, text="現金目前餘額 (Cash):", font=("Arial", 10, "bold"), bg=CARD_DARK, fg=TEXT_LIGHT).grid(row=1, column=0, sticky="e", padx=15, pady=8)
label_cash_val = tk.Label(tab1, text="", font=("Courier New", 14, "bold"), bg=CARD_DARK, fg="#a6e3a1") # 賺錢綠
label_cash_val.grid(row=1, column=1, sticky="w", padx=5)

tk.Label(tab1, text="銀行目前餘額 (Bank):", font=("Arial", 10, "bold"), bg=CARD_DARK, fg=TEXT_LIGHT).grid(row=2, column=0, sticky="e", padx=15, pady=8)
label_bank_val = tk.Label(tab1, text="", font=("Courier New", 14, "bold"), bg=CARD_DARK, fg="#89b4fa") # 銀行藍
label_bank_val.grid(row=2, column=1, sticky="w", padx=5)

update_balance_labels()

tk.Label(tab1, text=" ─── 記錄新交易 ─── ", fg=TEXT_MUTED, bg=CARD_DARK, font=("Arial", 9)).grid(row=3, column=0, columnspan=2, pady=20)

tk.Label(tab1, text="選擇帳戶:", font=("Arial", 10), bg=CARD_DARK, fg=TEXT_LIGHT).grid(row=4, column=0, sticky="e", padx=15, pady=8)
acc_var = tk.StringVar(value="Cash")
# 讓 OptionMenu 外觀配合深色模式
acc_menu = tk.OptionMenu(tab1, acc_var, "Cash", "Bank")
acc_menu.config(bg="#313244", fg=TEXT_LIGHT, highlightbackground=CARD_DARK, activebackground="#45475a", activeforeground=TEXT_LIGHT)
acc_menu["menu"].config(bg=CARD_DARK, fg=TEXT_LIGHT, activebackground=ACCENT_PURPLE)
acc_menu.grid(row=4, column=1, sticky="w", padx=5)

tk.Label(tab1, text="交易金額:", font=("Arial", 10), bg=CARD_DARK, fg=TEXT_LIGHT).grid(row=5, column=0, sticky="e", padx=15, pady=8)
entry_amount = tk.Entry(tab1, font=("Arial", 11), bg="#313244", fg="#ffffff", insertbackground="white", bd=0, width=20)
entry_amount.grid(row=5, column=1, sticky="w", padx=5, ipady=4) # 增加內襯高度看起來更現代

tk.Label(tab1, text="備註說明:", font=("Arial", 10), bg=CARD_DARK, fg=TEXT_LIGHT).grid(row=6, column=0, sticky="e", padx=15, pady=8)
entry_note = tk.Entry(tab1, font=("Arial", 11), bg="#313244", fg="#ffffff", insertbackground="white", bd=0, width=20)
entry_note.grid(row=6, column=1, sticky="w", padx=5, ipady=4)

# 現代化炫彩按鈕
btn_submit = tk.Button(tab1, text="確認送出並儲存", command=handle_submit, bg=ACCENT_PURPLE, fg=BG_DARK, activebackground="#b4befe", font=("Arial", 11, "bold"), width=20, bd=0, cursor="hand2")
btn_submit.grid(row=7, column=0, columnspan=2, pady=30)


# ----------------- 分頁二：歷史報表介面 -----------------
tk.Label(tab2, text="歷史交易明細表 (右鍵可刪除錯帳)", font=("Arial", 13, "bold"), bg=CARD_DARK, fg=TEXT_LIGHT).pack(pady=15)

columns = ("date", "account", "change", "note")
tree = ttk.Treeview(tab2, columns=columns, show="headings", height=14)

tree.heading("date", text="交易時間")
tree.column("date", width=140, anchor="center")

tree.heading("account", text="帳戶")
tree.column("account", width=70, anchor="center")

tree.heading("change", text="金額變動")
tree.column("change", width=90, anchor="e") # 👈 精準靠右對齊！

tree.heading("note", text="備註說明")
tree.column("note", width=160, anchor="w")

tree.pack(padx=15, pady=5, fill="both", expand=True)

tree.bind("<Button-3>", show_context_menu)

# 深色手動刷新按鈕
btn_refresh = tk.Button(tab2, text="🔄 手動刷新報表", command=refresh_history_tree, bg="#313244", fg=TEXT_LIGHT, activebackground="#45475a", activeforeground=TEXT_LIGHT, bd=0, font=("Arial", 9), padx=10, pady=4)
btn_refresh.pack(pady=15)


# =====================================================================
# 4. 自動化事件綁定與啟動
# =====================================================================
def on_tab_change(event):
    if notebook.index("current") == 1: 
        refresh_history_tree()

notebook.bind("<<NotebookTabChanged>>", on_tab_change)
entry_amount.bind("<Return>", lambda e: handle_submit())
entry_note.bind("<Return>", lambda e: handle_submit())
root.mainloop()