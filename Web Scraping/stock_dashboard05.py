import requests
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog # 📥 新增引入 simpledialog 彈窗工具
import threading
import csv
import os
from datetime import datetime
import pyttsx3 # 📥 全新引入：語音廣播大師

# ─── 💅 【暗黑極簡風設定】 ───
BG_DARK = "#1e1e2e"
CARD_DARK = "#252538"
TEXT_LIGHT = "#cdd6f4"
TEXT_MUTED = "#7f849c"
ACCENT_BLUE = "#89b4fa"
TREND_UP = "#f38ba8"
TREND_DOWN = "#a6e3a1"

# ─── 🔊 【初始化語音引擎】 ───
try:
    engine = pyttsx3.init()
    # 稍微放慢講話速度，聽起來比較專業
    engine.setProperty("rate", 160) 
except:
    engine = None

def speak_alarm(text):
    """用獨立執行緒播放語音，絕對不能卡住主畫面"""
    def target():
        if engine:
            engine.say(text)
            engine.runAndWait()
    threading.Thread(target=target, daemon=True).start()

# ─── 💾 【資料庫寫入（維持好習慣）】 ───
def save_to_database(code, name, price, change, volume):
    file_name = "stock_history.csv"
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_exists = os.path.exists(file_name)
    with open(file_name, mode="a", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["紀錄時間", "股票代碼", "股票名稱", "即時股價", "漲跌幅", "成交量"])
        writer.writerow([current_time, code, name, f"{price} 元", change, volume])

# ─── 🧠 【網頁爬蟲大腦（維持你親自 Debug 成功的黃金版）】 ───
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
            name_tag = soup.find("h1", class_="C($c-link-text)")
            change_tag = soup.find("span", class_="Fz(20px)")
            vol_title_tag = soup.find(string="成交量")
            
            volume = "N/A"
            if vol_title_tag:
                # 🎯 這是你上一次用肉搏精神親自校正出來的黃金爆頭槍！
                vol_val_tag = vol_title_tag.find_previous("span", class_="Fz(16px)")
                if vol_val_tag:
                    volume = f"{vol_val_tag.text.strip()} 張"

            if price_tag and name_tag:
                stock_name = name_tag.text.strip()
                price = price_tag.text.strip()
                change = change_tag.text.strip() if change_tag else "0.00%"
                
                classes = price_tag.get("class", [])
                classes_str = "".join(classes)
                status = "even"
                if "trend-up" in classes_str:
                    status = "up"
                    change = f"▲ {change}"
                elif "trend-down" in classes_str:
                    status = "down"
                    change = f"▼ {change}"
                    
                return stock_name, price, change, volume, status
    except:
        pass
    return "未知股票", "N/A", "0.00%", "N/A", "even"

# ─── 🎮 【UI 互動邏輯控制中心（右鍵警報功能大擴充）】 ───
def add_stock_event():
    code = entry_code.get().strip()
    if not code:
        messagebox.showwarning("提示", "請輸入股票代號！")
        return
    for child in tree.get_children():
        if str(tree.item(child)["values"][0]) == str(code):
            messagebox.showinfo("提示", f"股票 [{code}] 已經在清單中。")
            entry_code.delete(0, tk.END)
            return
    threading.Thread(target=async_crawl_task, args=(code,), daemon=True).start()
    entry_code.delete(0, tk.END)

def async_crawl_task(code):
    stock_name, price, change, volume, status = fetch_stock_price(code)
    if price == "N/A":
        messagebox.showerror("錯誤", f"無法取得代號 [{code}] 的資料！")
        return
    # 💡 欄位擴充：最尾巴預設加上一個 "未設定" 的警報目標欄位
    tree.insert("", "end", values=(code, stock_name, f"${price} 元", change, volume, "未設定"), tags=(status,))
    save_to_database(code, stock_name, price, change, volume)

def set_alarm_price():
    """跳出輸入視窗，讓使用者設定特定股票的警報目標價"""
    selected_item = tree.focus()
    if not selected_item:
        return
    
    row_data = tree.item(selected_item)["values"]
    stock_code = row_data[0]
    stock_name = row_data[1]
    
    # 📥 解鎖 Tkinter 特技：彈出一個輸入框，叫使用者輸入數字
    target_price = simpledialog.askfloat("設定警報", f"請輸入 [{stock_name}] 的警報觸發價格：\n(當即時股價低於或等於此價格時將觸發語音提示)")
    
    if target_price is not None:
        # 把使用者輸入的警報數字，寫回表格的最末端一欄（第 5 欄）
        tree.item(selected_item, values=(row_data[0], row_data[1], row_data[2], row_data[3], row_data[4], f"${target_price}"))
        messagebox.showinfo("成功", f"已成功為 {stock_name} 建立 ${target_price} 元的低價警報！")

def show_right_click_menu(event):
    selected_row = tree.identify_row(event.y)
    if selected_row:
        tree.selection_set(selected_row)
        right_click_menu.post(event.x_root, event.y_root)

def delete_selected_stock():
    selected_item = tree.focus()
    if selected_item:
        row_data = tree.item(selected_item)["values"]
        if messagebox.askyesno("確認", f"確定要移除 [{row_data[1]}] 嗎？"):
            tree.delete(selected_item)

