import matplotlib.pyplot as plt
import pandas as pd
import requests
import yfinance as yf

# =====================================================================
# 1. 抓取台灣共同基金歷史淨值 (鉅亨網公開網頁數據源)
# =====================================================================
def get_taiwan_fund_data(fund_id):
    print(f"正在從網路下載台灣基金 (代號: {fund_id}) 的歷史淨值...")
    
    # 鉅亨網公開的基金歷史淨值接口 (這個接口回傳的是乾淨的 JSON 格式)
    url = f"https://fund.cnyes.com/api/v1/funds/{fund_id}/nav"
    
    # 設定時間參數：2025-01-01 到 2025-12-31 (114年)
    params = {
        "start": "2025-01-01",
        "end": "2025-12-31"
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        
        # 【防錯鎖一】：如果網站回傳錯誤代碼 (例如被擋)，立刻停止
        if response.status_code != 200:
            print(f"❌ 伺服器拒絕連線，錯誤代碼: {response.status_code}")
            return pd.Series()
            
        res_data = response.json()
        
        # 【防錯鎖二】：檢查拿到的資料到底是不是我們要的格式
        if "items" not in res_data or not res_data["items"]:
            print("❌ 網站回傳的資料結構不正確，可能被反爬蟲攔截。")
            return pd.Series()
            
        items = res_data["items"]
        
        # 轉換成 Pandas 表格
        df = pd.DataFrame(items)
        
        # 清洗數據：將日期與淨值挑出來
        df['date'] = pd.to_datetime(df['date'])
        df['nav'] = df['nav'].astype(float)
        
        # 排序並設定索引
        df = df.sort_values('date')
        df.set_index('date', inplace=True)
        
        return df['nav']
        
    except Exception as e:
        print(f"❌ 讀取數據時發生未知錯誤: {e}")
        return pd.Series()

# =====================================================================
# 2. 主程式：114 年 共同基金 vs 美股 QQQ
# =====================================================================
start_date = "2025-01-01"
end_date = "2025-12-31"

# 鉅亨網的「安聯台灣科技基金」代號是 A13002
fund_code = "A13002" 
stock_code = "QQQ"

# A. 抓取基金
fund_nav = get_taiwan_fund_data(fund_code)

# B. 抓取股票
print(f"正在從 yfinance 下載股票 (代號: {stock_code}) 的歷史數據...")
stock_df = yf.download(stock_code, start=start_date, end=end_date, progress=False)
stock_price = stock_df['Adj Close'] if 'Adj Close' in stock_df.columns else stock_df['Close']

# =====================================================================
# 3. 開始繪圖
# =====================================================================
if fund_nav.empty:
    print("❌ 基金資料為空，無法繪製對比圖。")
elif stock_price.empty:
    print("❌ 股票資料為空，無法繪製對比圖。")
else:
    plt.figure(figsize=(11, 5))

    # 0% 歸零魔法：基金線
    initial_fund = fund_nav.iloc[0]
    fund_return = (fund_nav / initial_fund - 1) * 100
    plt.plot(fund_return, label=f"Taiwan Fund (Allianz Tech)", linewidth=2, color='#fab387')

    # 0% 歸零魔法：股票線
    initial_stock = stock_price.iloc[0]
    stock_return = (stock_price / initial_stock - 1) * 100
    plt.plot(stock_return, label=f"US Stock ({stock_code})", linewidth=2, color='#89b4fa')

    # 美化
    plt.title("Year 114: Taiwan Fund vs US Stock Performance (2025)", fontsize=12, fontweight='bold')
    plt.xlabel("Date")
    plt.ylabel("Cumulative Return (%)")
    plt.axhline(0, color='red', linestyle='--', linewidth=1, alpha=0.5)
    plt.legend()
    plt.grid(True, alpha=0.3)

    print("📊 計算完成！正在彈出對比圖表...")
    plt.show()