import requests
import urllib3
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime

# 讓跳過 SSL 檢查的警告文字閉嘴
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ─── 🎨 設定中文與高質感圖表字型（防止 Windows 畫圖中文變愛心/框框） ───
plt.style.use('seaborn-v0_8-darkgrid' if 'seaborn-v0_8-darkgrid' in plt.style.available else 'default')
plt.rcParams['font.family'] = ['Microsoft JhengHei'] # 使用微軟正黑體
plt.rcParams['axes.unicode_minus'] = False           # 正常顯示負號


def get_fund_history(fund_code, start_date, end_date):
    """💡 昨天的特技升級：動態點菜代碼組裝，沒收一整年基金淨值"""
    print(f"📥 正在從 Moneydj 秘密通道提取基金 [{fund_code}] 的歷史數據...")
    # 自動拼裝日期格式（從 2025-06-02 換成網址要的 2025-6-2）
    s_dt = datetime.strptime(start_date, "%Y-%m-%d")
    e_dt = datetime.strptime(end_date, "%Y-%m-%d")
    url = f"https://www.moneydj.com/funddj/bcd/tBCDNavList.djbcd?a={fund_code}&B={s_dt.year}-{s_dt.month}-{s_dt.day}&C={e_dt.year}-{e_dt.month}-{e_dt.day}&D="
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    response = requests.get(url, headers=headers, verify=False)
    
    fund_data = {}
    if response.status_code == 200:
        raw_data = response.text.strip()
        
        
        all_elements = raw_data.split(",")
        
        # ─── 🛡️ 【全自動防黏連安全檢查】 ───
        # 巡邏整條清單，看看有沒有長度大於 8 的連體嬰
        cleaned_elements = []
        for item in all_elements:
            item = item.strip()
            if len(item) > 8 and item.isdigit() == False: # 長度超過8且不純是數字（帶有小數點）
                # 抓出前 8 碼當作日期（例如 20260529）
                date_part = item[:8]
                # 剩下的後半段全部當作淨值數字（例如 65.7500）
                value_part = item[8:]
                
                # 把牠們拆散，依序塞進乾淨的清單裡
                cleaned_elements.append(date_part)
                cleaned_elements.append(value_part)
            else:
                cleaned_elements.append(item)
        
        # 重新計算黃金分水嶺，這下不管哪一檔基金、哪一天出錯，統統完美通殺！
        half_index = len(cleaned_elements) // 2
        date_list = cleaned_elements[:half_index]
        value_list = cleaned_elements[half_index:]
        
        # 把資料整理成 { "2025-06-02": 65.75 } 的格式方便對齊
        for d_str, v_str in zip(date_list, value_list):
            if d_str and v_str:
                standard_date = f"{d_str[0:4]}-{d_str[4:6]}-{d_str[6:8]}"
                try:
                    fund_data[standard_date] = float(v_str.strip())
                except:
                    pass
    return fund_data

def get_stock_history(stock_id, start_date, end_date):
    """💡 你在另一個對話框學到的神技：yfinance 瞬間抽取股票歷史價"""
    print(f"📈 正在透過 yfinance 下載股票 [{stock_id}] 的歷史數據...")
    stock_code = f"{stock_id}.TW"
    df = yf.download(stock_code, start=start_date, end=end_date, progress=False)
    
    stock_data = {}
    # 把 yfinance 抓出來的 DataFrame 轉換成跟基金一樣的字典格式
    for date, row in df.iterrows():
        date_str = date.strftime("%Y-%m-%d")
        # 抓取當天的收盤價 (Close)
        stock_data[date_str] = float(row['Close'].iloc[0] if hasattr(row['Close'], 'iloc') else row['Close'])
    return stock_data

