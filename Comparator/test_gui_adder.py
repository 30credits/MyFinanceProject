import tkinter as tk
from tkinter import messagebox, ttk
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class QuickAdderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🔑 第三步：多標的智慧加入測試器")
        self.root.geometry("500x400")
        
        # 儲存最終鎖定的對決名單
        self.battle_list = []
        
        # ─── 📥 輸入元件 ───
        frame_input = tk.Frame(root)
        frame_input.pack(pady=15, fill="x", padx=20)
        
        tk.Label(frame_input, text="輸入代號或名稱:").pack(side="left", padx=5)
        self.entry_search = tk.Entry(frame_input, width=25)
        self.entry_search.pack(side="left", padx=5)
        
        btn_add = tk.Button(frame_input, text="加入清單", command=self.process_input, bg="#89b4fa", fg="black")
        btn_add.pack(side="left", padx=5)
        
        # ─── 📋 顯示清單 ───
        tk.Label(root, text="【目前已鎖定的陣容】:").pack(anchor="w", padx=20)
        self.listbox_show = tk.Listbox(root, font=("Microsoft JhengHei", 10))
        self.listbox_show.pack(fill="both", expand=True, padx=20, pady=10)

    def search_fund_api(self, keyword):
        """運用 Will 抓到的新水管取得基金清單"""
        url = f"https://www.moneydj.com/funddj/djjson/YFundSearchJSON.djjson?q={keyword}"
        headers = {"User-Agent": "Mozilla/5.0"}
        fund_dict = {}
        try:
            res = requests.get(url, headers=headers, verify=False)
            if res.status_code == 200 and res.text.strip():
                items = res.text.strip().split(",")
                for item in items:
                    if not item: continue
                    parts = item.split("|")
                    if len(parts) >= 2:
                        fund_dict[parts[1].strip()] = parts[0].strip()
        except Exception as e:
            print(f"API 連線失敗: {e}")
        return fund_dict

    def process_input(self):
        user_input = self.entry_search.get().strip()
        if not user_input:
            messagebox.showwarning("提示", "請輸入內容！")
            return
            
        # ─── 🧠 鋼鐵防呆分流大腦：精準識別中文字 ───
        # 檢查輸入的字串中，是否「含有中文字」
        has_chinese = any('\u4e00' <= c <= '\u9fff' for c in user_input)
        
        if not has_chinese:
            # 📈 沒中文字：百分之百是台股(2330)、美股(AAPL)或帶點號的代號
            stock_code = user_input.upper()
            display_str = f"股票: {stock_code}"
            
            self.battle_list.append({"type": "stock", "code": stock_code, "name": display_str})
            self.listbox_show.insert(tk.END, f"📈 {display_str}")
            self.entry_search.delete(0, tk.END)
            print(f"✅ 成功鎖定股票：{stock_code}")
        else:
            # 🐷 含有中文字：必定是基金名稱，開啟 Will 的 YFundSearchJSON 密道
            print(f"🕵️‍♂️ 偵測到中文字串，啟動基金搜尋密道...")
            funds = self.search_fund_api(user_input)
            
            if not funds:
                messagebox.showerror("殘念", f"找不到任何跟『{user_input}』相關的基金。")
                return
                
            if len(funds) == 1:
                # 唯一命中：直接加入
                full_name = list(funds.keys())[0]
                code = funds[full_name]
                self.add_fund_to_list(full_name, code)
            else:
                # 模糊多選：彈出小視窗讓使用者選！
                self.pop_selection_window(funds)

    def pop_selection_window(self, fund_options):
        """💡 特技：當搜出多筆基金時，彈出副視窗讓使用者用滑鼠點選"""
        pop = tk.Toplevel(self.root)
        pop.title("🎯 請選擇您要比對的是哪一檔基金？")
        pop.geometry("450x300")
        pop.grab_set() # 鎖定焦點，強迫使用者選完才能回主畫面
        
        tk.Label(pop, text="搜尋結果有多筆，請點選一檔加入：", font=("Microsoft JhengHei", 10, "bold")).pack(pady=10)
        
        # 建立下拉清單或滾動 Listbox
        listbox_pop = tk.Listbox(pop, font=("Microsoft JhengHei", 9))
        listbox_pop.pack(fill="both", expand=True, padx=15, pady=5)
        
        # 把所有搜出來的基金全名塞進去
        names = list(fund_options.keys())
        for name in names:
            listbox_pop.insert(tk.END, name)
            
        def confirm_selection():
            try:
                selected_index = listbox_pop.curselection()[0]
                chosen_name = names[selected_index]
                chosen_code = fund_options[chosen_name]
                
                # 加入清單並關閉小視窗
                self.add_fund_to_list(chosen_name, chosen_code)
                pop.destroy()
            except IndexError:
                messagebox.showwarning("提示", "請先用滑鼠點選一檔基金！", parent=pop)
                
        btn_confirm = tk.Button(pop, text="確認加入", command=confirm_selection, bg="#a6e3a1", fg="black", width=15)
        btn_confirm.pack(pady=10)

    def add_fund_to_list(self, name, code):
        """將最終確認的基金塞進大陣容裡"""
        display_str = f"基金: {name} ({code})"
        self.battle_list.append({"type": "fund", "code": code, "name": name})
        self.listbox_show.insert(tk.END, f"🐷 {display_str}")
        self.entry_search.delete(0, tk.END)
        print(f"✅ 成功鎖定基金：{name} ➔ 代碼: {code}")

if __name__ == "__main__":
    root = tk.Tk()
    app = QuickAdderApp(root)
    root.mainloop()