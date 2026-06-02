import requests
import urllib3
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime

# 強迫跳過 SSL 檢查的警告文字閉嘴
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ─── 🎨 【補齊暗黑風色彩定義（修正報錯核心）】 ───
BG_DARK = "#1e1e2e"
CARD_DARK = "#252538"
TEXT_LIGHT = "#cdd6f4"
TEXT_MUTED = "#7f849c"
ACCENT_BLUE = "#89b4fa"

# ─── 💅 設定高質感圖表主題與中文生存字型 ───
plt.style.use('seaborn-v0_8-darkgrid' if 'seaborn-v0_8-darkgrid' in plt.style.available else 'default')
plt.rcParams['font.family'] = ['Microsoft JhengHei'] # 強制注入微軟正黑體
plt.rcParams['axes.unicode_minus'] = False           # 正常顯示負號

def get_fund_history(fund_code, start_date, end_date):
    """昨天的特技升級：動態點菜代碼組裝，沒收一整年基金淨值"""
    print(f"📥 正在從 Moneydj 秘密通道提取基金 [{fund_code}] 的歷史數據...")
    s_dt = datetime.strptime(start_date, "%Y-%m-%d")
    e_dt = datetime.strptime(end_date, "%Y-%m-%d")
    url = f"https://www.moneydj.com/funddj/bcd/tBCDNavList.djbcd?a={fund_code}&B={s_dt.year}-{s_dt.month}-{s_dt.day}&C={e_dt.year}-{e_dt.month}-{e_dt.day}&D="
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    response = requests.get(url, headers=headers, verify=False)
    
    fund_data = {}
    if response.status_code == 200:
        raw_data = response.text.strip()
        all_elements = raw_data.split(",")
        
        # 🛡️ 【全自動防黏連安全檢查】
        cleaned_elements = []
        for item in all_elements:
            item = item.strip()
            if len(item) > 8 and item.isdigit() == False:
                date_part = item[:8]
                value_part = item[8:]
                cleaned_elements.append(date_part)
                cleaned_elements.append(value_part)
            else:
                cleaned_elements.append(item)
        
        half_index = len(cleaned_elements) // 2
        date_list = cleaned_elements[:half_index]
        value_list = cleaned_elements[half_index:]
        
        for d_str, v_str in zip(date_list, value_list):
            if d_str and v_str:
                standard_date = f"{d_str[0:4]}-{d_str[4:6]}-{d_str[6:8]}"
                try:
                    fund_data[standard_date] = float(v_str.strip())
                except:
                    pass
    return fund_data

def get_stock_history(stock_id, start_date, end_date):
    """yfinance 瞬間下載股票歷史價"""
    print(f"📈 正在透過 yfinance 下載股票 [{stock_id}] 的歷史數據...")
    stock_code = f"{stock_id}.TW"
    df = yf.download(stock_code, start=start_date, end=end_date, progress=False)
    
    stock_data = {}
    for date, row in df.iterrows():
        date_str = date.strftime("%Y-%m-%d")
        stock_data[date_str] = float(row['Close'].iloc[0] if hasattr(row['Close'], 'iloc') else row['Close'])
    return stock_data

