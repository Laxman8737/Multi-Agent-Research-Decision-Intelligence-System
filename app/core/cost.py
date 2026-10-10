"""Token + cost tracking. USD per 1M tokens (input, output); edit PRICES for your provider."""
PRICES = {"offline-extractive": (0.0, 0.0), "gpt-4o-mini": (0.15, 0.60), "claude-haiku": (0.80, 4.00)}
USD_INR = 84.0

def est_tokens(text: str) -> int:
    return max(1, len(text) // 4)

class CostTracker:
    def __init__(self):
        self.reset()
    def reset(self):
        self.calls = self.tin = self.tout = 0; self.usd = 0.0
    def add(self, model: str, tin: int, tout: int) -> dict:
        pi, po = PRICES.get(model, (0.0, 0.0)); usd = (tin * pi + tout * po) / 1e6
        self.calls += 1; self.tin += tin; self.tout += tout; self.usd += usd
        return {"model": model, "tokens_in": tin, "tokens_out": tout, "usd": round(usd, 6), "inr": round(usd * USD_INR, 4)}
    def summary(self) -> dict:
        return {"calls": self.calls, "tokens_in": self.tin, "tokens_out": self.tout, "usd": round(self.usd, 6), "inr": round(self.usd * USD_INR, 4)}