# ─── 🚀 【世紀大對決主程式】 ───
if __name__ == "__main__":
    # 🎯 填入你想要比對的代號（隨便換都通！）
    target_stock = "2330"     # 股票：台積電
    target_fund = "ACDD04"    # 基金：安聯台灣科技基金 (你圖中的第一個！)
    fund_name = "安聯台灣科技基金"
    
    # 設定對決的歷史區間（整整一年）
    start = "2025-06-02"
    end = "2026-06-02"
    
    # 1. 搬數據
    fund_history = get_fund_history(target_fund, start, end)
    stock_history = get_stock_history(target_stock, start, end)
    
    # 2. 🔀 基準點對齊大腦：尋找兩邊都有開盤交易的共同日期
    common_dates = sorted(list(set(fund_history.keys()) & set(stock_history.keys())))
    
    if not common_dates:
        print("❌ 錯誤：找不到重疊的交易日期，請檢查代號是否正確。")
    else:
        # 抓出第一天的價格當作基準起跑點
        first_date = common_dates[0]
        base_stock_price = stock_history[first_date]
        base_fund_price = fund_history[first_date]
        
        final_dates = []
        stock_returns = []
        fund_returns = []
        
        # 3. 🧮 計算每一天相較於第一天的累計報酬率 %
        for date in common_dates:
            final_dates.append(date)
            # 股票累計 % = (今天 / 第一天 - 1) * 100
            s_ret = ((stock_history[date] / base_stock_price) - 1) * 100
            stock_returns.append(s_ret)
            # 基金累計 % = (今天 / 第一天 - 1) * 100
            f_ret = ((fund_history[date] / base_fund_price) - 1) * 100
            fund_returns.append(f_ret)
            
        # 4. 📊 繪製世紀大對決折線圖
        # ─── 📊 繪製世紀大對決折線圖 ───
        fig, ax = plt.subplots(figsize=(11, 6)) # 💡 改用 fig, ax 結構才能綁定滑鼠事件
        
        # 畫股票（紅色）與基金（藍色）的線
        line_stock, = ax.plot(final_dates, stock_returns, label=f"股票: 台積電 ({target_stock})", color="#f38ba8", linewidth=2)
        line_fund, = ax.plot(final_dates, fund_returns, label=f"基金: {fund_name} ({target_fund})", color="#89b4fa", linewidth=2)
        
        # 裝飾圖表
        ax.set_title(f"世紀大對決：股票 vs 基金 累計走勢比對 ({start} ~ {end})", fontsize=14, fontweight='bold')
        ax.set_xlabel("交易日期", fontsize=12)
        ax.set_ylabel("累計報酬率 (%)", fontsize=12)
        ax.xaxis.set_major_locator(plt.MultipleLocator(20))
        plt.xticks(rotation=30)
        ax.axhline(0, color='white', linestyle='--', linewidth=1)
        ax.legend(fontsize=11, loc="upper left")
        
        # ─── 🎯 【全新解鎖：滑鼠動態提示框元件】 ───
        # 1. 建立一個平常隱藏不見、等滑鼠移過來才會現形的「動態圓點」
        hover_dot_stock, = ax.plot([], [], 'o', color='#f38ba8', markersize=8, visible=False)
        hover_dot_fund, = ax.plot([], [], 'o', color='#89b4fa', markersize=8, visible=False)
        
        # 2. 建立一個懸浮在滑鼠旁邊的「數據提示大盒子」
        tooltip = ax.annotate(
            "", xmltext=False, # 關閉 xml 格式限制
            xy=(0, 0), xytext=(20, 20), textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#252538", alpha=0.9, edgecolor="#7f849c"),
            arrowprops=dict(arrowstyle="->", color="#7f849c"),
            fontsize=10, color=TEXT_LIGHT
        )
        tooltip.set_visible(False) # 預設隱藏

        # ─── 🖱️ 【核心邏輯：滑鼠移動事件監聽器】 ───
        def on_mouse_move(event):
            # 如果滑鼠滑出圖表外面，或者還沒載入好，就直接隱藏提示框
            if event.inaxes != ax:
                tooltip.set_visible(False)
                hover_dot_stock.set_visible(False)
                hover_dot_fund.set_visible(False)
                fig.canvas.draw_idle()
                return

            # 抓取滑鼠目前在 X 軸（日期軸）的座標位置
            x_mouse = event.xdata
            if x_mouse is None:
                return

            # 💡 關鍵數學題：算出滑鼠距離哪一個交易日最近？
            idx = min(max(0, int(round(x_mouse))), len(final_dates) - 1)
            
            # 抓出那天的精準數據
            target_date = final_dates[idx]
            current_s_ret = stock_returns[idx]
            current_f_ret = fund_returns[idx]

            # 更新動態圓點的座標，讓它黏在兩條折線的該交易日頂點上！
            hover_dot_stock.set_data([idx], [current_s_ret])
            hover_dot_fund.set_data([idx], [current_f_ret])
            hover_dot_stock.set_visible(True)
            hover_dot_fund.set_visible(True)

            # 動態組裝提示框裡面的文字
            tooltip_text = (
                f"📅 日期：{target_date}\n"
                f"────────────────\n"
                f"🟥 股票報酬：{current_s_ret:+.1f} %\n"
                f"🟦 基金報酬：{current_f_ret:+.1f} %\n"
                f"📊 雙方價差：{current_f_ret - current_s_ret:+.1f} %"
            )
            
            # 設定提示框要指向哪裡、以及要顯示什麼字
            tooltip.set_text(tooltip_text)
            tooltip.xy = (idx, (current_s_ret + current_f_ret) / 2) # 指向兩條線的中間
            tooltip.set_visible(True)

            # 強迫圖表在後台悄悄重繪，更新畫面
            fig.canvas.draw_idle()

        # ─── 世紀大綁定 ───
        # 告訴 Matplotlib：只要滑鼠有在動（motion_notify_event），立刻呼叫上面的 on_mouse_move 大腦！
        fig.canvas.mpl_connect("motion_notify_event", on_mouse_move)
        
        # （原本的黑底半透明總戰報盒子維持在原位）
        stats_text = (
            f"🏆 【世紀對決終極戰報】\n"
            f"📊 總對決交易日：{total_days} 天\n"
            f"🔥 基金壓制股票勝率：{win_rate:.1f} %\n"
            f"──────────────────\n"
            f"📈 股票最終報酬率：{stock_returns[-1]:.1f} %\n"
            f"📉 股票最大回撤 (MDD)：-{stock_mdd:.1f} %\n"
            f"──────────────────\n"
            f"📈 基金最終報酬率：{fund_returns[-1]:.1f} %\n"
            f"📉 基金最大回撤 (MDD)：-{fund_mdd:.1f} %"
        )
        ax.text(
            0.02, 0.55, stats_text, transform=ax.transAxes, 
            fontsize=10, verticalalignment='top',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#252538', alpha=0.8, edgecolor='#7f849c')
        )
        
        plt.tight_layout()
        print("🎨 互動式追蹤引擎啟動成功！請用滑鼠在圖表上滑動...")
        plt.show()
        
        