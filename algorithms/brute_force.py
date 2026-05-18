from itertools import combinations

class BruteForce:
    """
    Exhaustive Search algorithm.
    Used only as an additional comparison algorithm.
    """

    def solve(self, stocks, budget):
        if len(stocks) > 18:
            return {
                "profit": None,
                "cost": None,
                "selected_count": None,
                "skipped": True,
                "reason": "Brute Force skipped when n > 18 to keep the demo fast."
            }

        best_profit = 0.0
        best_cost = 0
        best_selected = []

        for size in range(len(stocks) + 1):
            for subset in combinations(stocks, size):
                total_cost = sum(max(1, int(s.get("weight", 1))) for s in subset)
                total_profit = sum(max(0.0, float(s.get("profit", 0))) for s in subset)

                if total_cost <= budget and total_profit > best_profit:
                    best_profit = total_profit
                    best_cost = total_cost
                    best_selected = [
                        s.get("symbol", s.get("name", "Unknown"))
                        for s in subset
                    ]

        return {
            "profit": round(best_profit, 4),
            "cost": best_cost,
            "selected_count": len(best_selected),
            "selected": best_selected
        }