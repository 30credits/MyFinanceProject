import requests
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import ttk, messagebox
import threading

# ─── 💅 【暗黑極簡風 + 漲跌色票設定】 ───
BG_DARK = "#1e1e2e"
CARD_DARK = "#252538"
TEXT_LIGHT = "#cdd6f4"
TEXT_MUTED = "#7f849c"
ACCENT_BLUE = "#89b4fa"

# 🔴 台灣股市專屬視覺色票
TREND_UP = "#f38ba8"     # 柔和紅（漲）
TREND_DOWN = "#a6e3a1"   # 柔和綠（跌）

# ─── 🧠 【升級版：爬蟲大腦函數】 ───
def fetch_stock_price(code):
    """回傳 (股票名稱, 股價, 漲跌狀態) 狀態可以是: 'up', 'down', 'even'"""
    url = f"https://tw.stock.yahoo.com/quote/{code}.TW"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            
            price_tag = soup.find("span", class_="Fz(32px)")
            name_tag = soup.find("h1", class_="C($c-link-text)") # 改用最穩固的方法 B：直接抓第一個 h1
            
            if price_tag and name_tag:
                stock_name = name_tag.text.strip()
                price = price_tag.text.strip()
                
                # 🕵️‍♂️ 【新增：偵測漲跌衣服】
                # 拿走這顆標籤身上所有的 class 衣服名字（會變成一個清單）
                classes = price_tag.get("class", [])
                classes_str = "".join(classes) # 把它們揉成一條字串好檢查
                
                status = "even" # 預設是平盤
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
    
    # 🛡️ 鐵壁防禦檢查（上次你親自 Debug 的精髓！）
    for child in tree.get_children():
        if str(tree.item(child)["values"][0]) == str(code):
            messagebox.showinfo("提示", f"股票 [{code}] 已經在監控清單中囉！")
            entry_code.delete(0, tk.END)
            return
            
    threading.Thread(target=async_crawl_task, args=(code,), daemon=True).start()
    entry_code.delete(0, tk.END)

def async_crawl_task(code):
    """在背景默默運作的爬蟲分身任務"""
    stock_name, price, status = fetch_stock_price(code) # 👈 迎回新夥伴 status
    if price == "N/A":
        messagebox.showerror("錯誤", f"無法取得代號 [{code}] 的資料！")
        return
        
    # 🚀 【新增：動態幫表格蓋上有顏色的蓋章 (tags)】
    # tree.insert 最後面可以加上 tags 參數，就像幫這列資料貼上一個分類標籤
    tree.insert("", "end", values=(code, stock_name, f"${price} 元"), tags=(status,))

# 🔄 自動更新計時器
def auto_refresh_loop():
    print("🔄 自動更新計時器觸發：開始洗牌全場股價與視覺色彩...")
    all_rows = tree.get_children()
    
    for row in all_rows:
        row_data = tree.item(row)["values"]
        stock_code = row_data[0]
        
        def refresh_single_stock(r_id, code):
            s_name, new_price, status = fetch_stock_price(code)
            # 更新數據的同時，順便把這列的 tags 標籤換掉！
            tree.item(r_id, values=(code, s_name, f"${new_price} 元"), tags=(status,))
            
        threading.Thread(target=refresh_single_stock, args=(row, stock_code), daemon=True).start()

    root.after(15000, auto_refresh_loop)

# ─── 🖥️ 【Tkinter 主畫面大佈局】 ───
root = tk.Tk()
root.title("個人股市即時監控儀表板 v2.0")
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

# 🎨 【全新魔法：定義 Tags 標籤對應的文字顏色】
# tree.tag_configure("標籤名", foreground="文字顏色")
tree.tag_configure("up", foreground=TREND_UP)     # 如果標籤是 up，這列的字自動變成紅色
tree.tag_configure("down", foreground=TREND_DOWN) # 如果標籤是 down，這列的字自動變成綠色
tree.tag_configure("even", foreground=TEXT_LIGHT) # 如果標籤是 even，維持高質感白字

# 啟動自動鬧鐘
threading.Thread(target=async_crawl_task, args=("2330",), daemon=True).start()
root.after(5000, auto_refresh_loop)

root.mainloop()