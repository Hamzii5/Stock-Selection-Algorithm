import os
import csv
import yfinance as yf

# 📁 مكان ملفات الأسهم
DATASET_PATH = "dataset/archive"

# 📄 الملف اللي بنسويّه
OUTPUT_FILE = "dataset/company_names.csv"

results = []

for file in os.listdir(DATASET_PATH):
    if file.endswith(".csv"):

        symbol = file.replace(".csv", "")

        try:
            stock = yf.Ticker(symbol)

            # 🔥 جلب اسم الشركة
            name = stock.info.get("longName", symbol)

            print(symbol, "→", name)

            results.append({
                "symbol": symbol,
                "name": name
            })

        except:
            print("Error:", symbol)

            results.append({
                "symbol": symbol,
                "name": symbol
            })

# 💾 حفظ الملف
with open(OUTPUT_FILE, "w", newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=["symbol", "name"])
    writer.writeheader()
    writer.writerows(results)

print("\n✅ DONE!")