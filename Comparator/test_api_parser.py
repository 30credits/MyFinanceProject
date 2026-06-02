import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def clean_and_search_fund(keyword):
    """🧠 基金解碼大腦：去新水管抓資料，並精準切片成字典"""
    url = f"https://www.moneydj.com/funddj/djjson/YFundSearchJSON.djjson?q={keyword}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    response = requests.get(url, headers=headers, verify=False)
    
    # 建立一個空字典，準備裝 { "基金全名": "秘密代碼" }
    fund_dictionary = {}
    
    if response.status_code == 200:
        raw_text = response.text.strip()
        
        # 1. 先用「逗號 ,」把每一檔基金切開
        fund_items = raw_text.split(",")
        
        for item in fund_items:
            if not item: # 防呆：如果是空字串就跳過
                continue
                
            # 2. 再用「豎線 |」把代碼、全名、分類號切開
            parts = item.split("|")
            
            # 確保切開後至少有代碼和全名（長度大於2）
            if len(parts) >= 2:
                fund_code = parts[0].strip()   # 拿到代碼 (例如 TLZR7)
                fund_name = parts[1].strip()   # 拿到全名 (例如 安聯AI人工智慧...)
                
                # 塞進字典裡收藏
                fund_dictionary[fund_name] = fund_code
                
    return fund_dictionary

# ─── 🚀 測試解碼器 ───
if __name__ == "__main__":
    # 這次我們故意搜尋得更精準一點，搜「安聯台灣科技」或「安聯AI」
    my_test_input = "安聯AI" 
    
    print(f"🕵️‍♂️ 正在利用新水管搜尋並由 Python 進行結構解碼：[{my_test_input}]...")
    result_dict = clean_and_search_fund(my_test_input)
    
    if result_dict:
        print(f"\n🎉 成功！解碼大腦已將原始亂字串轉換為乾淨字典，共整理出 {len(result_dict)} 檔基金：")
        print("──────────────────────────────────────────────────")
        
        # 把解碼後的結果清清楚楚印出來
        for name, code in result_dict.items():
            print(f"🔹 基金全名: {name}")
            print(f"   ➔ 解析代碼: {code}")
            print("──────────────────────────────────────────────────")
            
        # 💡 防呆檢查：看看使用者輸入的字，有沒有完美命中的基金？
        # 比如我們試著找看看有沒有包含「AT累積類股(美元)」的基金
        print("\n🔍 【防呆測試】模擬使用者想要精準尋找「含有 科技 或 美元 的基金」：")
        for name in result_dict.keys():
            if "美元" in name:
                print(f"🎯 成功幫使用者過濾出：{name} ➔ 代碼為 {result_dict[name]}")
                
    else:
        print("\n❌ 解碼失敗，或找不到任何相關基金。")