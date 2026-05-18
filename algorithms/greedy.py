class Greedy:
    """
    Greedy investment selector using profit-to-cost ratio.
    Design family: Greedy.
    """

    def solve(self, stocks, budget):
        ordered = sorted(
            stocks,
            key=lambda s: (s.get("profit", 0) / max(s.get("weight", 1), 1)),
            reverse=True
        )

        total_profit = 0.0
        total_cost = 0
        selected = []

        for stock in ordered:
            weight = stock.get("weight", 1)
            profit = stock.get("profit", 0)

            if weight <= budget - total_cost and profit > 0:
                selected.append(stock.get("symbol", stock.get("name", "Unknown")))
                total_cost += weight
                total_profit += profit

        return {
            "profit": round(total_profit, 4),
            "cost": total_cost,
            "selected_count": len(selected),
            "selected": selected
        }