import tkinter as tk
from tkinter import messagebox, ttk
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# ─── 🎨 圖表視覺設定 ───
plt.style.use('seaborn-v0_8-darkgrid' if 'seaborn-v0_8-darkgrid' in plt.style.available else 'default')
plt.rcParams['font.family'] = ['Microsoft JhengHei']
plt.rcParams['axes.unicode_minus'] = False

TEXT_LIGHT = "#cdd6f4"

class DCASimulatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📊 頂級定期定額與智慧逢低加碼複利模擬器")
        self.root.geometry("600x480")
        
        # ─── 📅 1. 時間軸設定 ───
        frame_date = tk.LabelFrame(root, text=" 1. 自訂回測時間軸 (預設過去三年) ")
        frame_date.pack(pady=8, fill="x", padx=20)
        
        today_obj = datetime.now()
        three_years_ago_obj = today_obj - timedelta(days=365 * 3)
        
        tk.Label(frame_date, text="開始日期:").pack(side="left", padx=10, pady=5)
        self.entry_start = tk.Entry(frame_date, font=("Microsoft JhengHei", 10), width=12)
        self.entry_start.pack(side="left", padx=5)
        self.entry_start.insert(0, three_years_ago_obj.strftime("%Y-%m-%d"))
        
        tk.Label(frame_date, text="結束日期:").pack(side="left", padx=10, pady=5)
        self.entry_end = tk.Entry(frame_date, font=("Microsoft JhengHei", 10), width=12)
        self.entry_end.pack(side="left", padx=5)
        self.entry_end.insert(0, today_obj.strftime("%Y-%m-%d"))
        
        # ─── 📥 2. 核心扣款參數設定 ───
        frame_param = tk.LabelFrame(root, text=" 2. 定期定額與智慧加碼參數 ")
        frame_param.pack(pady=8, fill="x", padx=20)
        
        # 標的物輸入
        frame_target = tk.Frame(frame_param)
        frame_target.pack(fill="x", padx=15, pady=5)
        tk.Label(frame_target, text="輸入回測標的代號 (例如 2330 或 QQQ):").pack(side="left")
        self.entry_target = tk.Entry(frame_target, font=("Microsoft JhengHei", 10, "bold"), width=10, fg="#89b4fa")
        self.entry_target.pack(side="left", padx=10)
        self.entry_target.insert(0, "2330")
        
        # 基本定期定額設定
        frame_dca = tk.Frame(frame_param)
        frame_dca.pack(fill="x", padx=15, pady=5)
        tk.Label(frame_dca, text="每月固定扣款金額 ($):").pack(side="left")
        self.entry_dca_money = tk.Entry(frame_dca, font=("Microsoft JhengHei", 10, "bold"), width=12, fg="#228b22")
        self.entry_dca_money.pack(side="left", padx=5)
        self.entry_dca_money.insert(0, "10000")
        
        tk.Label(frame_dca, text="每月扣款日 (號):").pack(side="left", padx=15)
        self.combo_day = ttk.Combobox(frame_dca, values=[str(i) for i in range(1, 29)], width=5, state="readonly")
        self.combo_day.pack(side="left")
        self.combo_day.set("6") # 預設每個月 6 號扣款
        
        # 🚀 高級逢低加碼開關
        frame_smart = tk.Frame(frame_param)
        frame_smart.pack(fill="x", padx=15, pady=8)
        self.var_use_smart = tk.BooleanVar(value=True)
        chk_smart = tk.Checkbutton(frame_smart, text="啟用智慧逢低加碼機制", variable=self.var_use_smart, font=("Microsoft JhengHei", 10, "bold"), fg="#e64553")
        chk_smart.pack(side="left")
        
        tk.Label(frame_smart, text="只要股價跌破20日均價時，當天額外大口加碼 ($):").pack(side="left", padx=5)
        self.entry_smart_money = tk.Entry(frame_smart, font=("Microsoft JhengHei", 10, "bold"), width=10, fg="#b22222")
        self.entry_smart_money.pack(side="left")
        self.entry_smart_money.insert(0, "5000")

        # ─── 🚀 3. 火力全開執行按鈕 ───
        btn_launch = tk.Button(root, text="🚀 啟動定期定額微笑曲線複利回測", font=("Microsoft JhengHei", 12, "bold"), 
                               command=self.run_dca_backtest, bg="#a6e3a1", fg="black", height=2)
        btn_launch.pack(fill="x", padx=20, pady=25)

    def run_dca_backtest(self):
        target = self.entry_target.get().strip().upper()
        start_date = self.entry_start.get().strip()
        end_date = self.entry_end.get().strip()
        
        try:
            dca_amount = float(self.entry_dca_money.get().strip())
            smart_amount = float(self.entry_smart_money.get().strip())
            dca_day = int(self.combo_day.get())
            if dca_amount <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("錯誤", "請輸入正確的扣款金額與扣款日期！")
            return
            
        if not target:
            messagebox.showwarning("提示", "請輸入股票或 ETF 代號！")
            return
            
        # 台股代號防呆自動補綴
        is_taiwan_asset = target[0].isdigit() if target else False
        actual_code = f"{target}.TW" if is_taiwan_asset else target
        
        print(f"📥 正在火速下載 {actual_code} 歷史時序數據...")
        try:
            df = yf.download(actual_code, start=start_date, end=end_date, progress=False)
            if df.empty: raise Exception
        except:
            messagebox.showerror("悲劇", f"無法取得 {target} 的歷史數據，請檢查代號或網路！")
            return
            
        # 數據清洗，取出收盤價
        df = df[['Close']].copy()
        df.columns = ['Price']
        # 計算 20 日均價作為智慧逢低加碼的臨界指標
        df['MA20'] = df['Price'].rolling(window=20).mean()
        df = df.dropna() # 割除開頭無法計算 MA20 的斷點
        
        # ─── 🧮 策略一：純定期定額核心大腦 ───
        cash_invested_normal = 0    # 累計投入本金
        shares_owned_normal = 0     # 累計持有股數
        history_principal_normal = []
        history_value_normal = []
        history_pct_normal = []
        
        # ─── 🧮 策略二：智慧逢低加碼核心大腦 ───
        cash_invested_smart = 0
        shares_owned_smart = 0
        history_principal_smart = []
        history_value_smart = []
        history_pct_smart = []
        
        last_dca_month = -1 # 用來鎖定每個月只在指定日期扣款一次
        
        # ─── ⏳ 坐上時光機，讓時間一天一天往前走 ───
        for date, row in df.iterrows():
            current_price = float(row['Price'])
            current_ma20 = float(row['MA20'])
            current_month = date.month
            current_day = date.day
            
            # 💡 判定今天是不是到了每個月設定的扣款日？
            # 如果剛好休市，則在當月看到的第一個交易日補扣款
            is_new_month_dca_trigger = (current_month != last_dca_month and current_day >= dca_day)
            
            if is_new_month_dca_trigger:
                # 執行策略一扣款（常規版）
                cash_invested_normal += dca_amount
                shares_owned_normal += dca_amount / current_price
                
                # 執行策略二扣款（智慧版基本盤）
                cash_invested_smart += dca_amount
                shares_owned_smart += dca_amount / current_price
                
                last_dca_month = current_month # 鎖定這個月，不能再重複扣常規的錢
                
            # 💡 判定今天是否觸發【智慧逢低加碼大腦】？
            # 條件：今天收盤價跌破 20日平均價，且使用者有勾選啟用
            if self.var_use_smart.get() and current_price < current_ma20:
                cash_invested_smart += smart_amount
                shares_owned_smart += smart_amount / current_price
                
            # ─── 🧾 每日收盤：即時結算兩個策略的市值與回報率 ───
            # 常規版結算
            current_market_val_normal = shares_owned_normal * current_price
            history_principal_normal.append(cash_invested_normal)
            history_value_normal.append(current_market_val_normal)
            pct_normal = ((current_market_val_normal / cash_invested_normal - 1) * 100) if cash_invested_normal > 0 else 0
            history_pct_normal.append(pct_normal)
            
            # 智慧版結算
            current_market_val_smart = shares_owned_smart * current_price
            history_principal_smart.append(cash_invested_smart)
            history_value_smart.append(current_market_val_smart)
            pct_smart = ((current_market_val_smart / cash_invested_smart - 1) * 100) if cash_invested_smart > 0 else 0
            history_pct_smart.append(pct_smart)
            
        # ─── 🎨 雙圖表左右對決渲染世界 ───
        fig, (ax_money, ax_pct) = plt.subplots(1, 2, figsize=(15, 6))
        common_dates = [d.strftime("%Y-%m-%d") for d in df.index]
        step = max(1, len(common_dates) // 10)
        
        # 📈 【左圖】：本金與市值相愛相殺對決
        # 畫出策略一的本金與市值
        ax_money.plot(common_dates, history_principal_normal, label="常規定期：累計本金(階梯線)", color="#4c4f69", linestyle="--", linewidth=1.5)
        ax_money.plot(common_dates, history_value_normal, label="常規定期：資產總市值", color="#1e66f5", linewidth=2.0)
        
        # 畫出策略二的本金與市值（如果有啟用的話）
        if self.var_use_smart.get():
            ax_money.plot(common_dates, history_principal_smart, label="智慧加碼：累計本金(逢低疊加)", color="#d20f39", linestyle=":", linewidth=1.5)
            ax_money.plot(common_dates, history_value_smart, label="智慧加碼：資產總市值", color="#df8e1d", linewidth=2.5)
            
        ax_money.set_title(f"💰 {target} 定期定額投入本金 vs 資產市現值走勢", fontsize=12, fontweight='bold')
        ax_money.set_ylabel("金額 (新台幣/美元)", fontsize=11, fontweight='bold')
        ax_money.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: f"{int(x):,}"))
        ax_money.xaxis.set_major_locator(plt.MultipleLocator(step))
        plt.setp(ax_money.get_xticklabels(), rotation=30, horizontalalignment='right')
        ax_money.legend(fontsize=9, loc="upper left")
        
        # 📉 【右圖】：雙策略累積報酬率大亂鬥
        ax_pct.plot(common_dates, history_pct_normal, label="常規定期定額 累計報酬率", color="#1e66f5", linewidth=2.0)
        if self.var_use_smart.get():
            ax_pct.plot(common_dates, history_pct_smart, label="智慧逢低加碼 累計報酬率", color="#df8e1d", linewidth=2.5)
            
        ax_pct.axhline(0, color='gray', linestyle=':', alpha=0.6)
        ax_pct.set_title(f"📈 {target} 雙策略累積報酬率 (%) 生死對決", fontsize=12, fontweight='bold')
        ax_pct.set_ylabel("累計報酬率 (%)", fontsize=11, fontweight='bold')
        ax_pct.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: f"{x:+.1f}%"))
        ax_pct.xaxis.set_major_locator(plt.MultipleLocator(step))
        plt.setp(ax_pct.get_xticklabels(), rotation=30, horizontalalignment='right')
        ax_pct.legend(fontsize=9, loc="upper left")
        
        # 🎛️ 高級中央儀表板動態看板
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
            
            if event.inaxes == ax_money:
                txt = [
                    f"📅 時間點：{common_dates[idx]}",
                    f"   當日收盤股價: {df['Price'].iloc[idx]:,.2f}",
                    "──────────────────",
                    f"  🔹 常規定期定額組：",
                    f"     - 總投入本金: ${history_principal_normal[idx]:,.0f}",
                    f"     - 資產市現值: ${history_value_normal[idx]:,.0f}"
                ]
                if self.var_use_smart.get():
                    txt.extend([
                        f"  🔸 智慧逢低加碼組：",
                        f"     - 總投入本金: ${history_principal_smart[idx]:,.0f}",
                        f"     - 資產市現值: ${history_value_smart[idx]:,.0f}"
                    ])
                box_money.set_text("\n".join(txt))
                box_money.set_visible(True)
                
            elif event.inaxes == ax_pct:
                txt = [
                    f"📅 時間點：{common_dates[idx]}",
                    "──────────────────",
                    f"  🔹 常規定期定額 報酬率: {history_pct_normal[idx]:+.2f}%"
                ]
                if self.var_use_smart.get():
                    txt.append(f"  🔸 智慧逢低加碼 報酬率: {history_pct_smart[idx]:+.2f}%")
                box_pct.set_text("\n".join(txt))
                box_pct.set_visible(True)
            fig.canvas.draw_idle()

        fig.canvas.mpl_connect("motion_notify_event", on_mouse_move)
        plt.subplots_adjust(left=0.07, right=0.95, top=0.90, bottom=0.15, wspace=0.25)
        plt.show()

if __name__ == "__main__":
    root = tk.Tk()
    app = DCASimulatorApp(root)
    root.mainloop()