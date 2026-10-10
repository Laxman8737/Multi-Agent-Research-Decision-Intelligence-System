"""Okapi BM25 (no external deps) + shared tokenizer."""
import math, re
from collections import Counter

_TOK = re.compile(r"[a-z0-9]+")
STOP = set("a an the of to in on for and or is are be by with at as it its this that from what how who when which do does i my we our you your can".split())

def tokenize(text: str) -> list[str]:
    return [w for w in _TOK.findall(text.lower()) if w not in STOP]

class BM25:
    def __init__(self, docs: list[str], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.tf = [Counter(tokenize(d)) for d in docs]
        self.len = [sum(c.values()) for c in self.tf]
        self.avg = (sum(self.len) / len(docs)) if docs else 0.0
        df = Counter()
        for c in self.tf:
            df.update(c.keys())
        n = len(docs)
        self.idf = {t: math.log(1 + (n - f + .5) / (f + .5)) for t, f in df.items()}

    def scores(self, query: str) -> list[float]:
        q = tokenize(query)
        out = []
        for tf, ln in zip(self.tf, self.len):
            s = 0.0
            for t in q:
                f = tf.get(t)
                if f:
                    s += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * ln / (self.avg or 1)))
            out.append(s)
        return out
