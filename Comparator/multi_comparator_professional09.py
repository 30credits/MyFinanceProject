import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import requests
import urllib3
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import urllib.parse
import json
import os
import webbrowser  # 🌐 引入全自動網頁開啟核心外掛
from tkcalendar import Calendar
import tkinter as tk
from tkinter import ttk
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ─── 🎨 圖表視覺與介面色彩設定 ───
plt.style.use('seaborn-v0_8-darkgrid' if 'seaborn-v0_8-darkgrid' in plt.style.available else 'default')
plt.rcParams['font.family'] = ['Microsoft JhengHei']
plt.rcParams['axes.unicode_minus'] = False

BG_DARK = "#1e1e2e"
TEXT_LIGHT = "#cdd6f4"
HISTORY_FILE_MONEY = "portfolio_history.json"
HISTORY_FILE_PCT = "portfolio_history_pct.json"

def clean_fund_name(raw_name):
    """✂️ 基金名稱精準瘦身手術：拔除冗長警語，但死死保留 (資產代碼)"""
    fund_code = ""
    if " (" in raw_name and raw_name.endswith(")"):
        fund_code = raw_name.split(" (")[-1].replace(")", "").strip()
    
    clean_name = raw_name
    if " (" in clean_name: clean_name = clean_name.split(" (")[0]
    if "(" in clean_name: clean_name = clean_name.split("(")[0]
    if "（" in clean_name: clean_name = clean_name.split("（")[0]
    if "-" in clean_name: clean_name = clean_name.split("-")[0]
    
    clean_name = clean_name.strip()
    
    if fund_code:
        return f"{clean_name}({fund_code})"
    return clean_name

class MultiComparatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("多資產配置雙模式歷史回測系統 (現值版/比例版完全體)")
        self.root.geometry("650x760") 
        
        self.battle_list_money = []
        self.battle_list_pct = []
        
        # ─── 📅 1. 全域歷史回測時間軸 (兩個分頁共用) ───
        frame_date = tk.LabelFrame(root, text=" 1. 自訂歷史回測時間軸 (點擊欄位開啟日曆) ")
        frame_date.pack(pady=6, fill="x", padx=15)
        
        today_obj = datetime.now()
        one_year_ago_obj = today_obj - timedelta(days=365)
        today_str = today_obj.strftime("%Y-%m-%d")
        one_year_ago_str = one_year_ago_obj.strftime("%Y-%m-%d")
        
        frame_start = tk.Frame(frame_date)
        frame_start.pack(side="left", expand=True, fill="x", padx=10, pady=5)
        tk.Label(frame_start, text="開始日期:").pack(side="left", padx=2)
        self.entry_start_date = tk.Entry(frame_start, font=("Microsoft JhengHei", 10), width=12, readonlybackground="white")
        self.entry_start_date.pack(side="left", padx=2)
        self.entry_start_date.insert(0, one_year_ago_str) 
        self.entry_start_date.bind("<Button-1>", lambda event: self.pop_calendar(self.entry_start_date))
        
        frame_end = tk.Frame(frame_date)
        frame_end.pack(side="left", expand=True, fill="x", padx=10, pady=5)
        tk.Label(frame_end, text="結束日期:").pack(side="left", padx=2)
        self.entry_end_date = tk.Entry(frame_end, font=("Microsoft JhengHei", 10), width=12, readonlybackground="white")
        self.entry_end_date.pack(side="left", padx=2)
        self.entry_end_date.insert(0, today_str) 
        self.entry_end_date.bind("<Button-1>", lambda event: self.pop_calendar(self.entry_end_date))

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(pady=5, fill="both", expand=True, padx=15)
        
        self.tab_money = tk.Frame(self.notebook)
        self.tab_pct = tk.Frame(self.notebook)
        
        self.notebook.add(self.tab_money, text=" 💰 模式一：獨立資金現值版 ")
        self.notebook.add(self.tab_pct, text=" % 模式二：資產權重比例版 ")
        
        self.setup_money_tab()
        self.setup_pct_tab()
        
        self.load_history_notebook_money()
        self.load_history_notebook_pct()


    def setup_money_tab(self):
        frame_input = tk.LabelFrame(self.tab_money, text=" 2. 輸入標的與獨立投資金額 ")
        frame_input.pack(pady=6, fill="x", padx=10)
        
        frame_row1 = tk.Frame(frame_input)
        frame_row1.pack(fill="x", padx=10, pady=2)
        tk.Label(frame_row1, text="股票代號/基金名稱:").pack(side="left", padx=2)
        self.entry_search_money = tk.Entry(frame_row1, font=("Microsoft JhengHei", 10))
        self.entry_search_money.pack(side="left", fill="x", expand=True, padx=5)
        
        frame_row2 = tk.Frame(frame_input)
        frame_row2.pack(fill="x", padx=10, pady=5)
        tk.Label(frame_row2, text="此項目投入金額 ($):").pack(side="left", padx=2)
        self.entry_money_val = tk.Entry(frame_row2, font=("Microsoft JhengHei", 10, "bold"), width=15, fg="#228b22")
        self.entry_money_val.pack(side="left", padx=5)
        self.entry_money_val.insert(0, "1000000") 
        
        btn_add = tk.Button(frame_row2, text="加入投資組合", command=self.process_input_money, 
                            bg="#89b4fa", fg="black", font=("Microsoft JhengHei", 9, "bold"), width=12)
        btn_add.pack(side="right", padx=2)
        
        frame_list = tk.LabelFrame(self.tab_money, text=" 3. 目前投資組合配置 (雙擊名稱開基金網頁 / 雙擊金額原地修改) ")
        frame_list.pack(pady=5, fill="both", expand=True, padx=10)
        
        columns = ("name", "code", "money")
        self.tree_money = ttk.Treeview(frame_list, columns=columns, show="headings", selectmode="browse")
        self.tree_money.heading("name", text="資產名稱")
        self.tree_money.heading("code", text="資產代碼")
        self.tree_money.heading("money", text="分配投入金額 (元)")
        self.tree_money.column("name", width=240, anchor="w")
        self.tree_money.column("code", width=90, anchor="center")
        self.tree_money.column("money", width=130, anchor="e")
        self.tree_money.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        self.tree_money.bind("<Double-1>", self.on_tree_money_double_click)
        scrollbar = tk.Scrollbar(frame_list, orient="vertical", command=self.tree_money.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree_money.config(yscrollcommand=scrollbar.set)
        
        # ─── 🎛️ 建立底部控制工具列 (讓刪除按鈕與下拉選單優雅並排) ───
        frame_ctrl = tk.Frame(self.tab_money)
        frame_ctrl.pack(pady=10, fill="x", padx=10)
        
        # 1. 刪除按鈕靠左置中
        btn_del = tk.Button(frame_ctrl, text="❌ 刪除選中標的", command=self.delete_target_money, bg="#f38ba8", fg="black", font=("Microsoft JhengHei", 9), width=15)
        btn_del.pack(side="left", anchor="center")
        
        # 2. 下拉選單與提示字集體靠右排隊
        self.combo_fx_mode = ttk.Combobox(frame_ctrl, state="readonly", width=25, font=("Microsoft JhengHei", 10))
        self.combo_fx_mode["values"] = (
            "模式一：原幣別 (純市場報酬)",
            "模式二：台幣(考慮匯率)",
            "模式三：原幣別+台幣"
        )
        self.combo_fx_mode.current(1) 
        self.combo_fx_mode.pack(side="right", padx=(5, 0))
        
        lbl_fx_mode = tk.Label(frame_ctrl, text="匯率模式：", font=("Microsoft JhengHei", 9, "bold"))
        lbl_fx_mode.pack(side="right") 
        
        # ─── 🟩 3. 綠色執行按鈕沉底托高 ───
        btn_launch = tk.Button(self.tab_money, text="📊 執行模式一歷史績效回測", font=("Microsoft JhengHei", 12, "bold"), 
                               command=self.launch_battle_money, bg="#a6e3a1", fg="black", height=2)
        btn_launch.pack(fill="x", padx=10, pady=(0, 10))

    def setup_pct_tab(self):
        frame_total_money = tk.Frame(self.tab_pct, bg=BG_DARK)
        frame_total_money.pack(pady=6, fill="x", padx=10)
        tk.Label(frame_total_money, text="💰 總投資資金總額 (元):", font=("Microsoft JhengHei", 10, "bold"), fg=TEXT_LIGHT, bg=BG_DARK).pack(side="left", padx=10, pady=6)
        self.entry_total_principal = tk.Entry(frame_total_money, font=("Microsoft JhengHei", 10, "bold"), width=18, fg="#228b22")
        self.entry_total_principal.pack(side="left", padx=5)
        self.entry_total_principal.insert(0, "1000000")
        
        frame_input = tk.LabelFrame(self.tab_pct, text=" 2. 輸入標的與指定權重比例 ")
        frame_input.pack(pady=6, fill="x", padx=10)
        
        frame_row1 = tk.Frame(frame_input)
        frame_row1.pack(fill="x", padx=10, pady=2)
        tk.Label(frame_row1, text="股票代號/基金名稱:").pack(side="left", padx=2)
        self.entry_search_pct = tk.Entry(frame_row1, font=("Microsoft JhengHei", 10))
        self.entry_search_pct.pack(side="left", fill="x", expand=True, padx=5)
        
        frame_row2 = tk.Frame(frame_input)
        frame_row2.pack(fill="x", padx=10, pady=5)
        tk.Label(frame_row2, text="分配比例 (只需輸入數字，如20):").pack(side="left", padx=2)
        self.entry_pct_val = tk.Entry(frame_row2, font=("Microsoft JhengHei", 10, "bold"), width=10, fg="#228b22")
        self.entry_pct_val.pack(side="left", padx=5)
        self.entry_pct_val.insert(0, "20") 
        tk.Label(frame_row2, text="%").pack(side="left")
        
        btn_add = tk.Button(frame_row2, text="加入投資組合", command=self.process_input_pct, 
                            bg="#89b4fa", fg="black", font=("Microsoft JhengHei", 9, "bold"), width=12)
        btn_add.pack(side="right", padx=2)
        
        frame_list = tk.LabelFrame(self.tab_pct, text=" 3. 目前投資組合權重配置 (雙擊名稱開基金網頁 / 雙擊比例原地修改) ")
        frame_list.pack(pady=5, fill="both", expand=True, padx=10)
        
        columns = ("name", "code", "money")
        self.tree_pct = ttk.Treeview(frame_list, columns=columns, show="headings", selectmode="browse")
        self.tree_pct.heading("name", text="資產名稱")
        self.tree_pct.heading("code", text="資產代碼")
        self.tree_pct.heading("money", text="分配比例 (%)")
        self.tree_pct.column("name", width=240, anchor="w")
        self.tree_pct.column("code", width=90, anchor="center")
        self.tree_pct.column("money", width=130, anchor="e")
        self.tree_pct.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        self.tree_pct.bind("<Double-1>", self.on_tree_pct_double_click)
        scrollbar = tk.Scrollbar(frame_list, orient="vertical", command=self.tree_pct.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree_pct.config(yscrollcommand=scrollbar.set)
        
        # ─── 🎛️ 建立底部控制工具列 (分頁二：並排大改造版) ───
        frame_ctrl = tk.Frame(self.tab_pct)
        frame_ctrl.pack(pady=10, fill="x", padx=10)
        
        # 1. 刪除按鈕靠左置中
        btn_del = tk.Button(frame_ctrl, text="❌ 刪除選中標的", command=self.delete_target_pct, bg="#f38ba8", fg="black", font=("Microsoft JhengHei", 9), width=15)
        btn_del.pack(side="left", anchor="center")
        
        # 2. 下拉選單與提示字集體靠右排隊 (注意：這裡同樣綁定在分頁二的 self.tab_pct)
        self.combo_fx_mode_pct = ttk.Combobox(frame_ctrl, state="readonly", width=25, font=("Microsoft JhengHei", 10))
        self.combo_fx_mode_pct["values"] = (
            "模式一：原幣別 (純市場報酬)",
            "模式二：台幣(考慮匯率)",
            "模式三：原幣別+台幣"
        )
        self.combo_fx_mode_pct.current(1) 
        self.combo_fx_mode_pct.pack(side="right", padx=(5, 0))
        
        lbl_fx_mode_pct = tk.Label(frame_ctrl, text="匯率模式：", font=("Microsoft JhengHei", 9, "bold"))
        lbl_fx_mode_pct.pack(side="right") 
        
        # ─── 🟩 3. 綠色執行按鈕沉底托高 ───
        btn_launch = tk.Button(self.tab_pct, text="📊 執行模式二歷史績效回測", font=("Microsoft JhengHei", 12, "bold"), 
                               command=self.launch_battle_pct, bg="#a6e3a1", fg="black", height=2)
        btn_launch.pack(fill="x", padx=10, pady=(0, 10))

    def pop_calendar(self, target_entry):
        pop_cal = tk.Toplevel(self.root)
        pop_cal.title("選擇日期")
        pop_cal.geometry("280x250")
        pop_cal.grab_set()
        current_val = target_entry.get().strip()
        try:
            dt = datetime.strptime(current_val, "%Y-%m-%d")
            cal = Calendar(pop_cal, selectmode='day', year=dt.year, month=dt.month, day=dt.day, date_pattern='yyyy-mm-dd')
        except:
            cal = Calendar(pop_cal, selectmode='day', date_pattern='yyyy-mm-dd')
        cal.pack(fill="both", expand=True, padx=10, pady=10)
        def set_date():
            target_entry.delete(0, tk.END)
            target_entry.insert(0, cal.get_date())
            pop_cal.destroy()
        tk.Button(pop_cal, text="確定", command=set_date, bg="#a6e3a1", fg="black").pack(pady=5)

    def save_history_notebook_money(self):
        try:
            with open(HISTORY_FILE_MONEY, "w", encoding="utf-8") as f:
                json.dump(self.battle_list_money, f, ensure_ascii=False, indent=4)
        except Exception as e: print(f"現值版快取儲存失敗: {e}")

    def load_history_notebook_money(self):
        if os.path.exists(HISTORY_FILE_MONEY):
            try:
                with open(HISTORY_FILE_MONEY, "r", encoding="utf-8") as f:
                    self.battle_list_money = json.load(f)
                self.refresh_tree_money()
            except Exception as e: print(f"現值版讀取快取失敗: {e}")

    def refresh_tree_money(self):
        for item in self.tree_money.get_children(): self.tree_money.delete(item)
        for t in self.battle_list_money:
            self.tree_money.insert("", tk.END, values=(t["name"], t["code"], f"${t['money']:,.0f}"))

    def save_history_notebook_pct(self):
        try:
            with open(HISTORY_FILE_PCT, "w", encoding="utf-8") as f:
                json.dump(self.battle_list_pct, f, ensure_ascii=False, indent=4)
        except Exception as e: print(f"比例版快取儲存失敗: {e}")

    def load_history_notebook_pct(self):
        if os.path.exists(HISTORY_FILE_PCT):
            try:
                with open(HISTORY_FILE_PCT, "r", encoding="utf-8") as f:
                    self.battle_list_pct = json.load(f)
                self.refresh_tree_pct()
            except Exception as e: print(f"比例版讀取快取失敗: {e}")

    def refresh_tree_pct(self):
        for item in self.tree_pct.get_children(): self.tree_pct.delete(item)
        for t in self.battle_list_pct:
            self.tree_pct.insert("", tk.END, values=(t["name"], t["code"], f"{t['money']:.1f} %"))

    def search_fund_api_all_pages(self, keyword):
        fund_dict = {}
        page = 1
        print(f"🕵️‍♂️ 正在發動全網【跨頁穿梭補網】，關鍵字: [{keyword}]")
        
        last_found_count = 0
        no_change_strike = 0
        
        while True:
            url = f"https://www.moneydj.com/funddj/ya/yFundSearch.djhtm?a={urllib.parse.quote(keyword)}&B={page}&C=0&D=&ff=1"
            headers = {"User-Agent": "Mozilla/5.0"}
            try:
                res = requests.get(url, headers=headers, verify=False, timeout=5)
                if res.status_code == 200 and res.text.strip():
                    html_text = res.text
                    current_page_found = 0
                    search_ptr = 0
                    
                    while True:
                        code_start_idx = html_text.find('?a=', search_ptr)
                        if code_start_idx == -1: break
                        code_end_idx = html_text.find('"', code_start_idx)
                        fund_code = html_text[code_start_idx+3 : code_end_idx].strip()
                        name_start_idx = html_text.find('>', code_end_idx) + 1
                        name_end_idx = html_text.find('</a>', name_start_idx)
                        raw_fund_name = html_text[name_start_idx : name_end_idx].strip()
                        search_ptr = name_end_idx
                        
                        is_legal_code = fund_code and fund_code.isalnum()
                        is_legal_name = raw_fund_name and (keyword in raw_fund_name) and "全部" not in raw_fund_name
                        
                        if is_legal_code and is_legal_name:
                            full_display_name = f"{raw_fund_name} ({fund_code})"
                            if full_display_name not in fund_dict:
                                fund_dict[full_display_name] = fund_code
                                current_page_found += 1
                                
                    total_now = len(fund_dict)
                    if total_now == last_found_count:
                        no_change_strike += 1
                        if no_change_strike >= 2: 
                            print(f"🏁 數據已全數捕獲完畢，安全踩煞車。共掘出 {total_now} 檔標的。")
                            break
                    else:
                        no_change_strike = 0
                        
                    last_found_count = total_now
                    if current_page_found == 0 and page > 1: break
                        
                    print(f"   ➔ ✅ 成功攻破第 {page} 頁，累積捕獲 {total_now} 檔基金級別...")
                    page += 1
                    import time
                    time.sleep(0.05)
                    if page > 50: break
                else: break
            except Exception as e: 
                print(f"搜尋發生異常: {e}")
                break
        return fund_dict

    def process_input_money(self):
        user_input = self.entry_search_money.get().strip()
        user_money_raw = self.entry_money_val.get().strip()
        if not user_input:
            messagebox.showwarning("提示", "請輸入資產名稱或代碼！")
            return
        try:
            allocated_money = float(user_money_raw)
            if allocated_money <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("錯誤", "請輸入正確的投資金額！")
            return
            
        has_chinese = any('\u4e00' <= c <= '\u9fff' for c in user_input)
        if not has_chinese:
            stock_code = user_input.upper()
            display_str = f"股票: {stock_code}"
            try:
                is_taiwan_asset = stock_code[0].isdigit() if stock_code else False
                actual_code = f"{stock_code}.TW" if is_taiwan_asset else stock_code
                ticker = yf.Ticker(actual_code)
                long_name = ticker.info.get('longName') or ticker.info.get('shortName')
                if long_name:
                    if "Taiwan Semiconductor" in long_name or stock_code == "2330":
                        display_str = "股票: 台積電"
                    else: display_str = f"股票: {long_name}"
            except Exception as e: print(f"股票名稱查詢失敗: {e}")
                
            self.battle_list_money.append({"type": "stock", "code": stock_code, "name": display_str, "money": allocated_money})
            self.refresh_tree_money()
            self.entry_search_money.delete(0, tk.END)
            self.save_history_notebook_money()
        else:
            funds = self.search_fund_api_all_pages(user_input)
            if not funds:
                messagebox.showerror("殘念", f"找不到任何跟『{user_input}』相關的基金。")
                return
            if len(funds) == 1:
                full_name = list(funds.keys())[0]
                self.add_fund_to_list_money(full_name, funds[full_name], allocated_money)
            else: self.pop_selection_window_money(funds, allocated_money)

    def pop_selection_window_money(self, fund_options, allocated_money):
        pop = tk.Toplevel(self.root)
        pop.title("🎯 請選擇您要比對的是哪一檔基金？")
        pop.geometry("500x380")
        pop.grab_set()
        
        tk.Label(pop, text=f"共掘出 {len(fund_options)} 筆結果，請點選一檔加入：", font=("Microsoft JhengHei", 10, "bold")).pack(pady=10)
        listbox_pop = tk.Listbox(pop, font=("Microsoft JhengHei", 9))
        listbox_pop.pack(fill="both", expand=True, padx=15, pady=5)
        sb = tk.Scrollbar(listbox_pop, orient="vertical", command=listbox_pop.yview)
        sb.pack(side="right", fill="y")
        listbox_pop.config(yscrollcommand=sb.set)
        
        names = list(fund_options.keys())
        for name in names: listbox_pop.insert(tk.END, name)
            
        def confirm_selection():
            try:
                selected_index = listbox_pop.curselection()[0]
                chosen_full_name = names[selected_index]
                self.add_fund_to_list_money(chosen_full_name, fund_options[chosen_full_name], allocated_money)
                pop.destroy()
            except IndexError: 
                messagebox.showwarning("提示", "請先用滑鼠點選一檔基金！", parent=pop)
                
        tk.Button(pop, text="確認加入", command=confirm_selection, bg="#a6e3a1", fg="black", width=15).pack(pady=10)

    def add_fund_to_list_money(self, name, code, allocated_money):
        clean_name = clean_fund_name(name)
        if "(" in clean_name: clean_name = clean_name.split("(")[0]
            
        # 🕵️‍♂️ 雷達一號：鑑定幣別
        asset_currency = "美金"
        if any(kw in name for kw in ["台幣", "新台幣", "TWD", "NTD"]): asset_currency = "台幣"
        elif any(kw in name for kw in ["日圓", "日幣", "JPY"]): asset_currency = "日圓"
        elif any(kw in name for kw in ["人民幣", "CNY", "RMB"]): asset_currency = "人民幣"
        elif any(kw in name for kw in ["港幣", "港元", "HKD"]): asset_currency = "港幣"
        elif any(kw in name for kw in ["紐幣", "紐元", "NZD"]): asset_currency = "紐幣"
        elif any(kw in name for kw in ["澳幣", "AUD"]): asset_currency = "澳幣"
        elif any(kw in name for kw in ["南非幣", "ZAR"]): asset_currency = "南非幣"
        elif any(kw in name for kw in ["歐元", "EUR"]): asset_currency = "歐元"
            
        # 🕵️‍♂️ 雷達二號：根據名稱字眼初步判定是否為配息型
        is_dividend_type = False
        if any(kw in name for kw in ["月配", "季配", "配息", "穩定月收", "AM", "分派", "收類股"]):
            if "累積" not in name:  # 防禦：防止有些名字叫 "配息不滾回但此級別為累積型" 的特例
                is_dividend_type = True
                
        type_label = "配息現領" if is_dividend_type else "不配息"
        display_str = f"基金: {clean_name}({asset_currency}-{type_label})"
        
        self.battle_list_money.append({
            "type": "fund", 
            "code": code, 
            "name": display_str, 
            "full_name": name, 
            "money": allocated_money,
            "is_dividend": is_dividend_type # 👈 注入配息基因標籤
        })
        self.refresh_tree_money()
        self.entry_search_money.delete(0, tk.END)
        self.save_history_notebook_money()

    def delete_target_money(self):
        try:
            selected_item = self.tree_money.selection()[0]
            index = self.tree_money.index(selected_item)
            self.tree_money.delete(selected_item)
            self.battle_list_money.pop(index)
            self.save_history_notebook_money()
        except IndexError: messagebox.showwarning("提示", "請先選擇欲刪除的標的！")

    def on_tree_money_double_click(self, event):
        region = self.tree_money.identify_region(event.x, event.y)
        if region != "cell": return 
        column = self.tree_money.identify_column(event.x)
        
        selected_item = self.tree_money.selection()[0]
        index = self.tree_money.index(selected_item)
        current_data = self.battle_list_money[index]
        
        if column == "#1" and current_data["type"] == "fund":
            clean_code = str(current_data['code']).strip().upper()
            target_url = f"https://www.moneydj.com/funddj/yp/yp011000.djhtm?a={clean_code}"
            headers = {"User-Agent": "Mozilla/5.0"}
            try:
                res = requests.get(target_url, headers=headers, verify=False, timeout=2)
                if res.status_code == 200 and "查無資料" in res.text:
                    print(f"📡 雷達偵測：【{clean_code}】在國內通道查無資料，自動修正為境外通道！")
                    target_url = f"https://www.moneydj.com/funddj/yp/yp011001.djhtm?a={clean_code}"
            except Exception as e: print(f"偵測通道發生異常，走安全預設: {e}")
            
            print(f"🌐 正在啟動網頁瀏覽器：{target_url}")
            webbrowser.open(target_url)
            return
            
        if column != "#3": return 
        bbox_res = self.tree_money.bbox(selected_item, column)
        if not bbox_res: return  
        x, y, width, height = bbox_res
        
        edit_entry = tk.Entry(self.tree_money, font=("Microsoft JhengHei", 9, "bold"), fg="#228b22", justify="right")
        edit_entry.insert(0, f"{int(current_data['money'])}")
        edit_entry.place(x=x, y=y, width=width, height=height)
        edit_entry.focus_set()
        edit_entry.selection_range(0, tk.END)
        
        def save_inplace_money(event=None):
            if not edit_entry.winfo_exists(): return
            raw_val = edit_entry.get().strip()
            try:
                new_money = float(raw_val)
                if new_money <= 0: raise ValueError
            except ValueError:
                messagebox.showerror("錯誤", "請輸入大於 0 的正確投資金額！")
                edit_entry.destroy()
                return
            self.battle_list_money[index]["money"] = new_money
            self.refresh_tree_money()
            self.save_history_notebook_money()
            edit_entry.destroy()
            
        edit_entry.bind("<Return>", save_inplace_money)
        edit_entry.bind("<FocusOut>", save_inplace_money)

    def on_tree_pct_double_click(self, event):
        region = self.tree_pct.identify_region(event.x, event.y)
        if region != "cell": return 
        column = self.tree_pct.identify_column(event.x)
        
        selected_item = self.tree_pct.selection()[0]
        index = self.tree_pct.index(selected_item)
        current_data = self.battle_list_pct[index]
        
        if column == "#1" and current_data["type"] == "fund":
            clean_code = str(current_data['code']).strip().upper()
            target_url = f"https://www.moneydj.com/funddj/yp/yp011000.djhtm?a={clean_code}"
            headers = {"User-Agent": "Mozilla/5.0"}
            try:
                res = requests.get(target_url, headers=headers, verify=False, timeout=2)
                if res.status_code == 200 and "查無資料" in res.text:
                    print(f"📡 雷達偵測：【{clean_code}】在國內通道查無資料，自動修正為境外通道！")
                    target_url = f"https://www.moneydj.com/funddj/yp/yp011001.djhtm?a={clean_code}"
            except Exception as e: print(f"偵測通道發生異常，走安全預設: {e}")
            
            print(f"🌐 正在啟動網頁瀏覽器：{target_url}")
            webbrowser.open(target_url)
            return
            
        if column != "#3": return 
        bbox_res = self.tree_pct.bbox(selected_item, column)
        if not bbox_res: return  
        x, y, width, height = bbox_res
        
        edit_entry = tk.Entry(self.tree_pct, font=("Microsoft JhengHei", 9, "bold"), fg="#228b22", justify="right")
        edit_entry.insert(0, f"{current_data['money']:.1f}")
        edit_entry.place(x=x, y=y, width=width, height=height)
        edit_entry.focus_set()
        edit_entry.selection_range(0, tk.END)
        
        def save_inplace_pct(event=None):
            if not edit_entry.winfo_exists(): return
            raw_val = edit_entry.get().strip()
            try:
                new_pct = float(raw_val)
                if new_pct <= 0 or new_pct > 100: raise ValueError
            except ValueError:
                messagebox.showerror("錯誤", "請輸入介於 0 到 100 之間的正確百分比權重！")
                edit_entry.destroy()
                return
            self.battle_list_pct[index]["money"] = new_pct
            self.refresh_tree_pct()
            self.save_history_notebook_pct()
            edit_entry.destroy()
            
        edit_entry.bind("<Return>", save_inplace_pct)
        edit_entry.bind("<FocusOut>", save_inplace_pct)

    def process_input_pct(self):
        user_input = self.entry_search_pct.get().strip()
        user_money_raw = self.entry_pct_val.get().strip()
        if not user_input:
            messagebox.showwarning("提示", "請輸入資產名稱或代碼！")
            return
        try:
            allocated_pct = float(user_money_raw)
            if allocated_pct <= 0 or allocated_pct > 100: raise ValueError
        except ValueError:
            messagebox.showerror("錯誤", "請輸入介於 0 到 100 之間的正確百分比權重！")
            return
            
        has_chinese = any('\u4e00' <= c <= '\u9fff' for c in user_input)
        if not has_chinese:
            stock_code = user_input.upper()
            display_str = f"股票: {stock_code}"
            try:
                is_taiwan_asset = stock_code[0].isdigit() if stock_code else False
                actual_code = f"{stock_code}.TW" if is_taiwan_asset else stock_code
                ticker = yf.Ticker(actual_code)
                long_name = ticker.info.get('longName') or ticker.info.get('shortName')
                if long_name:
                    if "Taiwan Semiconductor" in long_name or stock_code == "2330":
                        display_str = "股票: 台積電"
                    else: display_str = f"股票: {long_name}"
            except Exception as e: print(f"股票名稱查詢失敗: {e}")
                
            self.battle_list_pct.append({"type": "stock", "code": stock_code, "name": display_str, "money": allocated_pct})
            self.refresh_tree_pct()
            self.entry_search_pct.delete(0, tk.END)
            self.save_history_notebook_pct()
        else:
            funds = self.search_fund_api_all_pages(user_input)
            if not funds:
                messagebox.showerror("殘念", f"找不到任何跟『{user_input}』相關的基金。")
                return
            if len(funds) == 1:
                full_name = list(funds.keys())[0]
                self.add_fund_to_list_pct(full_name, funds[full_name], allocated_pct)
            else: self.pop_selection_window_pct(funds, allocated_pct)

    def pop_selection_window_pct(self, fund_options, allocated_pct):
        pop = tk.Toplevel(self.root)
        pop.title("🎯 請選擇您要比對的是哪一檔基金？")
        pop.geometry("500x380")
        pop.grab_set()
        
        tk.Label(pop, text=f"共掘出 {len(fund_options)} 筆結果，請點選一檔加入：", font=("Microsoft JhengHei", 10, "bold")).pack(pady=10)
        listbox_pop = tk.Listbox(pop, font=("Microsoft JhengHei", 9))
        listbox_pop.pack(fill="both", expand=True, padx=15, pady=5)
        sb = tk.Scrollbar(listbox_pop, orient="vertical", command=listbox_pop.yview)
        sb.pack(side="right", fill="y")
        listbox_pop.config(yscrollcommand=sb.set)
        
        names = list(fund_options.keys())
        for name in names: listbox_pop.insert(tk.END, name)
            
        def confirm_selection():
            try:
                selected_index = listbox_pop.curselection()[0]
                chosen_full_name = names[selected_index]
                self.add_fund_to_list_pct(chosen_full_name, fund_options[chosen_full_name], allocated_pct)
                pop.destroy()
            except IndexError: 
                messagebox.showwarning("提示", "請先用滑鼠點選一檔基金！", parent=pop)
                
        tk.Button(pop, text="確認加入", command=confirm_selection, bg="#a6e3a1", fg="black", width=15).pack(pady=10)

    def add_fund_to_list_pct(self, name, code, allocated_pct):
        clean_name = clean_fund_name(name)
        if "(" in clean_name: clean_name = clean_name.split("(")[0]
            
        asset_currency = "美金"
        if any(kw in name for kw in ["台幣", "新台幣", "TWD", "NTD"]): asset_currency = "台幣"
        elif any(kw in name for kw in ["日圓", "日幣", "JPY"]): asset_currency = "日圓"
        elif any(kw in name for kw in ["人民幣", "CNY", "RMB"]): asset_currency = "人民幣"
        elif any(kw in name for kw in ["港幣", "港元", "HKD"]): asset_currency = "港幣"
        elif any(kw in name for kw in ["紐幣", "紐元", "NZD"]): asset_currency = "紐幣"
        elif any(kw in name for kw in ["澳幣", "AUD"]): asset_currency = "澳幣"
        elif any(kw in name for kw in ["南非幣", "ZAR"]): asset_currency = "南非幣"
        elif any(kw in name for kw in ["歐元", "EUR"]): asset_currency = "歐元"
            
        is_dividend_type = False
        if any(kw in name for kw in ["月配", "季配", "配息", "穩定月收", "AM", "分派", "收類股"]):
            if "累積" not in name: is_dividend_type = True
                
        type_label = "配息現領" if is_dividend_type else "不配息"
        display_str = f"基金: {clean_name}({asset_currency}-{type_label})"
        
        self.battle_list_pct.append({
            "type": "fund", 
            "code": code, 
            "name": display_str, 
            "full_name": name, 
            "money": allocated_pct,
            "is_dividend": is_dividend_type
        })
        self.refresh_tree_pct()
        self.entry_search_pct.delete(0, tk.END)
        self.save_history_notebook_pct()

    def delete_target_pct(self):
        try:
            selected_item = self.tree_pct.selection()[0]
            index = self.tree_pct.index(selected_item)
            self.tree_pct.delete(selected_item)
            self.battle_list_pct.pop(index)
            self.save_history_notebook_pct()
        except IndexError: messagebox.showwarning("提示", "請先選擇欲刪除的標的！")

    # ─── 📥 歷史數據共用下載核心 (精準還原＋空格清洗防禦版) ───
    def get_fund_history(self, fund_code, start_date, end_date):
        s_dt = datetime.strptime(start_date, "%Y-%m-%d")
        e_dt = datetime.strptime(end_date, "%Y-%m-%d")
        clean_code = str(fund_code).strip().upper()
        
        url_taiwan = f"https://www.moneydj.com/funddj/bcd/tBCDNavList.djbcd?a={clean_code}&B={s_dt.year}-{s_dt.month}-{s_dt.day}&C={e_dt.year}-{e_dt.month}-{e_dt.day}&D="
        url_global = f"https://www.moneydj.com/funddj/bcd/BCDNavList.djbcd?a={clean_code}&B={s_dt.year}-{s_dt.month}-{s_dt.day}&C={e_dt.year}-{e_dt.month}-{e_dt.day}&D="
        
        headers = {"User-Agent": "Mozilla/5.0"}
        fund_data = {}
        
        for url in [url_taiwan, url_global]:
            try:
                res = requests.get(url, headers=headers, verify=False, timeout=5)
                if res.status_code == 200 and res.text.strip():
                    # 🎯 【核心防禦線】：直接把 MoneyDJ 交接處的「空格」在切分前全部換成「逗號」
                    raw_data = res.text.strip().replace(" ", ",")
                    
                    if "html" in raw_data.lower() or len(raw_data) < 10: continue
                        
                    all_elements = raw_data.split(",")
                    cleaned = []
                    for item in all_elements:
                        item = item.strip()
                        if len(item) > 8 and not item.isdigit():
                            cleaned.append(item[:8])
                            cleaned.append(item[8:])
                        else: cleaned.append(item)
                            
                    half = len(cleaned) // 2
                    dates = cleaned[:half]
                    values = cleaned[half:]
                    
                    for d, v in zip(dates, values):
                        if d and v:
                            clean_d = d.strip()
                            if len(clean_d) == 8 and clean_d.isdigit():
                                try:
                                    date_key = f"{clean_d[0:4]}-{clean_d[4:6]}-{clean_d[6:8]}"
                                    fund_data[date_key] = float(v)
                                except:
                                    continue
                    
                    if fund_data:
                        channel_name = "國內(t)" if "tBCD" in url else "海外(無t)"
                        print(f"─── ✅ 成功透過【{channel_name}】通道攻破基金 {clean_code} 數據！ ───")
                        return fund_data
            except: continue
        return fund_data
    
    # ─── 💱 獨立外掛：MoneyDJ 歷史配息數據動態解碼神盾 ───
    def get_fund_dividend_history(self, fund_code):
        from bs4 import BeautifulSoup
        import re
        clean_code = str(fund_code).strip().upper()
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        
        url_taiwan = f"https://www.moneydj.com/funddj/yp/funddividend.djhtm?a={clean_code}"
        url_global = f"https://www.moneydj.com/funddj/yp/wb05.djhtm?a={clean_code}"
        
        div_data = {} # 格式儲存為 { "2026-04-28": 0.073 }
        
        # 發動雙軌制網址體檢 (境內、境外雙向攻堅)
        for url in [url_taiwan, url_global]:
            try:
                res = requests.get(url, headers=headers, verify=False, timeout=5)
                if res.status_code == 200 and res.text.strip():
                    raw_html = res.text
                    
                    # 🕵️‍♂️ 完美對接圖 5：如果是累積型或壞軌，網頁會吐出「無此基金配息資料」，直接換軌
                    if "無此基金配息資料" in raw_html or "無基金配息資料" in raw_html:
                        continue
                        
                    soup = BeautifulSoup(raw_html, "html.parser")
                    # 抓取表格中所有的 tr 行數
                    rows = soup.find_all("tr")
                    
                    for row in rows:
                        tds = [td.get_text().strip() for td in row.find_all("td")]
                        if len(tds) >= 5:
                            # 境內或境外通常第一欄是「配息基準日」或「除息日」
                            # 我們嘗試用正則表達式撈出長得像 2025/06/26 或 2025-06-26 的日期
                            date_match = re.search(r"(\d{4})[-/](\d{2})[-/](\d{2})", tds[0])
                            if date_match:
                                date_str = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
                                
                                # 🕵️‍♂️ 完美對接圖 1~4：在同一個 tr 裡面尋找帶有小數點的「每單位配息金額」
                                for val in tds[1:]:
                                    # 拔掉 &nbsp 或文字雜質，只留純數字與小數點
                                    clean_val = val.replace("nbsp", "").replace(" ", "").strip()
                                    # 用正則抓出類似 0.073 或 0.0336 的浮點數
                                    val_match = re.match(r"^0\.\d+", clean_val)
                                    if val_match:
                                        try:
                                            div_data[date_str] = float(val_match.group(0))
                                            break # 抓到這一行的配息金額後就跳出
                                        except:
                                            continue
                if div_data:
                    print(f"💰 【配息天網】成功扒出基金 {clean_code} 的歷史配息紀錄，共 {len(div_data)} 期！")
                    return div_data
            except:
                continue
        return div_data

    def get_stock_history(self, stock_id, start_date, end_date):
        is_taiwan_asset = stock_id[0].isdigit() if stock_id else False
        stock_code = f"{stock_id}.TW" if is_taiwan_asset else stock_id
        try:
            df = yf.download(stock_code, start=start_date, end=end_date, progress=False)
            stock_data = {}
            for date, row in df.iterrows():
                date_str = date.strftime("%Y-%m-%d")
                stock_data[date_str] = float(row['Close'].iloc[0] if hasattr(row['Close'], 'iloc') else row['Close'])
            return stock_data
        except: return {}

    def launch_battle_money(self):
        # 💡 【優化一】：降級門檻，加入「1筆標的」即可開啟「單人孤獨觀察器模式」！
        if len(self.battle_list_money) < 1:
            messagebox.showwarning("人數不足", "請至少加入「1筆標的」才能啟動觀察器或回測系統喔！")
            return
        self.execute_core_backtest(self.battle_list_money, is_pct_mode=False)

    def launch_battle_pct(self):
        # 💡 【優化二】：降級門檻，分頁二同步支援單人運行
        if len(self.battle_list_pct) < 1:
            messagebox.showwarning("人數不足", "請至少加入「1筆標的」才能啟動觀察器或回測系統喔！")
            return
        try:
            total_fund = float(self.entry_total_principal.get().strip())
            if total_fund <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("錯誤", "請輸入大於 0 的正確總投資資金金額！")
            return

        total_weight = sum(t["money"] for t in self.battle_list_pct)
        if abs(total_weight - 100.0) > 0.05:
            messagebox.showerror("錯誤", f"目前配置總權重比例為 {total_weight:.1f}%，不等於 100%！\n請重新調整各標的比例再進行回測。")
            return

        real_money_list = []
        for t in self.battle_list_pct:
            real_money = total_fund * (t["money"] / 100.0)
            target_copy = t.copy()
            target_copy["money"] = real_money 
            real_money_list.append(target_copy)

        self.execute_core_backtest(real_money_list, is_pct_mode=True, total_principal_pct_mode=total_fund)

    def execute_core_backtest(self, target_list, is_pct_mode=False, total_principal_pct_mode=0):
        import pandas as pd  
        import numpy as np
        start = self.entry_start_date.get().strip()
        end = self.entry_end_date.get().strip()
        
        print(f"📥 正在全速提取歷史數據... 區間: {start} ~ {end}")
        series_list = []
        total_initial_principal = 0 
        current_run_birth_dates = {}
        
        for t in target_list:
            if t["type"] == "stock": 
                hist = self.get_stock_history(t["code"], start, end)
            else:
                hist = self.get_fund_history(t["code"], start, end)
            
            if hist:
                s = pd.Series(hist, name=t["name"])
                s.index = pd.to_datetime(s.index)
                s = s.sort_index()
                current_run_birth_dates[t["name"]] = s.index[0]
                series_list.append(s)
                total_initial_principal += t["money"]
        
        if not series_list or len(current_run_birth_dates) == 0:
            messagebox.showerror("錯誤", "所有標的皆無法取得數據。")
            return
            
        df_battle = pd.concat(series_list, axis=1, sort=True).sort_index()
        
        latest_birth_date = max(current_run_birth_dates.values())
        latest_birth_asset = [name for name, d in current_run_birth_dates.items() if d == latest_birth_date][0]
        user_start_dt = pd.to_datetime(start)
        
        if latest_birth_date > user_start_dt:
            latest_birth_str = latest_birth_date.strftime("%Y-%m-%d")
            notice_msg = f"⚠️ 發現回測時間太前面囉！\n\n【{latest_birth_asset}】\n最早起始數據於：{latest_birth_str}\n\n"
            notice_msg += f"為了確保公平對齊比較，系統已自動將所有標の「回測起跑線」統一調整至：{latest_birth_str} 算起！"
            messagebox.showinfo("智慧起跑線對齊提示", notice_msg)
            df_battle = df_battle.loc[latest_birth_date:]
        else:
            df_battle = df_battle.loc[user_start_dt:]
        
        df_battle = df_battle.ffill().bfill()
        if df_battle.empty:
            messagebox.showerror("錯誤", "對齊起跑線後無可用數據，請重新選擇結束日期！")
            return
            
        # ─── 💱 智慧全自動多國幣別動態解密暨外匯偵測神盾 ───
        fx_cache = {} 
        for t in target_list:
            clean_code = t["code"].strip().upper()
            asset_currency = "USD" 
            
            if not (clean_code[0].isdigit() or clean_code.endswith(".TW")):
                search_string = t.get("full_name", t["name"])
                if any(kw in search_string for kw in ["台幣", "新台幣", "TWD", "NTD"]): asset_currency = "TWD"
                elif any(kw in search_string for kw in ["日圓", "日幣", "JPY"]): asset_currency = "JPY"
                elif any(kw in search_string for kw in ["人民幣", "CNY", "RMB"]): asset_currency = "CNY"
                elif any(kw in search_string for kw in ["港幣", "港元", "HKD"]): asset_currency = "HKD"
                elif any(kw in search_string for kw in ["紐幣", "紐元", "NZD"]): asset_currency = "NZD"
                elif any(kw in search_string for kw in ["澳幣", "AUD"]): asset_currency = "AUD"
                elif any(kw in search_string for kw in ["南非幣", "ZAR"]): asset_currency = "ZAR"
                elif any(kw in search_string for kw in ["歐元", "EUR"]): asset_currency = "EUR"
                elif any(kw in search_string for kw in ["美金", "美元", "USD"]): asset_currency = "USD"

            if asset_currency != "TWD" and asset_currency not in fx_cache:
                fx_start_dt = df_battle.index[0] - timedelta(days=7)
                fx_end_dt = df_battle.index[-1] + timedelta(days=7)
                fx_start_str = fx_start_dt.strftime("%Y-%m-%d")
                fx_end_str = fx_end_dt.strftime("%Y-%m-%d")
                
                if asset_currency == "CNY": fx_ticker = "TWDCNY=X"    
                elif asset_currency == "JPY": fx_ticker = "TWDJPY=X"   
                elif asset_currency == "HKD": fx_ticker = "TWDHKD=X"   
                else: fx_ticker = f"{asset_currency}TWD=X"              
                
                try:
                    print(f"💱 正在全速調閱【{asset_currency} ➔ 台幣】的每日歷史匯率 (代碼: {fx_ticker})...")
                    df_fx = yf.download(fx_ticker, start=fx_start_str, end=fx_end_str, progress=False)
                    
                    if not df_fx.empty:
                        s_fx = pd.Series(df_fx['Close'].iloc[:, 0] if hasattr(df_fx['Close'], 'iloc') else df_fx['Close'])
                        s_fx.index = pd.to_datetime(s_fx.index)
                        s_fx = s_fx.ffill().bfill()
                        
                        if asset_currency in ["CNY", "JPY", "HKD"]:
                            s_fx = 1.0 / s_fx
                            
                        fx_cache[asset_currency] = s_fx.reindex(df_battle.index).ffill().bfill()
                        print(f"✨ 匯率天網裝填成功！【{asset_currency} ➔ 台幣】日資料對齊完畢。")
                    else:
                        raise ValueError
                except:
                    print(f"⚠️ 換匯市場調閱失敗或踩到日幣地雷，【{fx_ticker}】啟動安全防護，此標的暫以原幣(1.0)計價。")
                    fx_cache[asset_currency] = pd.Series(1.0, index=df_battle.index)

        # ─── 🧮 軌道一：生成「考慮匯率」的數據 ───
        df_money_val = pd.DataFrame(index=df_battle.index)
        df_pct_val = pd.DataFrame(index=df_battle.index)
        
        # ─── 🧮 軌道二：生成「不考慮匯率」的純原幣數據 ───
        df_pure_money = pd.DataFrame(index=df_battle.index)
        df_pure_pct = pd.DataFrame(index=df_battle.index)
        
        for t in target_list:
            col_name = t["name"]
            if col_name in df_battle.columns:
                clean_code = t["code"].strip().upper()
                is_div_fund = t.get("is_dividend", False) # 讀取有沒有配息標籤
                
                asset_currency = "USD" 
                if clean_code[0].isdigit() or clean_code.endswith(".TW"):
                    asset_currency = "TWD"
                else:
                    search_string = t.get("full_name", col_name)
                    if any(kw in search_string for kw in ["台幣", "新台幣", "TWD", "NTD"]): asset_currency = "TWD"
                    elif any(kw in search_string for kw in ["日圓", "日幣", "JPY"]): asset_currency = "JPY"
                    elif any(kw in search_string for kw in ["人民幣", "CNY", "RMB"]): asset_currency = "CNY"
                    elif any(kw in search_string for kw in ["港幣", "港元", "HKD"]): asset_currency = "HKD"
                    elif any(kw in search_string for kw in ["紐幣", "紐元", "NZD"]): asset_currency = "NZD"
                    elif any(kw in search_string for kw in ["澳幣", "AUD"]): asset_currency = "AUD"
                    elif any(kw in search_string for kw in ["南非幣", "ZAR"]): asset_currency = "ZAR"
                    elif any(kw in search_string for kw in ["歐元", "EUR"]): asset_currency = "EUR"
                    elif any(kw in search_string for kw in ["美金", "美元", "USD"]): asset_currency = "USD"

                print(f"📡 資產【{col_name}】計價幣別: 💎 {asset_currency} 💎 | 配息現領狀態: {'✅ 啟動' if is_div_fund else '❌ 關閉'}")
                
                # 預先下載這檔基金的配息字典 (如果它是配息型)
                div_history = self.get_fund_dividend_history(clean_code) if is_div_fund else {}
                
                # ─── 🚀 開始日曆時空滾動迴圈演算法 ───
                dates_index = df_battle.index
                
                # 建立儲存容器
                line_money_fx = []
                line_money_pure = []
                
                # 起跑點數據
                first_nav = df_battle[col_name].iloc[0]
                if pd.isna(first_nav) or first_nav == 0: first_nav = 1.0
                
                current_fx_series = fx_cache.get(asset_currency, pd.Series(1.0, index=dates_index)).bfill().ffill()
                first_fx = current_fx_series.iloc[0]
                if pd.isna(first_fx) or first_fx == 0: first_fx = 1.0
                
                # 初始持有單位數 (用當初投入的原始金額算)
                initial_units = t["money"] / first_nav
                
                # 獨立的「配息累積現金池」(原幣與台幣分開記)
                accumulated_cash_pure = 0.0
                accumulated_cash_twd = 0.0
                
                # 逐日時間流動計算
                for current_date in dates_index:
                    current_nav = df_battle[col_name].loc[current_date]
                    current_fx = current_fx_series.loc[current_date]
                    
                    # 🕵️‍♂️ 配息日雷達：如果今天刚好是除息日，且字典裡有配息紀錄
                    date_str_key = current_date.strftime("%Y-%m-%d")
                    if date_str_key in div_history:
                        per_unit_div = div_history[date_str_key]
                        
                        # 領取配息 (原幣現金)
                        today_dividend_pure = initial_units * per_unit_div
                        accumulated_cash_pure += today_dividend_pure
                        
                        # 換算成台幣配息現金領入手心
                        today_dividend_twd = (today_dividend_pure / first_fx) * current_fx
                        accumulated_cash_twd += today_dividend_twd
                    
                    # 計算今日總價值
                    # 軌道二：純原幣市值 ＝ (今日單位數 * 今日淨值) + 累積原幣配息池
                    today_val_pure = (initial_units * current_nav) + accumulated_cash_pure
                    line_money_pure.append(today_val_pure)
                    
                    # 軌道一：含匯率台幣市值 ＝ (今日單位數 * 今日淨值換算台幣) + 累積台幣配息池
                    if asset_currency == "TWD":
                        today_val_fx = (initial_units * current_nav) + accumulated_cash_twd
                    else:
                        today_val_fx = ((initial_units * current_nav) / first_fx) * current_fx + accumulated_cash_twd
                    line_money_fx.append(today_val_fx)
                
                # 把日迴圈跑完的整條黃金線路塞回 DataFrame
                df_money_val[col_name] = line_money_fx
                df_pure_money[col_name] = line_money_pure
                
                # 計算累積報酬率百分比 (%)
                df_pct_val[col_name] = (df_money_val[col_name] / t["money"] - 1.0) * 100
                df_pure_pct[col_name] = (df_pure_money[col_name] / t["money"] - 1.0) * 100
        
        # 集體平移補毒防空值
        df_money_val = df_money_val.ffill().bfill()
        df_pct_val = df_pct_val.ffill().bfill()
        df_pure_money = df_pure_money.ffill().bfill()
        df_pure_pct = df_pure_pct.ffill().bfill()
        
        total_vals_fx = df_money_val.sum(axis=1).values
        total_vals_pure = df_pure_money.sum(axis=1).values
        
        # ─── 📊 繪圖佈局啟動 (智慧三模分流版) ───
        # ─── 📊 繪圖佈局啟動 (智慧雙分頁三模分流完全體) ───
        fig, (ax_money, ax_pct) = plt.subplots(1, 2, figsize=(15, 6))
        common_dates = [d.strftime("%Y-%m-%d") for d in df_battle.index]
        step = max(1, len(common_dates) // 10) 
        
        # 🎯 【雙分頁智慧雷達】：自動辨識當前按鈕來自哪一個分頁，並抓取對應的下拉選單！
        if is_pct_mode:
            selected_mode_str = self.combo_fx_mode_pct.get()
        else:
            selected_mode_str = self.combo_fx_mode.get()
            
        # 🌟 精準解析三種模式字串
        if "模式一" in selected_mode_str or "只顯示原幣別" in selected_mode_str:
            fx_view_mode = 1
        elif "模式二" in selected_mode_str or "只顯示換回台幣" in selected_mode_str:
            fx_view_mode = 2
        else:
            fx_view_mode = 3 # 雙軌全面對照
            
        total_vals_fx = df_money_val.sum(axis=1).values
        total_vals_pure = df_pure_money.sum(axis=1).values
        
        # ─── 📉 左圖：總現值走勢 ───
        if fx_view_mode == 1:
            ax_money.plot(common_dates, total_vals_pure, label="不含匯率：純原始總現值", linewidth=3.0, color="#1f77b4")
            active_total_vals = total_vals_pure
            ax_money.set_title("原始配置總現值走勢 (Portfolio Value Base Currency)", fontsize=12, fontweight='bold')
        elif fx_view_mode == 2:
            ax_money.plot(common_dates, total_vals_fx, label="考慮匯率：總資產現值(台幣)", linewidth=3.0, color="#b22222")
            active_total_vals = total_vals_fx
            ax_money.set_title("新台幣計價總現值走勢 (Portfolio Total Value TWD)", fontsize=12, fontweight='bold')
        else:
            ax_money.plot(common_dates, total_vals_fx, label="考慮匯率：總資產現值(台幣)", linewidth=3.0, color="#b22222")
            ax_money.plot(common_dates, total_vals_pure, label="不含匯率：純原始總現值", linewidth=2.0, color="#1f77b4", linestyle="--")
            active_total_vals = total_vals_fx
            ax_money.set_title("新台幣總現值 vs 原始外幣現值對比", fontsize=12, fontweight='bold')
            
        # 標記最高最低點
        idx_max_m = np.nanargmax(active_total_vals)
        idx_min_m = np.nanargmin(active_total_vals)
        ax_money.annotate(f"[最高]: ${active_total_vals[idx_max_m]:,.0f}\n({common_dates[idx_max_m]})",
                          xy=(idx_max_m, active_total_vals[idx_max_m]), 
                          xytext=(idx_max_m, active_total_vals[idx_max_m] + (np.nanmax(active_total_vals) * 0.03)),
                          arrowprops=dict(facecolor='#a6e3a1', edgecolor='none', shrink=0.05, width=1, headwidth=6),
                          ha='center', fontsize=9, fontweight='bold', color='#228b22',
                          bbox=dict(boxstyle="round,pad=0.3", facecolor="#ffffff", alpha=0.8, edgecolor="#228b22"))
        ax_money.annotate(f"[最低]: ${active_total_vals[idx_min_m]:,.0f}\n({common_dates[idx_min_m]})",
                          xy=(idx_min_m, active_total_vals[idx_min_m]), 
                          xytext=(idx_min_m, active_total_vals[idx_min_m] - (np.nanmax(active_total_vals) * 0.05)),
                          arrowprops=dict(facecolor='#f38ba8', edgecolor='none', shrink=0.05, width=1, headwidth=6),
                          ha='center', fontsize=9, fontweight='bold', color='#cc0000',
                          bbox=dict(boxstyle="round,pad=0.3", facecolor="#ffffff", alpha=0.8, edgecolor="#cc0000"))
                
        ax_money.set_ylabel("資產現值 (元)", fontsize=11, fontweight='bold')
        ax_money.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: f"{int(x):,}"))
        ax_money.xaxis.set_major_locator(plt.MultipleLocator(step))
        plt.setp(ax_money.get_xticklabels(), rotation=30, horizontalalignment='right')
        
        combined_max = max(np.nanmax(total_vals_fx), np.nanmax(total_vals_pure))
        combined_min = min(np.nanmin(total_vals_fx), np.nanmin(total_vals_pure))
        ax_money.set_ylim(combined_min * 0.85, combined_max * 1.1)
        ax_money.legend(fontsize=9, loc="upper left")
        
        # ─── 📈 右圖：報酬率大亂鬥 (依模式動態分流繪製) ───
        if fx_view_mode == 1:
            # 模式一：只畫不含匯率的點虛線(這裡改成實線讓畫面好看)
            for col in df_pure_pct.columns:
                ax_pct.plot(common_dates, df_pure_pct[col].values, label=f"{col} (原幣)", linewidth=1.5, alpha=0.8)
            ax_pct.set_title("原幣別純市場報酬率對比 (Base Currency Returns)", fontsize=12, fontweight='bold')
        elif fx_view_mode == 2:
            # 模式二：只畫含匯率的實線
            for col in df_pct_val.columns:
                ax_pct.plot(common_dates, df_pct_val[col].values, label=f"{col} (台幣)", linewidth=1.5, alpha=0.8)
            ax_pct.set_title("換算新台幣真實報酬率對比 (TWD Returns)", fontsize=12, fontweight='bold')
        else:
            # 模式三：交叉大亂鬥 (實線台幣 / 點線原幣)
            for col in df_pct_val.columns:
                ax_pct.plot(common_dates, df_pct_val[col].values, label=f"{col} (台幣)", linewidth=1.5, alpha=0.8)
            for col in df_pure_pct.columns:
                ax_pct.plot(common_dates, df_pure_pct[col].values, label=f"{col} (原幣)", linewidth=1.2, alpha=0.5, linestyle=":")
            ax_pct.set_title("含匯率(實線) vs 原幣別純報酬(點虛線) 交叉大亂鬥", fontsize=12, fontweight='bold')
                
        ax_pct.axhline(0, color='gray', linestyle=':', alpha=0.6)
        ax_pct.set_ylabel("累積報酬率 (%)", fontsize=11, fontweight='bold')
        ax_pct.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: f"{x:+.1f}%"))
        ax_pct.xaxis.set_major_locator(plt.MultipleLocator(step))
        plt.setp(ax_pct.get_xticklabels(), rotation=30, horizontalalignment='right')
        
        # 動態設定右圖 Y 軸邊界
        if fx_view_mode == 1: pct_matrix = df_pure_pct.values
        elif fx_view_mode == 2: pct_matrix = df_pct_val.values
        else: pct_matrix = np.hstack([df_pct_val.values, df_pure_pct.values])
        
        p_min = np.nanmin(pct_matrix)
        p_max = np.nanmax(pct_matrix)
        ax_pct.set_ylim(-10 if np.isnan(p_min) else p_min - 5, 10 if np.isnan(p_max) else p_max + 5)
        ax_pct.legend(fontsize=8, loc="upper left", ncol=1 if fx_view_mode != 3 else 2)
        
        # ─── 🔮 滑鼠移入智慧看板連動模組 ───
        box_money = ax_money.annotate("", xy=(0.5, 0.95), xycoords='axes fraction', va='top', ha='center',
                                      bbox=dict(boxstyle="round,pad=0.5", facecolor="#252538", alpha=0.85, edgecolor="#7f849c"),
                                      fontsize=9, color=TEXT_LIGHT, visible=False)
        box_pct = ax_pct.annotate("", xy=(0.5, 0.95), xycoords='axes fraction', va='top', ha='center',
                                   bbox=dict(boxstyle="round,pad=0.5", facecolor="#252538", alpha=0.85, edgecolor="#7f849c"),
                                   fontsize=9, color=TEXT_LIGHT, visible=False)

        def on_mouse_move(event):
            box_money.set_visible(False)
            box_pct.set_visible(False)
            if event.xdata is None:
                fig.canvas.draw_idle()
                return
            idx = min(max(0, int(round(event.xdata))), len(common_dates) - 1)
            target_date = common_dates[idx]
            
            if event.inaxes == ax_money:
                if fx_view_mode == 1: txt = [f"歷史時間：{target_date}", "────────────────", f"原始外幣價值: ${total_vals_pure[idx]:,.0f}"]
                elif fx_view_mode == 2: txt = [f"歷史時間：{target_date}", "────────────────", f"實際台幣價值: ${total_vals_fx[idx]:,.0f}"]
                else: txt = [f"歷史時間：{target_date}", "────────────────", f"考慮匯率(台幣): ${total_vals_fx[idx]:,.0f}", f"不含匯率(原幣): ${total_vals_pure[idx]:,.0f}"]
                box_money.set_text("\n".join(txt))
                box_money.set_visible(True)
                
            elif event.inaxes == ax_pct:
                txt = [f"歷史時間：{target_date}", "────────────────"]
                for col in df_pct_val.columns:
                    if fx_view_mode == 1: txt.append(f"  - {col}: 原幣 {df_pure_pct[col].iloc[idx]:+.1f}%")
                    elif fx_view_mode == 2: txt.append(f"  - {col}: 台幣 {df_pct_val[col].iloc[idx]:+.1f}%")
                    else: txt.append(f"  - {col}: 台幣 {df_pct_val[col].iloc[idx]:+.1f}% | 原幣 {df_pure_pct[col].iloc[idx]:+.1f}%")
                box_pct.set_text("\n".join(txt))
                box_pct.set_visible(True)
            fig.canvas.draw_idle()

        fig.canvas.mpl_connect("motion_notify_event", on_mouse_move)
        plt.subplots_adjust(left=0.07, right=0.95, top=0.90, bottom=0.15, wspace=0.25)
        plt.show()

if __name__ == "__main__":
    root = tk.Tk()
    app = MultiComparatorApp(root)
    root.mainloop()