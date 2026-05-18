class Knapsack:
    """
    0/1 Knapsack using Dynamic Programming.
    Design family: Dynamic Programming.
    Space optimized from O(nW) to O(W).
    """

    def solve(self, stocks, budget):
        budget = max(1, int(budget))
        dp = [0.0] * (budget + 1)

        for stock in stocks:
            weight = max(1, int(stock.get("weight", 1)))
            profit = max(0.0, float(stock.get("profit", 0)))

            for current_budget in range(budget, weight - 1, -1):
                candidate = dp[current_budget - weight] + profit

                if candidate > dp[current_budget]:
                    dp[current_budget] = candidate

        return {
            "profit": round(dp[budget], 4),
            "cost": budget,
            "selected_count": "computed_by_dp"
        }