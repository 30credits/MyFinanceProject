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
        fig, ax = plt.subplots(figsize=(11, 6))
        
        for col in df_money_val.columns:
            if col == "投資組合總價值 (Total Portfolio)":
                # 💡 移除 linestyle="--"，換成純實線，當場消滅毛毛蟲與斷裂圖標！
                ax.plot(common_dates, df_money_val[col].values, label=col, linewidth=3.5, color="#b22222")
            else:
                ax.plot(common_dates, df_money_val[col].values, label=col, linewidth=1.8, alpha=0.8)
            
        ax.set_title(f"投資組合配置歷史資產總收益增長回測 ({start} ~ {end})", fontsize=14, fontweight='bold')
        ax.set_xlabel("交易日期 (已自動修補跨國休市斷點)", fontsize=12)
        ax.set_ylabel("資產市現值 (元)", fontsize=12)
        ax.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: f"{int(x):,}"))
        
        step = max(1, len(common_dates) // 12)
        ax.xaxis.set_major_locator(plt.MultipleLocator(step))
        plt.xticks(rotation=30)
        ax.legend(fontsize=10, loc="upper left")
        
        # 🖱️ 智慧提示框 (純文字安全版)
        tooltip_right_top = ax.annotate("", xy=(0, 0), xytext=(20, 20), textcoords="offset points", bbox=dict(boxstyle="round,pad=0.5", facecolor="#252538", alpha=0.9, edgecolor="#7f849c"), arrowprops=dict(arrowstyle="->", color="#7f849c"), fontsize=9, color=TEXT_LIGHT)
        tooltip_left_top = ax.annotate("", xy=(0, 0), xytext=(-320, 20), textcoords="offset points", bbox=dict(boxstyle="round,pad=0.5", facecolor="#252538", alpha=0.9, edgecolor="#7f849c"), arrowprops=dict(arrowstyle="->", color="#7f849c"), fontsize=9, color=TEXT_LIGHT)
        tooltip_right_bottom = ax.annotate("", xy=(0, 0), xytext=(20, -250), textcoords="offset points", bbox=dict(boxstyle="round,pad=0.5", facecolor="#252538", alpha=0.9, edgecolor="#7f849c"), arrowprops=dict(arrowstyle="->", color="#7f849c"), fontsize=9, color=TEXT_LIGHT)
        tooltip_left_bottom = ax.annotate("", xy=(0, 0), xytext=(-320, -250), textcoords="offset points", bbox=dict(boxstyle="round,pad=0.5", facecolor="#252538", alpha=0.9, edgecolor="#7f849c"), arrowprops=dict(arrowstyle="->", color="#7f849c"), fontsize=9, color=TEXT_LIGHT)
        
        for t_widget in [tooltip_right_top, tooltip_left_top, tooltip_right_bottom, tooltip_left_bottom]: t_widget.set_visible(False)

        def on_mouse_move(event):
            if event.inaxes != ax:
                for t_widget in [tooltip_right_top, tooltip_left_top, tooltip_right_bottom, tooltip_left_bottom]: t_widget.set_visible(False)
                fig.canvas.draw_idle()
                return

            x_mouse = event.xdata
            if x_mouse is None: return

            idx = min(max(0, int(round(x_mouse))), len(common_dates) - 1)
            target_date = common_dates[idx]

            lines_text = [f"回測時間：{target_date}", "────────────────"]
            
            for t in self.battle_list:
                col = t["name"]
                if col in df_money_val.columns:
                    current_money = df_money_val[col].iloc[idx] 
                    profit_money = current_money - t["money"] 
                    pct_val = (current_money / t["money"] - 1) * 100
                    raw_price = df_battle[col].iloc[idx]
                    
                    lines_text.append(f"   {col} (初始: ${t['money']:,.0f}):")
                    lines_text.append(f"     - 當日市價/淨值: {raw_price:,.2f}")
                    lines_text.append(f"     - 帳面現值: ${current_money:,.0f} ({pct_val:+.1f}%) | 獲利: {profit_money:+,.0f}")
            
            lines_text.append("────────────────")
            
            total_current_val = df_money_val["投資組合總價值 (Total Portfolio)"].iloc[idx]
            total_profit = total_current_val - total_initial_principal
            total_pct = (total_current_val / total_initial_principal - 1) * 100
            
            lines_text.append(f" [投資組合總計] (總本金: ${total_initial_principal:,.0f}):")
            lines_text.append(f"     - 總資產現值: ${total_current_val:,.0f}")
            lines_text.append(f"     - 總累計報酬: {total_pct:+.1f}%")
            lines_text.append(f"     - 組合淨獲利: {total_profit:+,.0f}")
                
            tooltip_text = "\n".join(lines_text)
            x_percent = (event.x - ax.bbox.xmin) / ax.bbox.width
            y_percent = (event.y - ax.bbox.ymin) / ax.bbox.height
            
            for t_widget in [tooltip_right_top, tooltip_left_top, tooltip_right_bottom, tooltip_left_bottom]: t_widget.set_visible(False)
            anchor_y = total_current_val
            
            if y_percent > 0.55: 
                if x_percent > 0.60: 
                    tooltip_left_bottom.set_text(tooltip_text); tooltip_left_bottom.xy = (idx, anchor_y); tooltip_left_bottom.set_visible(True)
                else: 
                    tooltip_right_bottom.set_text(tooltip_text); tooltip_right_bottom.xy = (idx, anchor_y); tooltip_right_bottom.set_visible(True)
            else: 
                if x_percent > 0.60: 
                    tooltip_left_top.set_text(tooltip_text); tooltip_left_top.xy = (idx, anchor_y); tooltip_left_top.set_visible(True)
                else: 
                    tooltip_right_top.set_text(tooltip_text); tooltip_right_top.xy = (idx, anchor_y); tooltip_right_top.set_visible(True)

            fig.canvas.draw_idle()

        fig.canvas.mpl_connect("motion_notify_event", on_mouse_move)
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    root = tk.Tk()
    app = MultiComparatorApp(root)
    root.mainloop()