# ─── 🚀 【世紀大對決主程式】 ───
if __name__ == "__main__":
    target_stock = "2330"     # 股票：台積電
    target_fund = "ACDD04"    # 基金：安聯台灣科技基金
    fund_name = "安聯台灣科技基金"
    
    start = "2025-06-02"
    end = "2026-06-02"
    
    fund_history = get_fund_history(target_fund, start, end)
    stock_history = get_stock_history(target_stock, start, end)
    
    common_dates = sorted(list(set(fund_history.keys()) & set(stock_history.keys())))
    
    if not common_dates:
        print("❌ 錯誤：找不到重疊的交易日期。")
    else:
        first_date = common_dates[0]
        base_stock_price = stock_history[first_date]
        base_fund_price = fund_history[first_date]
        
        final_dates = []
        stock_returns = []
        fund_returns = []
        
        for date in common_dates:
            final_dates.append(date)
            s_ret = ((stock_history[date] / base_stock_price) - 1) * 100
            stock_returns.append(s_ret)
            f_ret = ((fund_history[date] / base_fund_price) - 1) * 100
            fund_returns.append(f_ret)
            
        # 📊 計算最大回撤 (MDD)
        def calculate_mdd(returns_list):
            max_value = 0
            max_dd = 0
            for r in returns_list:
                current_value = 100 + r 
                if current_value > max_value:
                    max_value = current_value
                dd = (max_value - current_value) / max_value * 100
                if dd > max_dd:
                    max_dd = dd
            return max_dd

        stock_mdd = calculate_mdd(stock_returns)
        fund_mdd = calculate_mdd(fund_returns)
        
        # 計算歷史勝率
        fund_win_days = sum(1 for f, s in zip(fund_returns, stock_returns) if f > s)
        total_days = len(common_dates)
        win_rate = (fund_win_days / total_days) * 100
        
        # ─── 📊 建立畫布 ───
        fig, ax = plt.subplots(figsize=(11, 6))
        
        # 💡 拔除所有標題裡的 Emoji
        line_stock, = ax.plot(final_dates, stock_returns, label=f"股票: 台積電 ({target_stock})", color="#f38ba8", linewidth=2)
        line_fund, = ax.plot(final_dates, fund_returns, label=f"基金: {fund_name} ({target_fund})", color="#89b4fa", linewidth=2)
        
        ax.set_title(f"世紀大對決：股票 vs 基金 累計走勢比對 ({start} ~ {end})", fontsize=14, fontweight='bold')
        ax.set_xlabel("交易日期", fontsize=12)
        ax.set_ylabel("累計報酬率 (%)", fontsize=12)
        ax.xaxis.set_major_locator(plt.MultipleLocator(20))
        plt.xticks(rotation=30)
        ax.axhline(0, color='white', linestyle='--', linewidth=1)
        ax.legend(fontsize=11, loc="upper left")
        
        # ─── 🎯 滑鼠動態提示框元件 ───
        hover_dot_stock, = ax.plot([], [], 'o', color='#f38ba8', markersize=8, visible=False)
        hover_dot_fund, = ax.plot([], [], 'o', color='#89b4fa', markersize=8, visible=False)
        
        # ─── 🎯 滑鼠動態提示框元件（建立左右雙生框，完美閃過新版所有版本坑） ───
        # 右噴框（平常在用）
        tooltip_right = ax.annotate(
            "", xy=(0, 0), xytext=(20, 20), textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#252538", alpha=0.9, edgecolor="#7f849c"),
            arrowprops=dict(arrowstyle="->", color="#7f849c"),
            fontsize=10, color=TEXT_LIGHT
        )
        # 左噴框（靠右撞牆時用）
        tooltip_left = ax.annotate(
            "", xy=(0, 0), xytext=(-160, 20), textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#252538", alpha=0.9, edgecolor="#7f849c"),
            arrowprops=dict(arrowstyle="->", color="#7f849c"),
            fontsize=10, color=TEXT_LIGHT
        )
        tooltip_right.set_visible(False)
        tooltip_left.set_visible(False)

        # ─── 🖱️ 滑鼠移動事件監聽器 ───
        def on_mouse_move(event):
            if event.inaxes != ax:
                tooltip_right.set_visible(False)
                tooltip_left.set_visible(False)
                hover_dot_stock.set_visible(False)
                hover_dot_fund.set_visible(False)
                fig.canvas.draw_idle()
                return

            x_mouse = event.xdata
            if x_mouse is None:
                return

            idx = min(max(0, int(round(x_mouse))), len(final_dates) - 1)
            
            target_date = final_dates[idx]
            current_s_ret = stock_returns[idx]
            current_f_ret = fund_returns[idx]

            hover_dot_stock.set_data([idx], [current_s_ret])
            hover_dot_fund.set_data([idx], [current_f_ret])
            hover_dot_stock.set_visible(True)
            hover_dot_fund.set_visible(True)

            tooltip_text = (
                f"時間：{target_date}\n"
                f"────────────────\n"
                f" 紅線股票報酬：{current_s_ret:+.1f} %\n"
                f" 藍線基金報酬：{current_f_ret:+.1f} %\n"
                f" 兩者即時價差：{current_f_ret - current_s_ret:+.1f} %"
            )
            
            # 計算滑鼠在畫布上的百分比 (0.0 ~ 1.0)
            x_percent = (event.x - ax.bbox.xmin) / ax.bbox.width
            
            # 💡 黃金雙生開關邏輯：只控制顯示與隱藏，絕不去修改位置屬性！
            if x_percent > 0.75:  # 靠右，開啟左噴框，隱藏右噴框
                tooltip_right.set_visible(False)
                
                tooltip_left.set_text(tooltip_text)
                tooltip_left.xy = (idx, (current_s_ret + current_f_ret) / 2)
                tooltip_left.set_visible(True)
            else:                  # 正常，開啟右噴框，隱藏左噴框
                tooltip_left.set_visible(False)
                
                tooltip_right.set_text(tooltip_text)
                tooltip_right.xy = (idx, (current_s_ret + current_f_ret) / 2)
                tooltip_right.set_visible(True)

            fig.canvas.draw_idle()

        fig.canvas.mpl_connect("motion_notify_event", on_mouse_move)
        
        # ─── 🏆 總戰報看板 ───
        stats_text = (
            f"[ 世紀對決終極戰報 ]\n"
            f"- 總對決交易日：{total_days} 天\n"
            f"- 基金壓制股票勝率：{win_rate:.1f} %\n"
            f"──────────────────\n"
            f" 股票最終報酬率：{stock_returns[-1]:.1f} %\n"
            f" 股票最大回撤(MDD)：-{stock_mdd:.1f} %\n"
            f"──────────────────\n"
            f" 基金最終報酬率：{fund_returns[-1]:.1f} %\n"
            f" 基金最大回撤(MDD)：-{fund_mdd:.1f} %"
        )
        ax.text(
            0.02, 0.55, stats_text, transform=ax.transAxes, 
            fontsize=10, verticalalignment='top', color=TEXT_LIGHT,
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#252538', alpha=0.8, edgecolor='#7f849c')
        )
        
        plt.tight_layout()
        print("🎨 雙生追蹤引擎全面啟動，完美相容新版 Matplotlib！")
        plt.show()