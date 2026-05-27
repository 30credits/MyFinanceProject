import tkinter as tk
from tkinter import messagebox
import yfinance as yf
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# =====================================================================
# 核心大腦：按下按鈕後的繪圖邏輯（0% 基準點歸零魔法）
# =====================================================================
def generate_comparison_chart():
    raw_tickers = entry_tickers.get()
    start_date = entry_start_date.get()
    end_date = entry_end_date.get()
    
    # 清理空格並轉換成陣列 (例如: "QQQ, SMH" -> ["QQQ", "SMH"])
    tickers = [t.strip().upper() for t in raw_tickers.split(",") if t.strip()]
    
    if not tickers:
        messagebox.showwarning("提示", "請至少輸入一個股票或 ETF 代號！")
        return

    # 清除舊有的圖表，避免重疊
    for widget in frame_chart_container.winfo_children():
        widget.destroy()

    # 建立 Matplotlib 的 Figure 畫布 (採用質感的暗色系主題)
    fig, ax = plt.subplots(figsize=(8, 4.8), facecolor=CARD_DARK)
    ax.set_facecolor(CARD_DARK)
    
    has_data = False
    
    # 開始跑迴圈抓資料
    for ticker in tickers:
        try:
            # progress=False 可以讓終端機不印出下載進度條，畫面更乾淨
            df = yf.download(ticker, start=start_date, end=end_date, progress=False)
            
            if not df.empty:
                # 安全路徑抓取收盤價
                if 'Adj Close' in df.columns:
                    prices = df['Adj Close']
                elif 'Close' in df.columns:
                    prices = df['Close']
                else:
                    prices = df.iloc[:, 0]
                
                # 你剛學會的基準點歸零公式
                initial_price = prices.iloc[0]
                cumulative_returns = (prices / initial_price - 1) * 100
                
                # 畫線到 ax 軸上
                ax.plot(cumulative_returns, label=ticker, linewidth=2)
                has_data = True
            else:
                print(f"❌ 找不到 {ticker} 的歷史資料。")
        except Exception as e:
            print(f"抓取 {ticker} 發生錯誤: {e}")

    if not has_data:
        messagebox.showerror("錯誤", "無法下載任何標的的數據，請檢查網路或代號是否正確！(台股需加 .TW)")
        return

    # 圖表細節美化
    ax.set_title(f"114 Year Performance Comparison ({start_date} ~ {end_date})", color=ACCENT_GOLD, fontsize=12, fontweight='bold', pad=15)
    ax.set_xlabel("Date", color=TEXT_MUTED, fontsize=9)
    ax.set_ylabel("Cumulative Return (%)", color=TEXT_MUTED, fontsize=9)
    
    # 調整坐標軸顏色
    ax.tick_params(colors=TEXT_LIGHT, labelsize=8)
    for spine in ax.spines.values():
        spine.set_color("#45475a") 
        
    ax.axhline(0, color='#f38ba8', linestyle='--', linewidth=1, alpha=0.6) # 0% 基準線
    ax.legend(facecolor=CARD_DARK, edgecolor="#45475a", labelcolor=TEXT_LIGHT, fontsize=9)
    ax.grid(True, color="#313244", alpha=0.5)
    fig.tight_layout()

    # 將 Matplotlib 圖表嵌入 Tkinter 畫布中
    chart_canvas = FigureCanvasTkAgg(fig, master=frame_chart_container)
    chart_canvas.draw()
    chart_canvas.get_tk_widget().pack(fill="both", expand=True)

# =====================================================================
# UI 介面層：獨立的主視窗
# =====================================================================
root = tk.Tk()
root.title("114年 市場績效比較器 v1.0")
root.geometry("800x600")

# 延用你最熟悉的質感暗色系配色
BG_DARK = "#1e1e2e"      
CARD_DARK = "#252538"    
TEXT_LIGHT = "#cdd6f4"   
TEXT_MUTED = "#a6adc8"   
ACCENT_PURPLE = "#cba6f7" 
ACCENT_GOLD = "#f9e2af"   

root.configure(bg=BG_DARK)

# 上方控制面板
frame_control = tk.Frame(root, bg=CARD_DARK, padx=15, pady=15)
frame_control.pack(side="top", fill="x", padx=15, pady=10)

# 輸入標的
tk.Label(frame_control, text="股票/ETF代號 (英文逗號隔開):", bg=CARD_DARK, fg=TEXT_LIGHT, font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="e", padx=5, pady=5)
entry_tickers = tk.Entry(frame_control, bg="#313244", fg="#ffffff", insertbackground="white", bd=0, width=22)
entry_tickers.insert(0, "QQQ, SMH, SOXX") # 預設初始標的
entry_tickers.grid(row=0, column=1, sticky="w", padx=5, pady=5, ipady=3)

# 輸入時間（預設鎖定 114 年 / 2025 年）
tk.Label(frame_control, text="開始日期:", bg=CARD_DARK, fg=TEXT_LIGHT, font=("Arial", 10)).grid(row=0, column=2, sticky="e", padx=5, pady=5)
entry_start_date = tk.Entry(frame_control, bg="#313244", fg="#ffffff", insertbackground="white", bd=0, width=12)
entry_start_date.insert(0, "2025-01-01")
entry_start_date.grid(row=0, column=3, sticky="w", padx=5, pady=5, ipady=3)

tk.Label(frame_control, text="結束日期:", bg=CARD_DARK, fg=TEXT_LIGHT, font=("Arial", 10)).grid(row=0, column=4, sticky="e", padx=5, pady=5)
entry_end_date = tk.Entry(frame_control, bg="#313244", fg="#ffffff", insertbackground="white", bd=0, width=12)
entry_end_date.insert(0, "2025-12-31")
entry_end_date.grid(row=0, column=5, sticky="w", padx=5, pady=5, ipady=3)

# 繪圖按鈕
btn_compare = tk.Button(frame_control, text="📊 繪製對比圖", command=generate_comparison_chart, bg=ACCENT_PURPLE, fg=BG_DARK, font=("Arial", 10, "bold"), bd=0, cursor="hand2", padx=15)
btn_compare.grid(row=0, column=6, padx=15, pady=5, ipady=2)

# 下方圖表顯示區
frame_chart_container = tk.Frame(root, bg=BG_DARK)
frame_chart_container.pack(side="bottom", fill="both", expand=True, padx=15, pady=10)

# 綁定 Enter 鍵，輸入完直接按 Enter 也能畫圖
entry_tickers.bind("<Return>", lambda e: generate_comparison_chart())

# 啟動時自動先畫一次預設圖
generate_comparison_chart()

root.mainloop()