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
from tkcalendar import Calendar

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ─── 🎨 圖表視覺設定 ───
plt.style.use('seaborn-v0_8-darkgrid' if 'seaborn-v0_8-darkgrid' in plt.style.available else 'default')
plt.rcParams['font.family'] = ['Microsoft JhengHei']
plt.rcParams['axes.unicode_minus'] = False

TEXT_LIGHT = "#cdd6f4"
HISTORY_FILE = "portfolio_history.json"

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
        self.root.title("多資產配置獨立資金歷史回測系統 (穩定商用完全體)")
        self.root.geometry("620x680") 
        
        self.battle_list = []
        
        # ─── 📅 1. 智慧歷史回測時間軸 (結束抓當下，開始往前推一年) ───
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
        
        # ─── 📥 2. 輸入與資金配置區 ───
        frame_input = tk.LabelFrame(root, text=" 2. 輸入標的與獨立投資金額 ")
        frame_input.pack(pady=6, fill="x", padx=15)
        
        frame_row1 = tk.Frame(frame_input)
        frame_row1.pack(fill="x", padx=10, pady=2)
        tk.Label(frame_row1, text="股票代號/基金名稱:").pack(side="left", padx=2)
        self.entry_search = tk.Entry(frame_row1, font=("Microsoft JhengHei", 10))
        self.entry_search.pack(side="left", fill="x", expand=True, padx=5)
        
        frame_row2 = tk.Frame(frame_input)
        frame_row2.pack(fill="x", padx=10, pady=5)
        tk.Label(frame_row2, text="此項目投入金額 ($):").pack(side="left", padx=2)
        self.entry_money = tk.Entry(frame_row2, font=("Microsoft JhengHei", 10, "bold"), width=15, fg="#228b22")
        self.entry_money.pack(side="left", padx=5)
        self.entry_money.insert(0, "1000000") 
        
        btn_add = tk.Button(frame_row2, text="加入投資組合", command=self.process_input, 
                            bg="#89b4fa", fg="black", font=("Microsoft JhengHei", 9, "bold"), width=12)
        btn_add.pack(side="right", padx=2)
        
        # ─── 📋 3. 投資組合配置表 (Treeview) ───
        frame_list = tk.LabelFrame(root, text=" 3. 目前投資組合配置 (關閉程式自動記憶) ")
        frame_list.pack(pady=5, fill="both", expand=True, padx=15)
        
        columns = ("name", "code", "money")
        self.tree = ttk.Treeview(frame_list, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("name", text="資產名稱")
        self.tree.heading("code", text="資產代碼")
        self.tree.heading("money", text="分配投入金額 (元)")
        self.tree.column("name", width=260, anchor="w")
        self.tree.column("code", width=100, anchor="center")
        self.tree.column("money", width=140, anchor="e")
        self.tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        # 💡 【新增】：滑鼠雙擊表格任意一列，就觸發修改本金視窗
        self.tree.bind("<Double-1>", self.on_tree_double_click)
        scrollbar = tk.Scrollbar(frame_list, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.config(yscrollcommand=scrollbar.set)
        
        frame_ctrl = tk.Frame(root)
        frame_ctrl.pack(pady=5, fill="x", padx=15)
        btn_del = tk.Button(frame_ctrl, text="❌ 刪除選中標的", command=self.delete_target, bg="#f38ba8", fg="black", font=("Microsoft JhengHei", 9), width=15)
        btn_del.pack(side="left", padx=5)
        
        # ─── 🚀 4. 啟動按鈕 ───
        btn_launch = tk.Button(root, text="📊 執行投資組合歷史績效回測", font=("Microsoft JhengHei", 12, "bold"), 
                               command=self.launch_battle, bg="#a6e3a1", fg="black", height=2)
        btn_launch.pack(fill="x", padx=15, pady=12)
        
        self.load_history_notebook()

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

    def save_history_notebook(self):
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.battle_list, f, ensure_ascii=False, indent=4)
        except Exception as e: print(f"快取儲存失敗: {e}")

    def load_history_notebook(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    self.battle_list = json.load(f)
                self.refresh_tree_by_list()
            except Exception as e: print(f"讀取快取失敗: {e}")

    def refresh_tree_by_list(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        for t in self.battle_list:
            self.tree.insert("", tk.END, values=(t["name"], t["code"], f"${t['money']:,.0f}"))

    def search_fund_api_all_pages(self, keyword):
        fund_dict = {}
        page = 1
        print(f"🕵️‍♂️ 正在發動全網【跨頁穿梭補網】，關鍵字: [{keyword}]")
        while True:
            url = f"https://www.moneydj.com/funddj/ya/yFundSearch.djhtm?a={encoded_keyword if 'encoded_keyword' in locals() else urllib.parse.quote(keyword)}&B={page}&C=0&D=&ff=1"
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

    def process_input(self):
        user_input = self.entry_search.get().strip()
        user_money_raw = self.entry_money.get().strip()
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
                # 💡 新智慧防呆：只要開頭第一個字是數字，就自動判定為台股並補上 .TW
                is_taiwan_asset = stock_code[0].isdigit() if stock_code else False
                actual_code = f"{stock_code}.TW" if is_taiwan_asset else stock_code
                
                ticker = yf.Ticker(actual_code)
                long_name = ticker.info.get('longName') or ticker.info.get('shortName')
                if long_name:
                    if "Taiwan Semiconductor" in long_name or stock_code == "2330":
                        display_str = "股票: 台積電"
                    else:
                        display_str = f"股票: {long_name}"
            except Exception as e:
                print(f"股票名稱查詢失敗: {e}")
                
            self.battle_list.append({"type": "stock", "code": stock_code, "name": display_str, "money": allocated_money})
            self.refresh_tree_by_list()
            self.entry_search.delete(0, tk.END)
            self.save_history_notebook()
        else:
            funds = self.search_fund_api_all_pages(user_input)
            if not funds:
                messagebox.showerror("殘念", f"找不到任何跟『{user_input}』相關的基金。")
                return
            if len(funds) == 1:
                full_name = list(funds.keys())[0]
                self.add_fund_to_list(full_name, funds[full_name], allocated_money)
            else:
                self.pop_selection_window(funds, allocated_money)

    def pop_selection_window(self, fund_options, allocated_money):
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
                self.add_fund_to_list(chosen_name, fund_options[chosen_name], allocated_money)
                pop.destroy()
            except IndexError:
                messagebox.showwarning("提示", "請先用滑鼠點選一檔基金！", parent=pop)
        tk.Button(pop, text="確認加入", command=confirm_selection, bg="#a6e3a1", fg="black", width=15).pack(pady=10)

    def add_fund_to_list(self, name, code, allocated_money):
        display_str = f"基金: {name}"
        self.battle_list.append({"type": "fund", "code": code, "name": display_str, "money": allocated_money})
        self.refresh_tree_by_list()
        self.entry_search.delete(0, tk.END)
        self.save_history_notebook()

    def delete_target(self):
        try:
            selected_item = self.tree.selection()[0]
            index = self.tree.index(selected_item)
            self.tree.delete(selected_item)
            self.battle_list.pop(index)
            self.save_history_notebook()
        except IndexError:
            messagebox.showwarning("提示", "請先選擇欲刪除的標的！")

    def on_tree_double_click(self, event):
        """🎯 雙擊表格列：在「金額欄位」原地生出輸入框，像 Excel 一樣直接輸入修改"""
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell": return 
        
        column = self.tree.identify_column(event.x)
        if column != "#3": return # 限制：只有雙擊第三欄「分配投入金額」才能修改
        
        selected_item = self.tree.selection()[0]
        index = self.tree.index(selected_item)
        current_data = self.battle_list[index]
        
        # ─── ⚖️ 核心修正點：換成正版 bbox ───
        bbox_res = self.tree.bbox(selected_item, column)
        if not bbox_res: return  # 防呆：如果沒抓到坐標就直接返回，不崩潰
        x, y, width, height = bbox_res
        
        # 在 Treeview 的正上方「原地釘上」一個暫時的輸入框 Entry
        edit_entry = tk.Entry(self.tree, font=("Microsoft JhengHei", 9, "bold"), fg="#228b22", justify="right")
        edit_entry.insert(0, f"{int(current_data['money'])}")
        edit_entry.place(x=x, y=y, width=width, height=height)
        
        edit_entry.focus_set()
        edit_entry.selection_range(0, tk.END)
        
        def save_inplace_money(event=None):
            raw_val = edit_entry.get().strip()
            try:
                new_money = float(raw_val)
                if new_money <= 0: raise ValueError
            except ValueError:
                messagebox.showerror("錯誤", "請輸入大於 0 的正確投資金額！")
                edit_entry.destroy()
                return
                
            self.battle_list[index]["money"] = new_money
            self.refresh_tree_by_list()
            self.save_history_notebook()
            edit_entry.destroy()
            
        edit_entry.bind("<Return>", save_inplace_money)
        edit_entry.bind("<FocusOut>", save_inplace_money)
        
        def save_inplace_money(event=None):
            """內建安全儲存與自動銷毀機制"""
            raw_val = edit_entry.get().strip()
            try:
                new_money = float(raw_val)
                if new_money <= 0: raise ValueError
            except ValueError:
                messagebox.showerror("錯誤", "請輸入大於 0 的正確投資金額！")
                edit_entry.destroy()
                return
                
            # 💡 更新記憶體、前端表格與快取 JSON
            self.battle_list[index]["money"] = new_money
            self.refresh_tree_by_list()
            self.save_history_notebook()
            
            # 任務完成，把暫時的輸入框從畫面上拔除
            edit_entry.destroy()
            
        # ─── 🎛️ 綁定 Excel 級自動化事件 ───
        # A. 鍵盤按下 Enter 直接存檔
        edit_entry.bind("<Return>", save_inplace_money)
        # B. 滑鼠點擊電腦螢幕其他任何地方（失去焦點 FocusOut），自動存檔並關閉輸入框
        edit_entry.bind("<FocusOut>", save_inplace_money)        

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
                    if d and v:
                        fund_data[f"{d[0:4]}-{d[4:6]}-{d[6:8]}"] = float(v)
        except: pass
        return fund_data

    def get_stock_history(self, stock_id, start_date, end_date):
        # 💡 同步升級：只要開頭是數字，一律補上 .TW 確保 Yahoo Finance 找得到真貨
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

    def launch_battle(self):
        import pandas as pd  
        
        if len(self.battle_list) < 2:
            messagebox.showwarning("人數不足", "回測至少需要加入「2筆標的」喔！")
            return
            
        start = self.entry_start_date.get().strip()
        end = self.entry_end_date.get().strip()
        
        try:
            datetime.strptime(start, "%Y-%m-%d")
            datetime.strptime(end, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("日期錯誤", "請輸入標準 YYYY-MM-DD 格式")
            return
            
        print(f"📥 正在全速提取歷史數據... 區間: {start} ~ {end}")
        
        series_list = []
        total_initial_principal = 0 
        
        for t in self.battle_list:
            if t["type"] == "stock":
                hist = self.get_stock_history(t["code"], start, end)
            else:
                hist = self.get_fund_history(t["code"], start, end)
                if not hist:
                    hist = self.get_fund_history(t["code"], "2025-06-02", "2026-06-02")
            
            if hist:
                s = pd.Series(hist, name=t["name"])
                s.index = pd.to_datetime(s.index)
                series_list.append(s)
                total_initial_principal += t["money"]
        
        if not series_list:
            messagebox.showerror("錯誤", "所有標的皆無法取得數據。")
            return
            
        # 1. 聯集合併表格 (加入 sort=True 封鎖警告)
        df_battle = pd.concat(series_list, axis=1, sort=True).sort_index()
        
        # 2. 🩹 橫向平移補齊：雙向徹底填滿所有因開休市時差產生的空格
        df_battle = df_battle.ffill().bfill()
        
        # 3. 🧮 金額現值表格生成
        df_money_val = pd.DataFrame(index=df_battle.index)
        for t in self.battle_list:
            col_name = t["name"]
            if col_name in df_battle.columns:
                df_money_val[col_name] = (df_battle[col_name] / df_battle[col_name].iloc[0]) * t["money"]
        
        # 💡 【總價值斷點終極補強】：橫向加總前，對現值表再做一次終點前值平移補修，防止基金未更新導致總分斷線
        df_money_val = df_money_val.ffill().bfill()
        df_money_val["投資組合總價值 (Total Portfolio)"] = df_money_val.sum(axis=1)
        
        common_dates = [d.strftime("%Y-%m-%d") for d in df_money_val.index]
        
        # ─── 🎨 畫布渲染 ───
        # ─── 🎨 雙軸畫布極致渲染 ───
        # ─── 🎨 雙圖表獨立分層渲染 (上下拆分，共用 X 軸) ───
        # ─── 🎨 雙圖表左右獨立分流渲染 (1列2欄，寬度加寬至 15) ───
        # ─── 🎨 雙圖表左右獨立分流渲染 (1列2欄，寬度維持 15) ───
        fig, (ax_money, ax_pct) = plt.subplots(1, 2, figsize=(15, 6))
        
        # 計算每個資產每天的精準報酬率 (%) 表格
        df_pct_val = pd.DataFrame(index=df_battle.index)
        for t in self.battle_list:
            col_name = t["name"]
            if col_name in df_battle.columns:
                df_pct_val[col_name] = (df_battle[col_name] / df_battle[col_name].iloc[0] - 1) * 100
        
        df_pct_val["投資組合總價值 (Total Portfolio)"] = ((df_money_val["投資組合總價值 (Total Portfolio)"] / total_initial_principal) - 1) * 100
        
        common_dates = [d.strftime("%Y-%m-%d") for d in df_money_val.index]
        step = max(1, len(common_dates) // 10) 
        
        # ─── 📈 【左圖世界】：資產市現值 (元) ───
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
        
        # ─── 📉 【右圖世界】：累計報酬率 (%) ───
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
        
        # ─── 🎛️ 高級中置看板 (💡 xy=(0.5, 0.95), ha='center' 改為正中間，絕不擠壓排版) ───
        # 左邊專用看板 (現值)
        box_money = ax_money.annotate("", xy=(0.5, 0.95), xycoords='axes fraction', va='top', ha='center',
                                      bbox=dict(boxstyle="round,pad=0.5", facecolor="#252538", alpha=0.85, edgecolor="#7f849c"),
                                      fontsize=9, color=TEXT_LIGHT, visible=False)
        
        # 右邊專用看板 (報酬率)
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
                # 【左圖邏輯：純現值看板】
                txt = [f"📅 時間：{target_date}", "────────────────"]
                for t in self.battle_list:
                    col = t["name"]
                    if col in df_money_val.columns:
                        txt.append(f"  - {col}: ${df_money_val[col].iloc[idx]:,.0f}")
                txt.append("────────────────")
                txt.append(f"  總資產現值: ${df_money_val['投資組合總價值 (Total Portfolio)'].iloc[idx]:,.0f}")
                
                box_money.set_text("\n".join(txt))
                box_money.set_visible(True)
                
            elif event.inaxes == ax_pct:
                # 【右圖邏輯：純報酬率看板】
                txt = [f"📅 時間：{target_date}", "────────────────"]
                for t in self.battle_list:
                    col = t["name"]
                    if col in df_pct_val.columns:
                        txt.append(f"  - {col}: {df_pct_val[col].iloc[idx]:+.1f}% (淨值:{df_battle[col].iloc[idx]:,.2f})")
                txt.append("────────────────")
                txt.append(f"  組合總報酬: {df_pct_val['投資組合總價值 (Total Portfolio)'].iloc[idx]:+.1f}%")
                
                box_pct.set_text("\n".join(txt))
                box_pct.set_visible(True)

            fig.canvas.draw_idle()

        fig.canvas.mpl_connect("motion_notify_event", on_mouse_move)
        
        # ─── 🚀 頂級防擠壓排版對策 ───
        # plt.tight_layout() 有時候會抽風，我們直接改用 subplots_adjust 手動強行拉開左右間距（wspace=0.25）
        plt.subplots_adjust(left=0.07, right=0.95, top=0.90, bottom=0.15, wspace=0.25)
        plt.show()

if __name__ == "__main__":
    root = tk.Tk()
    app = MultiComparatorApp(root)
    root.mainloop()