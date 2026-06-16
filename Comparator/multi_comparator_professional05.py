import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import requests
import urllib3
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import urllib.parse
import json
import os
import webbrowser  # 🌐 引入全自動網頁開啟核心外掛
from tkcalendar import Calendar

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
    """✂️ 基金名稱精準瘦身手術：拔除所有冗長的警語與括號"""
    clean_name = raw_name
    if "-" in clean_name: clean_name = clean_name.split("-")[0]
    if "(" in clean_name: clean_name = clean_name.split("(")[0]
    if "（" in clean_name: clean_name = clean_name.split("（")[0]
    return clean_name.strip()

class MultiComparatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("多資產配置雙模式歷史回測系統 (現值版/比例版完全體)")
        self.root.geometry("650x760") 
        
        # 建立兩個分頁獨立的資產池
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

        # ─── 🗂️ 建立分頁核心控制元件 (Notebook) ───
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(pady=5, fill="both", expand=True, padx=15)
        
        self.tab_money = tk.Frame(self.notebook)
        self.tab_pct = tk.Frame(self.notebook)
        
        self.notebook.add(self.tab_money, text=" 💰 模式一：獨立資金現值版 ")
        self.notebook.add(self.tab_pct, text=" % 模式二：資產權重比例版 ")
        
        # ─── 🛠️ 建立分頁一：現值版介面 ───
        self.setup_money_tab()
        
        # ─── 🛠️ 建立分頁二：比例版介面 ───
        self.setup_pct_tab()
        
        # 讀取雙邊各自獨立的歷史存檔
        self.load_history_notebook_money()
        self.load_history_notebook_pct()

    # ─── 💰 建立分頁一：現值版介面 ───
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
        
        # 綁定統一雙擊事件
        self.tree_money.bind("<Double-1>", self.on_tree_money_double_click)
        scrollbar = tk.Scrollbar(frame_list, orient="vertical", command=self.tree_money.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree_money.config(yscrollcommand=scrollbar.set)
        
        frame_ctrl = tk.Frame(self.tab_money)
        frame_ctrl.pack(pady=5, fill="x", padx=10)
        btn_del = tk.Button(frame_ctrl, text="❌ 刪除選中標的", command=self.delete_target_money, bg="#f38ba8", fg="black", font=("Microsoft JhengHei", 9), width=15)
        btn_del.pack(side="left", padx=5)
        
        btn_launch = tk.Button(self.tab_money, text="📊 執行模式一歷史績效回測", font=("Microsoft JhengHei", 12, "bold"), 
                               command=self.launch_battle_money, bg="#a6e3a1", fg="black", height=2)
        btn_launch.pack(fill="x", padx=10, pady=10)

    # ─── % 建立分頁二：比例版介面 ───
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
        
        # 綁定統一雙擊事件
        self.tree_pct.bind("<Double-1>", self.on_tree_pct_double_click)
        scrollbar = tk.Scrollbar(frame_list, orient="vertical", command=self.tree_pct.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree_pct.config(yscrollcommand=scrollbar.set)
        
        frame_ctrl = tk.Frame(self.tab_pct)
        frame_ctrl.pack(pady=5, fill="x", padx=10)
        btn_del = tk.Button(frame_ctrl, text="❌ 刪除選中標的", command=self.delete_target_pct, bg="#f38ba8", fg="black", font=("Microsoft JhengHei", 9), width=15)
        btn_del.pack(side="left", padx=5)
        
        btn_launch = tk.Button(self.tab_pct, text="📊 執行模式二歷史績效回測", font=("Microsoft JhengHei", 12, "bold"), 
                               command=self.launch_battle_pct, bg="#a6e3a1", fg="black", height=2)
        btn_launch.pack(fill="x", padx=10, pady=10)

    # ─── 📅 全域通用小日曆 ───
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

    # ─── 💾 雙邊資料讀寫刷新控制 ───
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

    # ─── 🔎 網路穿梭搜尋引擎 ───
    def search_fund_api_all_pages(self, keyword):
        fund_dict = {}
        page = 1
        print(f"🕵️‍♂️ 正在發動全網【跨頁穿梭補網】，關鍵字: [{keyword}]")
        while True:
            url = f"https://www.moneydj.com/funddj/ya/yFundSearch.djhtm?a={urllib.parse.quote(keyword)}&B={page}&C=0&D=&ff=1"
            headers = {"User-Agent": "Mozilla/5.0"}
            try:
                res = requests.get(url, headers=headers, verify=False)
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
                        
                        if is_legal_code and is_legal_name and fund_code not in fund_dict.values():
                            clean_name = clean_fund_name(raw_fund_name)
                            if clean_name in fund_dict and fund_dict[clean_name] != fund_code:
                                clean_name = f"{clean_name}({fund_code})"
                            fund_dict[clean_name] = fund_code
                            current_page_found += 1
                    if current_page_found == 0: break
                    print(f"   ➔ ✅ 成功攻破第 {page} 頁，捕獲 {current_page_found} 檔真正 [{keyword}] 基金...")
                    page += 1
                    import time
                    time.sleep(0.05)
                else: break
            except: break
        return fund_dict

    # ─── 📥 分頁一新增標的與雙擊雷達智慧分流 ───
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
        pop.geometry("450x350") 
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
                chosen_name = names[selected_index]
                self.add_fund_to_list_money(chosen_name, fund_options[chosen_name], allocated_money)
                pop.destroy()
            except IndexError: messagebox.showwarning("提示", "請先用滑鼠點選一檔基金！", parent=pop)
        tk.Button(pop, text="確認加入", command=confirm_selection, bg="#a6e3a1", fg="black", width=15).pack(pady=10)

    def add_fund_to_list_money(self, name, code, allocated_money):
        display_str = f"基金: {name}"
        self.battle_list_money.append({"type": "fund", "code": code, "name": display_str, "money": allocated_money})
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
        """🎯 模式一智慧分流：雙擊第一欄開基金網頁 / 雙擊第三欄修改金額"""
        region = self.tree_money.identify_region(event.x, event.y)
        if region != "cell": return 
        column = self.tree_money.identify_column(event.x)
        
        selected_item = self.tree_money.selection()[0]
        index = self.tree_money.index(selected_item)
        current_data = self.battle_list_money[index]
        
        # 🟢 【新需求一】：如果雙擊第一欄「資產名稱」且是基金，全自動秒開 MoneyDJ 網頁
        if column == "#1" and current_data["type"] == "fund":
            fund_url = f"https://www.moneydj.com/funddj/yp/yp011000.djhtm?a={current_data['code']}"
            print(f"🌐 正在啟動網頁瀏覽器，深入解析基金基本資料：{fund_url}")
            webbrowser.open(fund_url)
            return
            
        # 如果點的是第三欄，維持原先的原地修改金額邏輯
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

    # ─── 📥 分頁二新增標的與雙擊雷達智慧分流 ───
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
        pop.geometry("450x350") 
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
                chosen_name = names[selected_index]
                self.add_fund_to_list_pct(chosen_name, fund_options[chosen_name], allocated_pct)
                pop.destroy()
            except IndexError: messagebox.showwarning("提示", "請先用滑鼠點選一檔基金！", parent=pop)
        tk.Button(pop, text="確認加入", command=confirm_selection, bg="#a6e3a1", fg="black", width=15).pack(pady=10)

    def add_fund_to_list_pct(self, name, code, allocated_pct):
        display_str = f"基金: {name}"
        self.battle_list_pct.append({"type": "fund", "code": code, "name": display_str, "money": allocated_pct})
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

    def on_tree_pct_double_click(self, event):
        """🎯 模式二智慧分流：雙擊第一欄開基金網頁 / 雙擊第三欄修改百分比比例"""
        region = self.tree_pct.identify_region(event.x, event.y)
        if region != "cell": return 
        column = self.tree_pct.identify_column(event.x)
        
        selected_item = self.tree_pct.selection()[0]
        index = self.tree_pct.index(selected_item)
        current_data = self.battle_list_pct[index]
        
        # 🟢 【新需求二】：分頁二同步支援雙擊「資產名稱」秒開 MoneyDJ 網頁
        if column == "#1" and current_data["type"] == "fund":
            fund_url = f"https://www.moneydj.com/funddj/yp/yp011000.djhtm?a={current_data['code']}"
            print(f"🌐 正在啟動網頁瀏覽器，深入解析基金基本資料：{fund_url}")
            webbrowser.open(fund_url)
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

    # ─── 📈 歷史數據共用下載核心 ───
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
                    else: cleaned.append(item)
                half = len(cleaned) // 2
                dates = cleaned[:half]
                values = cleaned[half:]
                for d, v in zip(dates, values):
                    if d and v: fund_data[f"{d[0:4]}-{d[4:6]}-{d[6:8]}"] = float(v)
        except: pass
        return fund_data

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
        if len(self.battle_list_money) < 2:
            messagebox.showwarning("人數不足", "模式一回測至少需要加入「2筆標的」喔！")
            return
        self.execute_core_backtest(self.battle_list_money, is_pct_mode=False)

    def launch_battle_pct(self):
        if len(self.battle_list_pct) < 2:
            messagebox.showwarning("人數不足", "模式二回測至少需要加入「2筆標的」喔！")
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

    # ─── 📊 核心通用雙圖表繪圖暨看板引擎 ───
    def execute_core_backtest(self, target_list, is_pct_mode=False, total_principal_pct_mode=0):
        import pandas as pd  
        start = self.entry_start_date.get().strip()
        end = self.entry_end_date.get().strip()
        
        print(f"📥 正在全速提取歷史數據... 區間: {start} ~ {end}")
        series_list = []
        total_initial_principal = 0 
        
        for t in target_list:
            if t["type"] == "stock": hist = self.get_stock_history(t["code"], start, end)
            else:
                hist = self.get_fund_history(t["code"], start, end)
                if not hist: hist = self.get_fund_history(t["code"], "2025-06-02", "2026-06-02")
            
            if hist:
                s = pd.Series(hist, name=t["name"])
                s.index = pd.to_datetime(s.index)
                series_list.append(s)
                total_initial_principal += t["money"]
        
        if not series_list:
            messagebox.showerror("錯誤", "所有標的皆無法取得數據。")
            return
            
        df_battle = pd.concat(series_list, axis=1, sort=True).sort_index()
        df_battle = df_battle.ffill().bfill()
        
        df_money_val = pd.DataFrame(index=df_battle.index)
        for t in target_list:
            col_name = t["name"]
            if col_name in df_battle.columns:
                df_money_val[col_name] = (df_battle[col_name] / df_battle[col_name].iloc[0]) * t["money"]
        
        df_money_val = df_money_val.ffill().bfill()
        df_money_val["投資組合總價值 (Total Portfolio)"] = df_money_val.sum(axis=1)
        
        fig, (ax_money, ax_pct) = plt.subplots(1, 2, figsize=(15, 6))
        
        df_pct_val = pd.DataFrame(index=df_battle.index)
        for t in target_list:
            col_name = t["name"]
            if col_name in df_battle.columns:
                df_pct_val[col_name] = (df_battle[col_name] / df_battle[col_name].iloc[0] - 1) * 100
        
        df_pct_val["投資組合總價值 (Total Portfolio)"] = ((df_money_val["投資組合總價值 (Total Portfolio)"] / total_initial_principal) - 1) * 100
        
        common_dates = [d.strftime("%Y-%m-%d") for d in df_money_val.index]
        step = max(1, len(common_dates) // 10) 
        
        # 左圖：資產市現值
        for col in df_money_val.columns:
            if col == "投資組合總價值 (Total Portfolio)":
                ax_money.plot(common_dates, df_money_val[col].values, label=col, linewidth=3.0, color="#b22222")
            else:
                ax_money.plot(common_dates, df_money_val[col].values, label=col, linewidth=1.5, alpha=0.8)
                
        ax_money.set_title("資產市現值配置走勢", fontsize=12, fontweight='bold')
        ax_money.set_ylabel("資產市現值 (元)", fontsize=11, fontweight='bold')
        ax_money.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: f"{int(x):,}"))
        ax_money.xaxis.set_major_locator(plt.MultipleLocator(step))
        plt.setp(ax_money.get_xticklabels(), rotation=30, horizontalalignment='right')
        ax_money.legend(fontsize=9, loc="upper left")
        
        # 右圖：累計報酬率
        for col in df_pct_val.columns:
            if col == "投資組合總價值 (Total Portfolio)":
                ax_pct.plot(common_dates, df_pct_val[col].values, label=col, linewidth=3.0, color="#b22222")
            else:
                ax_pct.plot(common_dates, df_pct_val[col].values, label=col, linewidth=1.5, alpha=0.8)
                
        ax_pct.axhline(0, color='gray', linestyle=':', alpha=0.6)
        ax_pct.set_title("累計報酬率對比走勢", fontsize=12, fontweight='bold')
        ax_pct.set_ylabel("累計報酬率 (%)", fontsize=11, fontweight='bold')
        ax_pct.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: f"{x:+.1f}%"))
        ax_pct.xaxis.set_major_locator(plt.MultipleLocator(step))
        plt.setp(ax_pct.get_xticklabels(), rotation=30, horizontalalignment='right')
        ax_pct.legend(fontsize=9, loc="upper left")
        
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
                txt = [f"📅 時間：{target_date}", "────────────────"]
                for t in target_list:
                    col = t["name"]
                    if col in df_money_val.columns:
                        txt.append(f"  - {col}: ${df_money_val[col].iloc[idx]:,.0f}")
                txt.append("────────────────")
                txt.append(f"  總資產現值: ${df_money_val['投資組合總價值 (Total Portfolio)'].iloc[idx]:,.0f}")
                box_money.set_text("\n".join(txt))
                box_money.set_visible(True)
                
            elif event.inaxes == ax_pct:
                txt = [f"📅 時間：{target_date}", "────────────────"]
                for t in target_list:
                    col = t["name"]
                    if col in df_pct_val.columns:
                        txt.append(f"  - {col}: {df_pct_val[col].iloc[idx]:+.1f}% (淨值:{df_battle[col].iloc[idx]:,.2f})")
                txt.append("────────────────")
                txt.append(f"  組合總報酬: {df_pct_val['投資組合總價值 (Total Portfolio)'].iloc[idx]:+.1f}%")
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