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
# 1. 資料處理層 (Data Layer) —— 【解鎖動態初始化】
# =====================================================================
def load_data():
    try:
        with open(FILE_NAME, "r", encoding="utf-8") as file:
            existing_data = json.load(file)
            # 防呆：確保新結構相容，如果發現沒有 balance 字典就重置
            if "balance" not in existing_data:
                raise ValueError
            return existing_data
    except (FileNotFoundError, ValueError):
        # 初始預設四個常用帳戶，使用者未來可以自由增刪
        initial_data = {
            "balance": {
                "現金 Cash": 0, 
                "銀行 Bank": 0, 
                "悠遊卡": 0, 
                "電子支付": 0
            }, 
            "history": []
        }
        with open(FILE_NAME, "w", encoding="utf-8") as file:
            json.dump(initial_data, file, indent=4, ensure_ascii=False)
        return initial_data

def save_data(data):
    with open(FILE_NAME, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

data = load_data()

# =====================================================================
# 2. 核心動作邏輯層 (Business Logic) —— 【全面動態化分流】
# =====================================================================
def handle_submit():
    amount_str = entry_amount.get()
    note_str = entry_note.get()
    action_type = acc_var.get() # 現已變成動態選單

    try:
        amount = int(amount_str)
        if amount == 0:
            messagebox.showwarning("提示", "交易金額不能為 $0 元！")
            entry_amount.focus()
            return 
            
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # ─── 【動態轉帳大腦】 ───
        if action_type == "🔄 內部轉帳":
            # 轉帳需要知道從哪轉到哪，我們用一個優雅的 Tkinter 彈出視窗來詢問！
            show_transfer_dialog(amount, note_str, now)
            return

        # ─── 常規記帳邏輯（自動適應任何帳戶名稱） ───
        else:
            if action_type in data["balance"]:
                data["balance"][action_type] += amount
                log = {"date": now, "account": action_type, "change": amount, "note": note_str}
                data["history"].append(log)
                
                action_text = "存入" if amount > 0 else "支出"
                finalize_transaction(f"已成功記錄 {action_type} {action_text}: ${abs(amount)}")
            else:
                messagebox.showerror("錯誤", "找不到該帳戶！")
        
    except ValueError:
        messagebox.showerror("錯誤", "金額請輸入正確的整數數字！\n(支出請在數字前加上減號，例如: -500)")
        entry_amount.focus()

# 專屬轉帳彈出視窗：免打字，直接選出發地和目的地！
def show_transfer_dialog(amount, note_str, now):
    transfer_win = tk.Toplevel(root)
    transfer_win.title("選擇轉帳方向")
    transfer_win.geometry("320x200")
    transfer_win.configure(bg=CARD_DARK)
    transfer_win.grab_set() # 鎖定視窗，必須填完才能回到主畫面
    
    tk.Label(transfer_win, text=f"轉帳金額: ${amount}", font=("Arial", 11, "bold"), bg=CARD_DARK, fg=ACCENT_GOLD).pack(pady=10)
    
    accounts = list(data["balance"].keys())
    
    # 出發地
    tk.Label(transfer_win, text="請選擇【來源帳戶】(扣錢):", bg=CARD_DARK, fg=TEXT_LIGHT).pack()
    from_var = tk.StringVar(value=accounts[0])
    from_menu = ttk.Combobox(transfer_win, textvariable=from_var, values=accounts, state="readonly")
    from_menu.pack(pady=5)
    
    # 目的地
    tk.Label(transfer_win, text="請選擇【目的帳戶】(加錢):", bg=CARD_DARK, fg=TEXT_LIGHT).pack()
    to_var = tk.StringVar(value=accounts[1] if len(accounts) > 1 else accounts[0])
    to_menu = ttk.Combobox(transfer_win, textvariable=to_var, values=accounts, state="readonly")
    to_menu.pack(pady=5)
    
    def confirm_transfer():
        f_acc = from_var.get()
        t_acc = to_var.get()
        if f_acc == t_acc:
            messagebox.showwarning("提示", "來源帳戶與目的帳戶不能相同！", parent=transfer_win)
            return
            
        # 執行扣補
        data["balance"][f_acc] -= abs(amount)
        data["balance"][t_acc] += abs(amount)
        
        # 自由的備註欄紀錄
        final_note = f"[{f_acc} ➔ {t_acc}] {note_str}".strip()
        log = {"date": now, "account": "Transfer", "change": abs(amount), "note": final_note, "from": f_acc, "to": t_acc}
        data["history"].append(log)
        
        transfer_win.destroy()
        finalize_transaction(f"【轉帳成功】\n已從 {f_acc} 轉移 ${abs(amount)} 至 {t_acc}！")
        
    tk.Button(transfer_win, text="確定轉帳", command=confirm_transfer, bg=ACCENT_PURPLE, fg=BG_DARK, bd=0, font=("Arial", 10, "bold"), padx=10, pady=4).pack(pady=10)

def finalize_transaction(success_msg):
    save_data(data)
    update_balance_labels()
    messagebox.showinfo("成功", success_msg)
    entry_amount.delete(0, tk.END)
    entry_note.delete(0, tk.END)
    entry_amount.focus()

# ─── 【重要進化：動態看板產生器】 ───
def update_balance_labels():
    # 先清除舊的標籤，避免疊加
    for widget in frame_dashboard.winfo_children():
        widget.destroy()
        
    total_wealth = sum(data["balance"].values())
    
    # 1. 永遠居中頂部的總資產黃金看板
    tk.Label(frame_dashboard, text="淨資產總計 (Total Wealth):", font=("Arial", 13, "bold"), bg=CARD_DARK, fg=ACCENT_GOLD).grid(row=0, column=0, sticky="e", padx=15, pady=10)
    label_total_val = tk.Label(frame_dashboard, text=f"${total_wealth}", font=("Courier New", 20, "bold"), bg=CARD_DARK, fg=ACCENT_GOLD)
    label_total_val.grid(row=0, column=1, sticky="w", padx=5)
    
    # 2. 歷史帳戶色彩池（動態分配顏色）
    colors = ["#a6e3a1", "#89b4fa", "#f9e2af", "#f5c2e7", "#94e2d5", "#fab387"]
    
    # 3. 用迴圈把 JSON 裡面所有的帳戶餘額撈出來，自動排隊印在畫面上！
    for i, (acc_name, value) in enumerate(data["balance"].items()):
        row_idx = i + 1
        color = colors[i % len(colors)]
        
        tk.Label(frame_dashboard, text=f"{acc_name} 目前餘額:", font=("Arial", 11), bg=CARD_DARK, fg=TEXT_LIGHT).grid(row=row_idx, column=0, sticky="e", padx=15, pady=5)
        lbl_val = tk.Label(frame_dashboard, text=f"${value}", font=("Courier New", 14, "bold"), bg=CARD_DARK, fg=color)
        lbl_val.grid(row=row_idx, column=1, sticky="w", padx=5)
        
    # 順便連動更新下拉選單的選項！
    update_option_menu()

def update_option_menu():
    # ─── 【安全防禦鎖】 ───
    # 檢查 acc_menu 元件是否已經在全域被建立出來。如果還沒，就先跳過，等 UI 蓋好再更新！
    if "acc_menu" not in globals():
        return
        
    menu = acc_menu["menu"]
    menu.delete(0, "end")
    for acc_name in data["balance"].keys():
        menu.add_command(label=acc_name, command=lambda v=acc_name: acc_var.set(v))
    menu.add_command(label="🔄 內部轉帳", command=lambda: acc_var.set("🔄 內部轉帳"))

def refresh_history_tree():
    global data
    data = load_data() 
    for item in tree.get_children():
        tree.delete(item)
        
    # 年度時間篩選
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

    for log in reversed(data["history"][-20:]): 
        if log['change'] > 0:
            change_str = f"+${log['change']}"
        else:
            change_str = f"-${abs(log['change'])}"
        tree.insert("", tk.END, values=(log['date'], log['account'], change_str, log['note']))

    draw_asset_pie_chart()

# ─── 【史詩進化：動態多向圓餅圖與垂直圖例】 ───
def draw_asset_pie_chart():
    canvas.delete("all")
    
    total_val = sum(max(0, v) for v in data["balance"].values()) # 排除負資產帳戶進行佔比計算
    
    if total_val <= 0:
        canvas.create_text(110, 110, text="目前尚無淨資產資料\n無法繪製佔比圖", fill=TEXT_MUTED, font=("Arial", 10), justify="center")
        return

    colors = ["#a6e3a1", "#89b4fa", "#f9e2af", "#f5c2e7", "#94e2d5", "#fab387"]
    current_start = 0
    start_y = 225
    # 1. 動態角度接力迴圈
    for i, (acc_name, value) in enumerate(data["balance"].items()):
        
        percent = value / total_val if total_val > 0 and value > 0 else 0
        angle = percent * 360
        color = colors[i % len(colors)]
        
        canvas.create_arc(20, 20, 200, 200, start=current_start, extent=angle, fill=color, outline=CARD_DARK, width=2)
        current_start += angle

    # 2. 聽從 PM 指揮的「自動排隊垂直圖例」進化版！
    
    
        percent_r = (value / total_val * 100) if total_val > 0 and value > 0 else 0
        
        # 每一個帳戶自動往下挪動 22 像素，永遠不撞車
        y_rect_top = start_y + (i * 22)
        y_text_center = y_rect_top + 6
        
        canvas.create_rectangle(20, y_rect_top, 32, y_rect_top + 12, fill=color, outline="")
        canvas.create_text(42, y_text_center, text=f"{acc_name} ({percent_r:.1f}%)", fill=TEXT_LIGHT, font=("Arial", 9), anchor="w")

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
        # 回原資料結構找對應歷史 log 進行安全補償
        for log in data["history"]:
            if log["date"] == log_date and log["account"] == log_account and log["change"] == log_change:
                if log_account == "Transfer":
                    # 轉帳逆向還原
                    f_acc = log.get("from")
                    t_acc = log.get("to")
                    if f_acc in data["balance"] and t_acc in data["balance"]:
                        data["balance"][f_acc] += log_change
                        data["balance"][t_acc] -= log_change
                else:
                    if log_account in data["balance"]:
                        data["balance"][log_account] -= log_change
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
root.title("Will's Wealth Manager Dynamic-Core v8.0")
root.geometry("780x680") 

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
tab1.columnconfigure(0, weight=1)
tab1.columnconfigure(1, weight=1)

tk.Label(tab1, text="FINANCE DASHBOARD", font=("Impact", 24), bg=CARD_DARK, fg=ACCENT_PURPLE).grid(row=0, column=0, columnspan=2, pady=20)

# 【神級改動】：動態看板專屬容器，裡面的標籤全由 JSON 決定
frame_dashboard = tk.Frame(tab1, bg=CARD_DARK)
frame_dashboard.grid(row=1, column=0, columnspan=2, pady=5)

# 初始化動態看板
update_balance_labels()

# 為了排版美觀，我們動態計算下一個元件的起始 row 索引
start_row = 10 

tk.Label(tab1, text=" ─── 記錄交易 (常規收支請用正負號判定) ─── ", fg=TEXT_MUTED, bg=CARD_DARK, font=("Arial", 10)).grid(row=start_row, column=0, columnspan=2, pady=15)

tk.Label(tab1, text="選擇類型/帳戶:", font=("Arial", 11), bg=CARD_DARK, fg=TEXT_LIGHT).grid(row=start_row+1, column=0, sticky="e", padx=15, pady=6)
acc_var = tk.StringVar()
acc_menu = tk.OptionMenu(tab1, acc_var, "") # 先留空，由 update_option_menu 動態注入
acc_menu.config(bg="#313244", fg=TEXT_LIGHT, highlightbackground=CARD_DARK, activebackground="#45475a", activeforeground=TEXT_LIGHT)
acc_menu["menu"].config(bg=CARD_DARK, fg=TEXT_LIGHT, activebackground=ACCENT_PURPLE)
acc_menu.grid(row=start_row+1, column=1, sticky="w", padx=5)

# 觸發一次選單更新，並設定預設值
update_option_menu()
if data["balance"]:
    acc_var.set(list(data["balance"].keys())[0])

tk.Label(tab1, text="交易金額:", font=("Arial", 11), bg=CARD_DARK, fg=TEXT_LIGHT).grid(row=start_row+2, column=0, sticky="e", padx=15, pady=6)
entry_amount = tk.Entry(tab1, font=("Arial", 12), bg="#313244", fg="#ffffff", insertbackground="white", bd=0, width=22)
entry_amount.grid(row=start_row+2, column=1, sticky="w", padx=5, ipady=4)

tk.Label(tab1, text="備註說明:", font=("Arial", 11), bg=CARD_DARK, fg=TEXT_LIGHT).grid(row=start_row+3, column=0, sticky="e", padx=15, pady=6)
entry_note = tk.Entry(tab1, font=("Arial", 12), bg="#313244", fg="#ffffff", insertbackground="white", bd=0, width=22)
entry_note.grid(row=start_row+3, column=1, sticky="w", padx=5, ipady=4)

btn_submit = tk.Button(tab1, text="確認送出並儲存", command=handle_submit, bg=ACCENT_PURPLE, fg=BG_DARK, activebackground="#b4befe", font=("Arial", 12, "bold"), width=22, bd=0, cursor="hand2")
btn_submit.grid(row=start_row+4, column=0, columnspan=2, pady=20)


# ----------------- 分頁二：歷史報表與圖表雙拼介面 -----------------
frame_left = tk.Frame(tab2, bg=CARD_DARK)
frame_left.pack(side="left", fill="both", expand=True, padx=(10, 5), pady=10)

frame_right = tk.Frame(tab2, bg=CARD_DARK)
frame_right.pack(side="right", fill="both", padx=(5, 10), pady=10)

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

tk.Label(frame_right, text="目前資產分佈佔比", font=("Arial", 12, "bold"), bg=CARD_DARK, fg=ACCENT_GOLD).pack(pady=8)

canvas = tk.Canvas(frame_right, width=220, height=380, bg=CARD_DARK, highlightthickness=0) # 加高畫布以容納多個垂直圖例
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