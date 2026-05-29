import requests
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import csv
import os
from datetime import datetime
import re

# ─── 💅 【暗黑極簡風 + 視覺色票】 ───
BG_DARK = "#1e1e2e"
CARD_DARK = "#252538"
TEXT_LIGHT = "#cdd6f4"
TEXT_MUTED = "#7f849c"
ACCENT_BLUE = "#89b4fa"
TREND_UP = "#f38ba8"
TREND_DOWN = "#a6e3a1"

# ─── 💾 【資料庫寫入：同步擴充欄位】 ───
def save_to_database(code, name, price, change, volume):
    file_name = "stock_history.csv"
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_exists = os.path.exists(file_name)
    
    with open(file_name, mode="a", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        if not file_exists:
            # 📥 欄位大擴充：加入漲跌幅與成交量
            writer.writerow(["紀錄時間", "股票代碼", "股票名稱", "即時股價", "漲跌幅", "成交量"])
        writer.writerow([current_time, code, name, f"{price} 元", change, volume])

# ─── 🧠 【滿血版：爬蟲大腦函數】 ───
def fetch_stock_price(code):
    """回傳 (名稱, 股價, 漲跌幅, 成交量, 狀態)"""
    url = f"https://tw.stock.yahoo.com/quote/{code}.TW"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 1. 抓取股價與名字（維持你親自 Debug 成功的鐵防線）
            price_tag = soup.find("span", class_="Fz(32px)")
            name_tag = soup.find("h1", class_="C($c-link-text)")
            
            # 2. 🕵️‍♂️ 【新挑戰：抓取漲跌幅數字】
            # Yahoo 的漲跌幅數字通常是用 Fz(20px) 標記
            change_tag = soup.find("span", class_="Fz(20px)")
            
            # 3. 🕵️‍♂️ 【新挑戰：抓取成交量】
            # 💡 密技：用 re.compile("成交量")，白話意思是：「只要網頁字串裡『包含』成交量三個字，不管前後有沒有空格換行，通通給我抓出來！」
            vol_title_tag = soup.find(string="成交量")
            volume = "N/A"

            if vol_title_tag:
                # 爬蟲密技：先往上找爸爸（大盒子），再從大盒子肚子裡找第一個 span 數字！
                vol_val_tag = vol_title_tag.find_previous("span", class_="Fz(16px)")
                if vol_val_tag:
                    volume = f"{vol_val_tag.text.strip()} 張"

            if price_tag and name_tag:
                stock_name = name_tag.text.strip()
                price = price_tag.text.strip()
                change = change_tag.text.strip() if change_tag else "0.00%"
                
                # 偵測漲跌顏色衣服
                classes = price_tag.get("class", [])
                classes_str = "".join(classes)
                
                status = "even"
                if "trend-up" in classes_str:
                    status = "up"
                    change = f"▲ {change}" # 加上漂亮的小三角形
                elif "trend-down" in classes_str:
                    status = "down"
                    change = f"▼ {change}"
                    
                return stock_name, price, change, volume, status
    except Exception as e:
        print(f"爬蟲大腦發生錯誤: {e}")
    return "未知股票", "N/A", "0.00%", "N/A", "even"

# ─── 🎮 【UI 互動邏輯控制中心】 ───
def add_stock_event():
    code = entry_code.get().strip()
    if not code:
        messagebox.showwarning("提示", "請輸入股票代號！")
        return
    
    # 雙重 str() 鐵壁防禦網
    for child in tree.get_children():
        if str(tree.item(child)["values"][0]) == str(code):
            messagebox.showinfo("提示", f"股票 [{code}] 已經在清單中。")
            entry_code.delete(0, tk.END)
            return
            
    threading.Thread(target=async_crawl_task, args=(code,), daemon=True).start()
    entry_code.delete(0, tk.END)

def async_crawl_task(code):
    # 迎回大擴充的 5 個數據項
    stock_name, price, change, volume, status = fetch_stock_price(code)
    if price == "N/A":
        messagebox.showerror("錯誤", f"無法取得代號 [{code}] 的資料！")
        return
        
    # 塞入表格（五個欄位統統對齊填滿）
    tree.insert("", "end", values=(code, stock_name, f"${price} 元", change, volume), tags=(status,))
    save_to_database(code, stock_name, price, change, volume)

# 🔄 自動更新計時器
def auto_refresh_loop():
    print("🔄 自動更新計時器觸發：全面刷新 5 大核心數據...")
    all_rows = tree.get_children()
    
    for row in all_rows:
        row_data = tree.item(row)["values"]
        stock_code = row_data[0]
        
        def refresh_single_stock(r_id, code):
            s_name, new_price, new_change, new_vol, status = fetch_stock_price(code)
            if new_price != "N/A":
                # 刷新畫面的 5 大欄位
                tree.item(r_id, values=(code, s_name, f"${new_price} 元", new_change, new_vol), tags=(status,))
                save_to_database(code, s_name, new_price, new_change, new_vol)
            
        threading.Thread(target=refresh_single_stock, args=(row, stock_code), daemon=True).start()

    root.after(15000, auto_refresh_loop)

# ─── 🖥️ 【Tkinter 主畫面大佈局】 ───
root = tk.Tk()
root.title("個人專業股市大數據儀表板 v4.0")
root.geometry("750x400") # 📥 寬度從 600 拉大到 750，因為欄位變多了！
root.configure(bg=BG_DARK)

# 左邊控制卡片區
frame_left = tk.Frame(root, bg=CARD_DARK, bd=0)
frame_left.place(x=20, y=20, width=180, height=360)
tk.Label(frame_left, text="📊 專業監控", bg=CARD_DARK, fg=TEXT_LIGHT, font=("微軟正黑體", 12, "bold")).pack(pady=15)
entry_code = tk.Entry(frame_left, bg=BG_DARK, fg=TEXT_LIGHT, bd=0, insertbackground=TEXT_LIGHT, font=("Arial", 12), justify="center")
entry_code.pack(pady=5, ipady=4, padx=15)
entry_code.bind("<Return>", lambda e: add_stock_event())
btn_add = tk.Button(frame_left, text="➕ 新增監控", bg=ACCENT_BLUE, fg=BG_DARK, bd=0, font=("微軟正黑體", 10, "bold"), command=add_stock_event)
btn_add.pack(pady=20, ipadx=10, ipady=3)

# 右邊數據看板區（同步拉大寬度）
frame_right = tk.Frame(root, bg=BG_DARK)
frame_right.place(x=220, y=20, width=800, height=360)

style = ttk.Style()
style.theme_use("default")
style.configure("Treeview", bg=CARD_DARK, fg=TEXT_LIGHT, fieldbackground=CARD_DARK, rowheight=30, borderwidth=0, font=("微軟正黑體", 10))
style.configure("Treeview.Heading", bg=BG_DARK, fg=TEXT_MUTED, borderwidth=0, font=("微軟正黑體", 10, "bold"))

# 📥 表格定義增加為 5 個欄位：("code", "name", "price", "change", "vol")
tree = ttk.Treeview(frame_right, columns=("code", "name", "price", "change", "volume"), show="headings", selectmode="browse")
tree.heading("code", text="股票代號")
tree.heading("name", text="股票名稱")
tree.heading("price", text="即時股價")
tree.heading("change", text="當日漲跌幅") # 📥 新增欄位
tree.heading("volume", text="今日成交量")    # 📥 新增欄位

# 調整各個欄位的寬度比例
tree.column("code", width=80, anchor="center")     # 股票代號
tree.column("name", width=120, anchor="center")    # 股票名稱
tree.column("price", width=120, anchor="center")    # 即時股價
tree.column("change", width=130, anchor="center")   # 當日漲跌幅（留空間給三角形 ▲▼）
tree.column("volume", width=150, anchor="center")      # 今日成交量（加大到 150，保證 86,055 張完美現形！）
tree.pack(fill=tk.BOTH, expand=True)

tree.tag_configure("up", foreground=TREND_UP)
tree.tag_configure("down", foreground=TREND_DOWN)
tree.tag_configure("even", foreground=TEXT_LIGHT)

# 啟動第一次載入
threading.Thread(target=async_crawl_task, args=("2330",), daemon=True).start()
root.after(5000, auto_refresh_loop)

root.mainloop()