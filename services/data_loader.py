import csv
import os

class DataLoader:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(__file__))
        self.dataset_dir = os.path.join(self.base_dir, "dataset")
        self.archive_dir = os.path.join(self.dataset_dir, "archive")
        self.names_file = os.path.join(self.dataset_dir, "company_names.csv")
        self.names_map = self.load_names()

    def load_names(self):
        names = {}

        if not os.path.exists(self.names_file):
            print("company_names.csv not found:", self.names_file)
            return names

        with open(self.names_file, newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for row in reader:
                symbol = (row.get("symbol") or "").strip()
                name = (row.get("name") or symbol).strip()

                if symbol:
                    names[symbol] = name

        return names

    def get_all(self):
        companies = []

        if not os.path.exists(self.archive_dir):
            print("Archive folder not found:", self.archive_dir)
            return companies

        for filename in os.listdir(self.archive_dir):
            if filename.lower().endswith(".csv") and not filename.startswith("._"):
                symbol = filename.replace(".csv", "").strip()

                companies.append({
                    "symbol": symbol,
                    "name": self.names_map.get(symbol, symbol)
                })

        companies.sort(key=lambda company: company["name"])
        return companies

    def get_symbols(self):
        return [company["symbol"] for company in self.get_all()]

    def load_multiple(self, symbols=None, limit=None):
        if not symbols:
            symbols = self.get_symbols()

        if limit:
            symbols = symbols[:int(limit)]

        stocks = []

        for symbol in symbols:
            stock = self.load_one(symbol)

            if stock:
                stocks.append(stock)

        return stocks

    def load_one(self, symbol):
        path = os.path.join(self.archive_dir, f"{symbol}.csv")

        if not os.path.exists(path):
            return None

        prices = []

        with open(path, newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for row in reader:
                try:
                    close_price = float(row.get("Close", 0) or 0)

                    if close_price > 0:
                        prices.append(close_price)

                except ValueError:
                    continue

        if len(prices) < 2:
            return None

        first_price = prices[0]
        last_price = prices[-1]
        profit = last_price - first_price

        return {
            "symbol": symbol,
            "name": self.names_map.get(symbol, symbol),
            "cost": round(first_price, 4),
            "weight": max(1, int(round(first_price))),
            "profit": round(max(0, profit), 4),
            "start_price": round(first_price, 4),
            "end_price": round(last_price, 4),
            "records": len(prices)
        }