import tkinter as tk

root = tk.Tk()
root.title("Modern Finance UI")
root.geometry("350x250")
root.configure(bg="#f0f0f0") # 設定背景顏色 (淡灰色)

# 定義專業字體
header_font = ("Helvetica", 14, "bold")
label_font = ("Helvetica", 10)

# 使用 grid 進行精確排版
# column 0 是左邊，column 1 是右邊
tk.Label(root, text="Wealth Manager", font=header_font, bg="#f0f0f0", fg="#333").grid(row=0, column=0, columnspan=2, pady=20)

tk.Label(root, text="Amount:", font=label_font, bg="#f0f0f0").grid(row=1, column=0, padx=10, pady=5, sticky="e")
entry_amount = tk.Entry(root, relief="sunken", bd=2) # flat 加上小邊框
entry_amount.grid(row=1, column=1, padx=10, pady=5)

tk.Label(root, text="Account:", font=label_font, bg="#f0f0f0").grid(row=2, column=0, padx=10, pady=5, sticky="e")
acc_var = tk.StringVar(value="Cash")
acc_menu = tk.OptionMenu(root, acc_var, "Cash", "Bank")
acc_menu.config(bg="white", relief="flat", bd=10)
acc_menu.grid(row=2, column=1, padx=10, pady=5, sticky="w")

# 現代化按鈕
btn_submit = tk.Button(root, text="Add Transaction", bg="#2ecc71", fg="white", 
                       font=("Helvetica", 10, "bold"), relief="flat", padx=20, pady=5)
btn_submit.grid(row=3, column=0, columnspan=2, pady=20)

root.mainloop()