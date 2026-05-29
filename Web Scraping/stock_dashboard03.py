import requests
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import csv       # 📥 全新引入：CSV 檔案紀錄官
import os        # 📥 全新引入：作業系統工具（用來檢查檔案存不存在）
from datetime import datetime # 📥 全新引入：時間戳記大師

# ─── 💅 【暗黑極簡風 + 漲跌色票設定】 ───
BG_DARK = "#1e1e2e"
CARD_DARK = "#252538"
TEXT_LIGHT = "#cdd6f4"
TEXT_MUTED = "#7f849c"
ACCENT_BLUE = "#89b4fa"
TREND_UP = "#f38ba8"
TREND_DOWN = "#a6e3a1"

# ─── 💾 【全新登場：自動數據存檔密室】 ───
def save_to_database(code, name, price):
    """把抓到的股價，蓋上時間戳記，整整齊齊地寫入 stock_history.csv 檔案中"""
    file_name = "stock_history.csv"
    
    # 1. 抓取當下的精準時間，格式化成：2026-05-29 14:30:15
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 2. 檢查這個 csv 檔案以前是不是就存在了？
    # 如果檔案是第一次建立，我們必須先幫它寫入「表格欄位大標題」！
    file_exists = os.path.exists(file_name)
    
    # 3. 啟動 Python 的檔案寫入模式 (a 代表 append，意思是「在檔案最尾巴一直加字，不覆蓋舊資料」)
    # encoding="utf-8-sig" 是最高級的設定，能確保你用 Excel 點開檔案看中文時，絕對不變亂碼！
    with open(file_name, mode="a", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        
        # 如果是新檔案，先餵它欄位標頭
        if not file_exists:
            writer.writerow(["紀錄時間", "股票代碼", "股票名稱", "即時股價"])
            
        # 正式把這一筆珍貴的數據塞進去！
        writer.writerow([current_time, code, name, f"{price} 元"])
    print(f"💾 數據庫安全存檔成功 ➔ [{current_time}] {name}: ${price}")

# ─── 🧠 【爬蟲大腦函數】 ───
def fetch_stock_price(code):
    url = f"https://tw.stock.yahoo.com/quote/{code}.TW"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            
            price_tag = soup.find("span", class_="Fz(32px)")
            name_tag = soup.find("h1", class_="C($c-link-text)") # 維持你修正後最精準的方法！
            
            if price_tag and name_tag:
                stock_name = name_tag.text.strip()
                price = price_tag.text.strip()
                
                classes = price_tag.get("class", [])
                classes_str = "".join(classes)
                
                status = "even"
                if "trend-up" in classes_str:
                    status = "up"
                elif "trend-down" in classes_str:
                    status = "down"
                    
                return stock_name, price, status
    except:
        pass
    return "未知股票", "N/A", "even"

# ─── 🎮 【UI 互動邏輯控制中心】 ───
def add_stock_event():
    code = entry_code.get().strip()
    if not code:
        messagebox.showwarning("提示", "請輸入股票代號！")
        return
    
    for child in tree.get_children():
        if str(tree.item(child)["values"][0]) == str(code):
            messagebox.showinfo("提示", f"股票 [{code}] 已經在監控清單中囉！")
            entry_code.delete(0, tk.END)
            return
            
    threading.Thread(target=async_crawl_task, args=(code,), daemon=True).start()
    entry_code.delete(0, tk.END)

def async_crawl_task(code):
    stock_name, price, status = fetch_stock_price(code)
    if price == "N/A":
        messagebox.showerror("錯誤", f"無法取得代號 [{code}] 的資料！")
        return
        
    tree.insert("", "end", values=(code, stock_name, f"${price} 元"), tags=(status,))
    
    # 🚀 【新增：新增股票成功時，立刻存檔一次！】
    save_to_database(code, stock_name, price)

# 🔄 自動更新計時器
def auto_refresh_loop():
    print("🔄 自動更新計時器觸發：開始洗牌全場股價並同步寫入資料庫...")
    all_rows = tree.get_children()
    
    for row in all_rows:
        row_data = tree.item(row)["values"]
        stock_code = row_data[0]
        
        def refresh_single_stock(r_id, code):
            s_name, new_price, status = fetch_stock_price(code)
            tree.item(r_id, values=(code, s_name, f"${new_price} 元"), tags=(status,))
            
            # 🚀 【新增：每 15 秒自動刷新完，分身順手把最新價格寫入 CSV 存檔！】
            if new_price != "N/A":
                save_to_database(code, s_name, new_price)
            
        threading.Thread(target=refresh_single_stock, args=(row, stock_code), daemon=True).start()

    root.after(15000, auto_refresh_loop)

# ─── 🖥️ 【Tkinter 主畫面大佈局】 ───
root = tk.Tk()
root.title("個人股市大數據監控儀表板 v3.0")
root.geometry("600x400")
root.configure(bg=BG_DARK)

# 左邊控制卡片區
frame_left = tk.Frame(root, bg=CARD_DARK, bd=0)
frame_left.place(x=20, y=20, width=180, height=360)
tk.Label(frame_left, text="📊 股票監控", bg=CARD_DARK, fg=TEXT_LIGHT, font=("微軟正黑體", 12, "bold")).pack(pady=15)
entry_code = tk.Entry(frame_left, bg=BG_DARK, fg=TEXT_LIGHT, bd=0, insertbackground=TEXT_LIGHT, font=("Arial", 12), justify="center")
entry_code.pack(pady=5, ipady=4, padx=15)
entry_code.bind("<Return>", lambda e: add_stock_event())
btn_add = tk.Button(frame_left, text="➕ 新增監控", bg=ACCENT_BLUE, fg=BG_DARK, bd=0, font=("微軟正黑體", 10, "bold"), command=add_stock_event)
btn_add.pack(pady=20, ipadx=10, ipady=3)

# 右邊數據看板區
frame_right = tk.Frame(root, bg=BG_DARK)
frame_right.place(x=220, y=20, width=360, height=360)

style = ttk.Style()
style.theme_use("default")
style.configure("Treeview", bg=CARD_DARK, fg=TEXT_LIGHT, fieldbackground=CARD_DARK, rowheight=30, borderwidth=0, font=("微軟正黑體", 10))
style.configure("Treeview.Heading", bg=BG_DARK, fg=TEXT_MUTED, borderwidth=0, font=("微軟正黑體", 10, "bold"))

tree = ttk.Treeview(frame_right, columns=("code", "name", "price"), show="headings", selectmode="browse")
tree.heading("code", text="股票代號")
tree.heading("name", text="股票名稱")
tree.heading("price", text="即時股價")
tree.column("code", width=80, anchor="center")
tree.column("name", width=140, anchor="center")
tree.column("price", width=120, anchor="center")
tree.pack(fill=tk.BOTH, expand=True)

tree.tag_configure("up", foreground=TREND_UP)
tree.tag_configure("down", foreground=TREND_DOWN)
tree.tag_configure("even", foreground=TEXT_LIGHT)

# 啟動自動鬧鐘
threading.Thread(target=async_crawl_task, args=("2330",), daemon=True).start()
root.after(5000, auto_refresh_loop)

root.mainloop()