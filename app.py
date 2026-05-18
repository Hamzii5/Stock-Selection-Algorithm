from flask import Flask, render_template, request, jsonify
from algorithms.greedy import Greedy
from algorithms.knapsack import Knapsack
from algorithms.brute_force import BruteForce
from services.data_loader import DataLoader
import platform
import random
import statistics
import time

app = Flask(__name__)

ALGORITHMS = {
    "greedy": {
        "label": "Greedy Algorithm",
        "family": "Greedy",
        "time": "O(n log n)",
        "space": "O(n)",
        "runner": Greedy()
    },
    "dp": {
        "label": "Dynamic Programming Knapsack",
        "family": "Dynamic Programming",
        "time": "O(nW)",
        "space": "O(W)",
        "runner": Knapsack()
    },
    "bruteforce": {
        "label": "Brute Force",
        "family": "Exhaustive Search",
        "time": "O(2^n)",
        "space": "O(n)",
        "runner": BruteForce()
    }
}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    companies = DataLoader().get_all()
    return render_template("dashboard.html", companies=companies)

@app.route("/run_experiment", methods=["POST"])
def run_experiment():
    data = request.get_json() or {}

    selected_symbols = data.get("stocks", [])
    max_n = safe_int(data.get("max_n", 50), 50)
    repetitions = safe_int(data.get("repetitions", 5), 5)
    case_type = data.get("case_type", "average")
    include_extra = bool(data.get("include_extra", False))
    custom_budget = safe_int(data.get("custom_budget", 0), 0)

    max_n = min(max(max_n, 1), 200)
    repetitions = min(max(repetitions, 1), 20)

    loader = DataLoader()
    stocks = loader.load_multiple(selected_symbols, limit=max_n if not selected_symbols else None)

    if not stocks:
        return jsonify({"error": "No valid stock data found."}), 400

    if selected_symbols:
        stocks = stocks[:max_n]

    n_values = build_n_values(len(stocks))

    algorithm_keys = ["greedy", "dp"]
    if include_extra:
        algorithm_keys.append("bruteforce")

    rows = []
    chart = []

    random.seed(301)

    for n in n_values:
        chart_row = {"n": n}

        for key in algorithm_keys:
            meta = ALGORITHMS[key]

            measured_times = []
            profits = []
            skipped = False
            budget = 1

            for _ in range(repetitions):
                run_input = choose_case(stocks, n, case_type)

                if custom_budget > 0:
                    budget = custom_budget
                else:
                    budget = make_budget(run_input)

                elapsed_ms, result = measure(meta["runner"], run_input, budget)

                if result.get("skipped"):
                    skipped = True
                    continue

                measured_times.append(elapsed_ms)
                profits.append(result.get("profit", 0))

            if measured_times:
                avg_time = round(statistics.mean(measured_times), 4)
                best_time = round(min(measured_times), 4)
                worst_time = round(max(measured_times), 4)
                avg_profit = round(statistics.mean(profits), 4) if profits else 0
            else:
                avg_time = None
                best_time = None
                worst_time = None
                avg_profit = None

            chart_row[key] = avg_time

            rows.append({
                "n": n,
                "case": case_type,
                "algorithm": meta["label"],
                "family": meta["family"],
                "avg_time_ms": avg_time,
                "best_time_ms": best_time,
                "worst_time_ms": worst_time,
                "avg_profit": avg_profit,
                "budget": budget,
                "time_complexity": meta["time"],
                "space_complexity": meta["space"],
                "repetitions": repetitions,
                "skipped": skipped
            })

        chart.append(chart_row)

    ranked_companies = sorted(
        stocks,
        key=lambda x: x.get("profit", 0) / max(x.get("weight", 1), 1),
        reverse=True
    )
    top_best = ranked_companies[:3]
    top_worst = list(reversed(ranked_companies[-3:]))

    calc_budget = custom_budget if custom_budget > 0 else 10000

    def get_single_profit(company):
        ratio = float(company.get("profit", 0)) / max(float(company.get("weight", 1)), 1.0)
        # Divide by 100 to treat the ratio as a natural percentage
        profit_value = (ratio / 100) * calc_budget
        return f"${profit_value:,.2f}"

    return jsonify({
        "setup": {
            "timer": "time.perf_counter()",
            "repetitions": repetitions,
            "case_type": case_type,
            "same_inputs": "Yes, each algorithm receives the same n, same case type, same budget rule.",
            "budget_rule": f"Custom Budget: {custom_budget}" if custom_budget > 0 else "35% of total selected stock weights for each n.",
            "dataset_size_used": len(stocks),
            "budget_used": calc_budget,
            "top_best_companies": [
                f'#{i+1} {c.get("symbol", "Unknown")} | Est. Profit: {get_single_profit(c)}'
                for i, c in enumerate(top_best)
            ],
            "top_worst_companies": [
                f'#{i+1} {c.get("symbol", "Unknown")} | Est. Profit: {get_single_profit(c)}'
                for i, c in enumerate(top_worst)
            ]
        },
        "algorithms": [
            {
                "name": ALGORITHMS[key]["label"],
                "family": ALGORITHMS[key]["family"],
                "time_complexity": ALGORITHMS[key]["time"],
                "space_complexity": ALGORITHMS[key]["space"]
            }
            for key in algorithm_keys
        ],
        "n_values": n_values,
        "rows": rows,
        "chart": chart
    })

def safe_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def build_n_values(total):
    candidates = [5, 10, 20, 50, 100, 150, 200]
    values = [n for n in candidates if n <= total]

    if total not in values:
        values.append(total)

    return sorted(set(max(1, n) for n in values))

def make_budget(stocks):
    total_weight = sum(max(1, int(stock.get("weight", 1))) for stock in stocks)
    return max(1, int(total_weight * 0.35))

def choose_case(stocks, n, case_type):
    n = min(n, len(stocks))

    def ratio(stock):
        return stock.get("profit", 0) / max(stock.get("weight", 1), 1)

    if case_type == "best":
        return sorted(stocks, key=ratio, reverse=True)[:n]

    if case_type == "worst":
        return sorted(stocks, key=ratio)[:n]

    return random.sample(stocks, n)

def measure(algorithm, stocks, budget):
    start = time.perf_counter()
    result = algorithm.solve(stocks, budget)
    end = time.perf_counter()
    return round((end - start) * 1000, 4), result

if __name__ == "__main__":
    print("🚀 Server running on http://127.0.0.1:5000")
    app.run(debug=True)