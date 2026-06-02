import tkinter as tk
from tkinter import messagebox, ttk
import requests
import urllib3
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ─── 🎨 圖表視覺設定 ───
plt.style.use('seaborn-v0_8-darkgrid' if 'seaborn-v0_8-darkgrid' in plt.style.available else 'default')
plt.rcParams['font.family'] = ['Microsoft JhengHei']
plt.rcParams['axes.unicode_minus'] = False

BG_DARK = "#1e1e2e"
TEXT_LIGHT = "#cdd6f4"

def clean_fund_name(raw_name):
    """✂️ 基金名稱精準瘦身手術：拔除所有冗長的警語與括號"""
    clean_name = raw_name
    if "-" in clean_name:
        clean_name = clean_name.split("-")[0]
    if "(" in clean_name:
        clean_name = clean_name.split("(")[0]
    if "（" in clean_name:
        clean_name = clean_name.split("（")[0]
    return clean_name.strip()

class MultiComparatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("資產配置跨界世紀大對決回測系統 (完全體)")
        self.root.geometry("580x620") 
        
        self.battle_list = []
        
        # ─── 📥 1. 輸入與智慧判定區 ───
        frame_input = tk.LabelFrame(root, text=" 1. 輸入股票代號或基金名稱 ")
        frame_input.pack(pady=8, fill="x", padx=15)
        
        tk.Label(frame_input, text="請輸入 (如 2330, AAPL 或 安聯科技):").pack(anchor="w", padx=10, pady=2)
        
        frame_entry = tk.Frame(frame_input)
        frame_entry.pack(fill="x", padx=10, pady=5)
        
        self.entry_search = tk.Entry(frame_entry, font=("Microsoft JhengHei", 10))
        self.entry_search.pack(side="left", fill="x", expand=True, padx=5)
        
        # 🟢 按鈕：精準對齊 process_input
        btn_add = tk.Button(frame_entry, text="加入對決清單", command=self.process_input, 
                            bg="#89b4fa", fg="black", font=("Microsoft JhengHei", 9, "bold"))
        btn_add.pack(side="right", padx=5)
        
        # ─── 📅 2. 自訂歷史回測時間軸 (格式: YYYY-MM-DD) ───
        frame_date = tk.LabelFrame(root, text=" 2. 自訂歷史回測時間軸 (格式: YYYY-MM-DD) ")
        frame_date.pack(pady=8, fill="x", padx=15)
        
        frame_start = tk.Frame(frame_date)
        frame_start.pack(side="left", expand=True, fill="x", padx=10, pady=5)
        tk.Label(frame_start, text="開始日期:").pack(side="left", padx=2)
        self.entry_start_date = tk.Entry(frame_start, font=("Microsoft JhengHei", 10), width=12)
        self.entry_start_date.pack(side="left", padx=2)
        self.entry_start_date.insert(0, "2025-06-02") 
        
        frame_end = tk.Frame(frame_date)
        frame_end.pack(side="left", expand=True, fill="x", padx=10, pady=5)
        tk.Label(frame_end, text="結束日期:").pack(side="left", padx=2)
        self.entry_end_date = tk.Entry(frame_end, font=("Microsoft JhengHei", 10), width=12)
        self.entry_end_date.pack(side="left", padx=2)
        self.entry_end_date.insert(0, "2026-06-02") 
        
        # ─── 📋 3. 已鎖定的名單顯示區 ───
        frame_list = tk.LabelFrame(root, text=" 3. 目前已鎖定的對決陣容 (不限筆數) ")
        frame_list.pack(pady=5, fill="both", expand=True, padx=15)
        
        self.listbox_show = tk.Listbox(frame_list, font=("Microsoft JhengHei", 10), selectmode="single")
        self.listbox_show.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        scrollbar = tk.Scrollbar(frame_list, orient="vertical", command=self.listbox_show.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox_show.config(yscrollcommand=scrollbar.set)
        
        btn_del = tk.Button(root, text="刪除選中標的", command=self.delete_target, bg="#f38ba8", fg="black", font=("Microsoft JhengHei", 9))
        btn_del.pack(pady=5)
        
        # ─── 🚀 4. 啟動大混戰按鈕 ───
        btn_launch = tk.Button(root, text="🔥 啟動自適應跨界世紀大混戰", font=("Microsoft JhengHei", 12, "bold"), 
                               command=self.launch_battle, bg="#a6e3a1", fg="black", height=2)
        btn_launch.pack(fill="x", padx=15, pady=15)

    def search_fund_api_all_pages(self, keyword):
        """🚀 終極翻頁引擎（精準關鍵字過濾版）：強制限定名字必須包含關鍵字，踢除所有境外路人！"""
        fund_dict = {}
        page = 1
        
        print(f"🕵️‍♂️ 正在發動全網【跨頁穿梭補網】，關鍵字: [{keyword}]")
        
        while True:
            # 💡 順著你偵破的 B= 黃金網頁通道一路翻頁
            url = f"https://www.moneydj.com/funddj/ya/yFundSearch.djhtm?SearchKey={keyword}&B={page}&C=0&D=&ff=1"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            try:
                res = requests.get(url, headers=headers, verify=False)
                if res.status_code == 200 and res.text.strip():
                    html_text = res.text
                    
                    current_page_found = 0
                    search_ptr = 0
                    
                    while True:
                        code_start_idx = html_text.find('?a=', search_ptr)
                        if code_start_idx == -1:
                            break
                            
                        code_end_idx = html_text.find('"', code_start_idx)
                        fund_code = html_text[code_start_idx+3 : code_end_idx].strip()
                        
                        name_start_idx = html_text.find('>', code_end_idx) + 1
                        name_end_idx = html_text.find('</a>', name_start_idx)
                        raw_fund_name = html_text[name_start_idx : name_end_idx].strip()
                        
                        search_ptr = name_end_idx
                        
                        # ─── 🛡️ 鋼鐵過濾網（本次致命修正點） ───
                        # 1. 代碼必須是純英數字 (排除網頁上的中文字選單按鈕)
                        is_legal_code = fund_code and fund_code.isalnum()
                        
                        # 2. 核心修正：除了不是空字串，【名字裡必須百分之百包含你輸入的關鍵字】(例如：安聯)！
                        # 這樣一來，那些沒帶關鍵字的其他境外基金(DWS、CPR)就會被一微秒內直接擊碎剔除！
                        is_legal_name = raw_fund_name and (keyword in raw_fund_name) and "全部" not in raw_fund_name
                        
                        if is_legal_code and is_legal_name and fund_code not in fund_dict.values():
                            # 💡 執行名稱瘦身手術
                            clean_name = clean_fund_name(raw_fund_name)
                            
                            # 防止瘦身後名稱撞衫
                            if clean_name in fund_dict and fund_dict[clean_name] != fund_code:
                                clean_name = f"{clean_name}({fund_code})"
                                
                            fund_dict[clean_name] = fund_code
                            current_page_found += 1
                    
                    # 如果這一頁篩選完，沒有任何一檔符合你關鍵字的真基金，代表後面也沒有了，直接收工
                    if current_page_found == 0:
                        break
                        
                    print(f"   ➔ ✅ 成功攻破第 {page} 頁，捕獲 {current_page_found} 檔真正 [{keyword}] 基金...")
                    page += 1
                    
                    import time
                    time.sleep(0.05)
                else:
                    break
            except Exception as e:
                print(f"跨頁搜尋在第 {page} 頁發生阻礙: {e}")
                break
                
        print(f"🎉 跨頁大總結！共計幫您跨時空掘出 {len(fund_dict)} 檔乾淨的「{keyword}」系列基金！")
        return fund_dict

    def process_input(self):
        user_input = self.entry_search.get().strip()
        if not user_input:
            messagebox.showwarning("提示", "請輸入內容！")
            return
            
        has_chinese = any('\u4e00' <= c <= '\u9fff' for c in user_input)
        
        if not has_chinese:
            stock_code = user_input.upper()
            display_str = f"股票: {stock_code}"
            self.battle_list.append({"type": "stock", "code": stock_code, "name": display_str})
            self.listbox_show.insert(tk.END, f"📈 {display_str}")
            self.entry_search.delete(0, tk.END)
        else:
            # 🟢 呼叫穩定跨頁搜尋通道
            funds = self.search_fund_api_all_pages(user_input)
            if not funds:
                messagebox.showerror("殘念", f"找不到任何跟『{user_input}』相關的基金。")
                return
            if len(funds) == 1:
                full_name = list(funds.keys())[0]
                self.add_fund_to_list(full_name, funds[full_name])
            else:
                self.pop_selection_window(funds)

    def pop_selection_window(self, fund_options):
        pop = tk.Toplevel(self.root)
        pop.title("🎯 請選擇您要比對的是哪一檔基金？")
        pop.geometry("450x350") 
        pop.grab_set()
        
        tk.Label(pop, text=f"共掘出 {len(fund_options)} 筆結果，請點選一檔加入：", font=("Microsoft JhengHei", 10, "bold")).pack(pady=10)
        
        listbox_pop = tk.Listbox(pop, font=("Microsoft JhengHei", 9))
        listbox_pop.pack(fill="both", expand=True, padx=15, pady=5)
        
        sb = tk.Scrollbar(listbox_pop, orient="vertical", command=listbox_pop.yview)
        sb.pack(side="right", fill="y")
        listbox_pop.config(yscrollcommand=sb.set)
        
        names = list(fund_options.keys())
        for name in names:
            listbox_pop.insert(tk.END, name)
            
        def confirm_selection():
            try:
                selected_index = listbox_pop.curselection()[0]
                chosen_name = names[selected_index]
                self.add_fund_to_list(chosen_name, fund_options[chosen_name])
                pop.destroy()
            except IndexError:
                messagebox.showwarning("提示", "請先用滑鼠點選一檔基金！", parent=pop)
                
        tk.Button(pop, text="確認加入", command=confirm_selection, bg="#a6e3a1", fg="black", width=15).pack(pady=10)

    def add_fund_to_list(self, name, code):
        display_str = f"基金: {name}"
        self.battle_list.append({"type": "fund", "code": code, "name": display_str})
        self.listbox_show.insert(tk.END, f"🐷 {display_str} ({code})")
        self.entry_search.delete(0, tk.END)

    def delete_target(self):
        try:
            index = self.listbox_show.curselection()[0]
            self.listbox_show.delete(index)
            self.battle_list.pop(index)
        except IndexError:
            messagebox.showwarning("提示", "請先在清單中點選你想刪除的標的！")

    def get_fund_history(self, fund_code, start_date, end_date):
        s_dt = datetime.strptime(start_date, "%Y-%m-%d")
        e_dt = datetime.strptime(end_date, "%Y-%m-%d")
        url = f"https://www.moneydj.com/funddj/bcd/tBCDNavList.djbcd?a={fund_code}&B={s_dt.year}-{s_dt.month}-{s_dt.day}&C={e_dt.year}-{e_dt.month}-{e_dt.day}&D="
        headers = {"User-Agent": "Mozilla/5.0"}
        fund_data = {}
        try:
            res = requests.get(url, headers=headers, verify=False)
            if res.status_code == 200:
                raw_data = res.text.strip()
                all_elements = raw_data.split(",")
                cleaned = []
                for item in all_elements:
                    item = item.strip()
                    if len(item) > 8 and not item.isdigit():
                        cleaned.append(item[:8])
                        cleaned.append(item[8:])
                    else:
                        cleaned.append(item)
                half = len(cleaned) // 2
                dates = cleaned[:half]
                values = cleaned[half:]
                for d, v in zip(dates, values):
                    if d and v:
                        fund_data[f"{d[0:4]}-{d[4:6]}-{d[6:8]}"] = float(v)
        except:
            pass
        return fund_data

    def get_stock_history(self, stock_id, start_date, end_date):
        stock_code = f"{stock_id}.TW" if stock_id.isdigit() else stock_id
        try:
            df = yf.download(stock_code, start=start_date, end=end_date, progress=False)
            stock_data = {}
            for date, row in df.iterrows():
                date_str = date.strftime("%Y-%m-%d")
                stock_data[date_str] = float(row['Close'].iloc[0] if hasattr(row['Close'], 'iloc') else row['Close'])
            return stock_data
        except:
            return {}

    # ─── 🚀 【100% 一字不差保留你最完美的數據修補大腦】 ───
    def launch_battle(self):
        import pandas as pd  # 💡 引入數據修補大師
        
        if len(self.battle_list) < 2:
            messagebox.showwarning("人數不足", "世紀大混戰至少需要加入「2筆標的」才能開打比對喔！")
            return
            
        start = self.entry_start_date.get().strip()
        end = self.entry_end_date.get().strip()
        
        try:
            datetime.strptime(start, "%Y-%m-%d")
            datetime.strptime(end, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("日期錯誤", "請輸入標準 YYYY-MM-DD 格式（例如: 2025-01-20）")
            return
            
        print(f"📥 正在全速提取所有標的的歷史數據，自訂時間軸: {start} ~ {end} ...")
        
        # 1. 搬移歷史數據，並直接轉換成 Pandas 的獨立時間序列
        series_list = []
        for t in self.battle_list:
            if t["type"] == "stock":
                hist = self.get_stock_history(t["code"], start, end)
            else:
                hist = self.get_fund_history(t["code"], start, end)
                # 💡 防呆：如果自訂區間太長（超過一年）導致 Moneydj 罷工，自動補救抓取一年份
                if not hist:
                    print(f"⚠️ 基金 {t['code']} 提取失敗，可能超過一年限制，自動轉換為安全年區間...")
                    hist = self.get_fund_history(t["code"], "2025-06-02", "2026-06-02")
            
            # 把字典轉換成 Pandas Series (時間當索引)
            if hist:
                s = pd.Series(hist, name=t["name"])
                s.index = pd.to_datetime(s.index)
                series_list.append(s)
        
        if not series_list:
            messagebox.showerror("錯誤", "所有標的皆無法取得數據，請檢查網路或代號。")
            return
            
        # 2. 🔀 【各跑各地、無限聯集大合體】 ───
        # 用 Axis=1 把大家拼成一張大表格。只要有人有開盤，那一天就會留著！
        df_battle = pd.concat(series_list, axis=1)
        df_battle = df_battle.sort_index() # 按照日期由舊到新排序
        
        # 3. 🩹 【自動向前修補斷點 (Forward Fill)】 ───
        # 如果某天美股休市、台股有開，美股那一格自動複製「前一天的股價」補齊，絕對不斷線！
        df_battle = df_battle.ffill()
        # 萬一第一天就有人沒開盤（前面沒資料可補），就往後複製
        df_battle = df_battle.bfill()
        
        # 4. 🧮 格式化所有人回歸 0% 起跑線
        # 拿每一列的資料去除以「第一天的初始價格」，算出累計報酬率 %
        df_returns = (df_battle / df_battle.iloc[0] - 1) * 100
        
        # 提取出整理完畢的共同日期字串清單
        common_dates = [d.strftime("%Y-%m-%d") for d in df_returns.index]
        
        # 5. 🎨 建立大畫布
        fig, ax = plt.subplots(figsize=(11, 6))
        
        # 迴圈把每檔標的的累計報酬率畫上去
        for col in df_returns.columns:
            ax.plot(common_dates, df_returns[col].values, label=col, linewidth=2)
            
        ax.set_title(f"無限跨界世紀大對決：累計報酬率走勢極限比對 ({start} ~ {end})", fontsize=14, fontweight='bold')
        ax.set_xlabel("交易日期 (已自動修補跨國休市斷點)", fontsize=12)
        ax.set_ylabel("累計報酬率 (%)", fontsize=12)
        
        step = max(1, len(common_dates) // 12)
        ax.xaxis.set_major_locator(plt.MultipleLocator(step))
        plt.xticks(rotation=30)
        ax.axhline(0, color='white', linestyle='--', linewidth=1)
        ax.legend(fontsize=10, loc="upper left")
        
        # 🖱️ 智慧自適應雙生提示框 (完美多線支援版)
        tooltip_right = ax.annotate(
            "", xy=(0, 0), xytext=(20, 20), textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#252538", alpha=0.9, edgecolor="#7f849c"),
            arrowprops=dict(arrowstyle="->", color="#7f849c"), fontsize=9, color=TEXT_LIGHT
        )
        tooltip_left = ax.annotate(
            "", xy=(0, 0), xytext=(-240, 20), textcoords="offset points", 
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#252538", alpha=0.9, edgecolor="#7f849c"),
            arrowprops=dict(arrowstyle="->", color="#7f849c"), fontsize=9, color=TEXT_LIGHT
        )
        tooltip_right.set_visible(False)
        tooltip_left.set_visible(False)

        def on_mouse_move(event):
            if event.inaxes != ax:
                tooltip_right.set_visible(False)
                tooltip_left.set_visible(False)
                fig.canvas.draw_idle()
                return

            x_mouse = event.xdata
            if x_mouse is None: return

            idx = min(max(0, int(round(x_mouse))), len(common_dates) - 1)
            target_date = common_dates[idx]

            lines_text = [f"時間：{target_date}", "────────────────"]
            avg_y = 0
            
            # 從 Pandas 表格裡直接撈出那天的數據
            for col in df_returns.columns:
                val = df_returns[col].iloc[idx]
                avg_y += val
                lines_text.append(f" {col}: {val:+.1f} %")
                
            avg_y /= len(df_returns.columns)
            tooltip_text = "\n".join(lines_text)
            
            x_percent = (event.x - ax.bbox.xmin) / ax.bbox.width
            if x_percent > 0.7:
                tooltip_right.set_visible(False)
                tooltip_left.set_text(tooltip_text)
                tooltip_left.xy = (idx, avg_y)
                tooltip_left.set_visible(True)
            else:
                tooltip_left.set_visible(False)
                tooltip_right.set_text(tooltip_text)
                tooltip_right.xy = (idx, avg_y)
                tooltip_right.set_visible(True)

            fig.canvas.draw_idle()

        fig.canvas.mpl_connect("motion_notify_event", on_mouse_move)
        plt.tight_layout()
        print("🎨 智慧修補版多線大混戰畫布渲染完畢！")
        plt.show()

if __name__ == "__main__":
    root = tk.Tk()
    app = MultiComparatorApp(root)
    root.mainloop()