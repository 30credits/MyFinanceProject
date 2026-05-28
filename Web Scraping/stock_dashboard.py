import requests
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import ttk, messagebox
import threading # 引入多執行緒「隱形分身」，防止爬蟲時介面卡死

# ─── 💅 【暗黑極簡風視覺設定】 ───
BG_DARK = "#1e1e2e"       # 宇宙深藍底色
CARD_DARK = "#252538"     # 卡片區塊色
TEXT_LIGHT = "#cdd6f4"    # 優雅白字
TEXT_MUTED = "#7f849c"    # 科技灰字
ACCENT_BLUE = "#89b4fa"   # 亮眼藍（按鈕）

# ─── 🧠 【核心爬蟲大腦函數】 ───
def fetch_stock_price(stock_code):
    """給它代號，它戴上面具去 Yahoo 抓股價，抓到就回傳，失敗就回傳 N/A"""
    url = f"https://tw.stock.yahoo.com/quote/{stock_code}.TW"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 嘗試抓取股價數字
            price_tag = soup.find("span", class_="Fz(32px)")
            # 嘗試抓取股票名稱（順便豐富介面！）
            name_tag = soup.find("h1", class_="C($c-link-text)")
            
            if price_tag and name_tag:
                # 剥殼剥乾淨，回傳 (股票名稱, 股價)
                return name_tag.text.strip(), price_tag.text.strip()
    except:
        pass
    return "未知股票", "N/A"

# ─── 🎮 【UI 互動邏輯控制中心】 ───
# ─── 🎮 【UI 互動邏輯控制中心（升級版）】 ───

def add_stock_event():
    """按下確認或 Enter 時觸發的點擊事件"""
    code = entry_code.get().strip()
    if not code:
        messagebox.showwarning("提示", "請輸入股票代號！")
        return
    
    # 派隱形分身去背景爬蟲，避免卡死
    threading.Thread(target=async_crawl_task, args=(code,), daemon=True).start()
    entry_code.delete(0, tk.END)

def async_crawl_task(code):
    """在背景默默運作的爬蟲分身任務"""
    stock_name, price = fetch_stock_price(code)
    if price == "N/A":
        messagebox.showerror("錯誤", f"無法取得代號 [{code}] 的資料！")
        return
        
    # 檢查表格裡是不是已經有這檔股票了？防止使用者重複重複新增！
    for child in tree.get_children():
        # 用 tree.item(child)["values"][0] 抓出每一列的第一欄（股票代號）
        if str(tree.item(child)["values"][0]) == str(code):
            # 如果已經存在，就更新它的股價，不要重複插一列新的
            tree.item(child, values=(code, stock_name, f"${price} 元"))
            return

    # 表格裡沒有，才插在最後面
    tree.insert("", "end", values=(code, stock_name, f"${price} 元"))


# 🔥 【全新登場：自動化定時刷新經理】 🔥
def auto_refresh_loop():
    """每隔 15 秒，自動把表格裡所有的股票重新去網路上爬一次最新價格！"""
    print("🔄 自動更新計時器觸發：開始洗牌全場股價...")
    
    # 1. 呼叫你最會的點名特技：tree.get_children() 沒收目前表格裡所有的「列代號」
    all_rows = tree.get_children()
    
    # 2. 用迴圈一列一列抓出來處理
    for row in all_rows:
        # 拿到這那一列的原始數據（代碼、名字、舊股價）
        row_data = tree.item(row)["values"]
        stock_code = row_data[0] # 拿到代號（例如 2330）
        
        # 3. 每一檔股票，都派一個單獨的隱形分身去背景爬最新股價！
        # 這樣就算有 10 檔股票，它們也會「同時出發」，1 秒鐘之內全部刷洗完畢，完全不卡頓！
        def refresh_single_stock(r_id, code):
            s_name, new_price = fetch_stock_price(code)
            # 爬完了，直接更新畫面上那一列的數值！
            tree.item(r_id, values=(code, s_name, f"${new_price} 元"))
            
        threading.Thread(target=refresh_single_stock, args=(row, stock_code), daemon=True).start()

    # 4. 🔴 【最核心的定時鬧鐘】 🔴
    # 事情做完後，在主視窗大腦裡重新設一個 15000 毫秒（15 秒）後的鬧鐘
    # 叫自己 15 秒後再回來執行一次這個 auto_refresh_loop 函數！
    root.after(15000, auto_refresh_loop)

# ─── 🖥️ 【Tkinter 主畫面大佈局】 ───
root = tk.Tk()
root.title("個人股市即時監控儀表板 v1.0")
root.geometry("600x400")
root.configure(bg=BG_DARK)

# 1. 左邊：控制卡片區（輸入與按鈕）
frame_left = tk.Frame(root, bg=CARD_DARK, bd=0)
frame_left.place(x=20, y=20, width=180, height=360)

tk.Label(frame_left, text="📊 股票監控", bg=CARD_DARK, fg=TEXT_LIGHT, font=("微軟正黑體", 12, "bold")).pack(pady=15)
tk.Label(frame_left, text="請輸入股票代號:", bg=CARD_DARK, fg=TEXT_MUTED, font=("微軟正黑體", 9)).pack(pady=5)

entry_code = tk.Entry(frame_left, bg=BG_DARK, fg=TEXT_LIGHT, bd=0, insertbackground=TEXT_LIGHT, font=("Arial", 12), justify="center")
entry_code.pack(pady=5, ipady=4, padx=15)
entry_code.bind("<Return>", lambda e: add_stock_event()) # 完美的 Enter 鍵接球監聽

btn_add = tk.Button(frame_left, text="➕ 新增監控", bg=ACCENT_BLUE, fg=BG_DARK, bd=0, font=("微軟正黑體", 10, "bold"), activebackground=TEXT_LIGHT, command=add_stock_event)
btn_add.pack(pady=20, ipadx=10, ipady=3)

# 2. 右邊：數據 Treeview 顯示看板區
frame_right = tk.Frame(root, bg=BG_DARK)
frame_right.place(x=220, y=20, width=360, height=360)

# 設定 ttk 表格元件的暗黑視覺樣式 (Style)
style = ttk.Style()
style.theme_use("default")
style.configure("Treeview", bg=CARD_DARK, fg=TEXT_LIGHT, fieldbackground=CARD_DARK, rowheight=30, borderwidth=0, font=("微軟正黑體", 10))
style.configure("Treeview.Heading", bg=BG_DARK, fg=TEXT_MUTED, borderwidth=0, font=("微軟正黑體", 10, "bold"))

# 建立表格樹狀元件，定義三個欄位
tree = ttk.Treeview(frame_right, columns=("code", "name", "price"), show="headings", selectmode="browse")
tree.heading("code", text="股票代號")
tree.heading("name", text="股票名稱")
tree.heading("price", text="即時股價")

# 設定欄位的寬度與置中對齊
tree.column("code", width=80, anchor="center")
tree.column("name", width=140, anchor="center")
tree.column("price", width=120, anchor="center")
tree.pack(fill=tk.BOTH, expand=True)

# 預設幫使用者塞入一檔台積電當作開機歡迎禮物！
threading.Thread(target=async_crawl_task, args=("2330",), daemon=True).start()

root.mainloop()