# 🔄 【核心智慧：自動更新計時器 ＋ 警報比對中心】
def auto_refresh_loop():
    print("🔄 自動更新計時器觸發：全面洗牌股價並進行安全警報監聽...")
    all_rows = tree.get_children()
    
    for row in all_rows:
        row_data = tree.item(row)["values"]
        stock_code = row_data[0]
        # 抓出目前這檔股票以前有沒有設定過警報價（把裡面的 $ 拔掉轉成數字）
        old_alarm_str = str(row_data[5]).replace("$", "").strip()
        
        def refresh_single_stock(r_id, code, alarm_str):
            s_name, new_price, new_change, new_vol, status = fetch_stock_price(code)
            if new_price != "N/A":
                # 保持畫面上警報價格欄位（第 5 欄）不被洗掉
                display_alarm = f"${alarm_str}" if alarm_str != "未設定" else "未設定"
                tree.item(r_id, values=(code, s_name, f"${new_price} 元", new_change, new_vol, display_alarm), tags=(status,))
                save_to_database(code, s_name, new_price, new_change, new_vol)
                
                # 🧮 🚨 【世紀大對決：進行警報數學審判】 🚨
                if alarm_str != "未設定":
                    try:
                        current_p = float(new_price.replace(",", "")) # 把股價的千分位逗號擦掉轉成數字
                        alarm_p = float(alarm_str)
                        if alarm_p = 0:
                            return
                        elif current_p <= alarm_p:
                            # 🔥 條件成立！發動降維打擊：電腦開口說話、並跳出最嚴厲的警告！
                            alarm_msg = f"主人！注意！{s_name} 目前股價已跌到 {current_p} 元，低於您的設定價 {alarm_p} 元！"
                            print(f"🚨 警報大響：{alarm_msg}")
                            speak_alarm(alarm_msg)
                            messagebox.showwarning("⚠️ 價格警報觸發！", alarm_msg)
                    except Exception as e:
                        print(f"警報比對失敗: {e}")
            
        threading.Thread(target=refresh_single_stock, args=(row, stock_code, old_alarm_str), daemon=True).start()

    root.after(15000, auto_refresh_loop)

# ─── 🖥️ 【主畫面大佈局（同步拉大寬度）】 ───
root = tk.Tk()
root.title("個人智能AI股市監控儀表板 v5.0")
root.geometry("880x400") # 📥 寬度加大到 880，因為右邊多了一欄警報價！
root.configure(bg=BG_DARK)

frame_left = tk.Frame(root, bg=CARD_DARK, bd=0)
frame_left.place(x=20, y=20, width=180, height=360)
tk.Label(frame_left, text="📊 智能監控", bg=CARD_DARK, fg=TEXT_LIGHT, font=("微軟正黑體", 12, "bold")).pack(pady=15)
entry_code = tk.Entry(frame_left, bg=BG_DARK, fg=TEXT_LIGHT, bd=0, insertbackground=TEXT_LIGHT, font=("Arial", 12), justify="center")
entry_code.pack(pady=5, ipady=4, padx=15)
entry_code.bind("<Return>", lambda e: add_stock_event())
btn_add = tk.Button(frame_left, text="➕ 新增監控", bg=ACCENT_BLUE, fg=BG_DARK, bd=0, font=("微軟正黑體", 10, "bold"), command=add_stock_event)
btn_add.pack(pady=20, ipadx=10, ipady=3)

frame_right = tk.Frame(root, bg=BG_DARK)
frame_right.place(x=220, y=20, width=640, height=360) # 📥 看板區拉大到 640

style = ttk.Style()
style.theme_use("default")
style.configure("Treeview", bg=CARD_DARK, fg=TEXT_LIGHT, fieldbackground=CARD_DARK, rowheight=30, borderwidth=0, font=("微軟正黑體", 10))
style.configure("Treeview.Heading", bg=BG_DARK, fg=TEXT_MUTED, borderwidth=0, font=("微軟正黑體", 10, "bold"))

# 📥 表格定義增加為 6 個欄位，最後一個是 "alarm"
tree = ttk.Treeview(frame_right, columns=("code", "name", "price", "change", "vol", "alarm"), show="headings", selectmode="browse")
tree.heading("code", text="股票代號")
tree.heading("name", text="股票名稱")
tree.heading("price", text="即時股價")
tree.heading("change", text="當日漲跌幅")
tree.heading("vol", text="今日成交量")
tree.heading("alarm", text="💡 低價警報目標") # 📥 新增欄位

tree.column("code", width=70, anchor="center")
tree.column("name", width=110, anchor="center")
tree.column("price", width=100, anchor="center")
tree.column("change", width=110, anchor="center")
tree.column("vol", width=120, anchor="center")
tree.column("alarm", width=130, anchor="center") # 📥 新增欄位寬度
tree.pack(fill=tk.BOTH, expand=True)

tree.tag_configure("up", foreground=TREND_UP)
tree.tag_configure("down", foreground=TREND_DOWN)
tree.tag_configure("even", foreground=TEXT_LIGHT)

# ─── 🖱️ 【右鍵選單：雙重功能大進化】 ───
right_click_menu = tk.Menu(root, tearoff=0, bg=CARD_DARK, fg=TEXT_LIGHT, activebackground=ACCENT_BLUE, activeforeground=BG_DARK, bd=0)
# 📥 功能 A：設定警報
right_click_menu.add_command(label="🔔 設定低價語音警報", command=set_alarm_price)
right_click_menu.add_separator() # 畫一條好看的置中分隔線
# 功能 B：刪除股票
right_click_menu.add_command(label="❌ 刪除此股票監控", command=delete_selected_stock)

tree.bind("<Button-3>", show_right_click_menu)

# 啟動第一次載入
threading.Thread(target=async_crawl_task, args=("2330",), daemon=True).start()
root.after(5000, auto_refresh_loop)

root.mainloop()