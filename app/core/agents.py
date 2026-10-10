"""Multi-agent research workflow: Planner -> Researcher -> Extractor -> Verifier -> ConflictDetector -> Writer.
Agents are plain functions over a shared state dict (LangGraph-compatible). Offline reference agents are rule-based;
LLM variants plug in behind the same signatures (see README)."""
import re, time
from collections import defaultdict
from .bm25 import tokenize
from .cost import CostTracker, est_tokens
from .guard import scan
from .tools import ToolRegistry, corpus_search_tool

CLAIM = re.compile(r"^(?P<subj>.+?) (?:was|were|reached|stood at) (?P<val>[\d.,]+) (?P<unit>million units|GW|percent|billion USD) in (?P<year>\d{4})\.?$")

def key_of(subject: str, year: str) -> str:
    return " ".join(sorted({t for t in tokenize(subject) if len(t) > 1})) + " " + year

def planner(s):
    q = s["question"]; parts = [p.strip() for p in re.split(r"\band\b|;|,", q) if len(p.strip()) > 8]
    years = re.findall(r"\b(20\d\d)\b", q); stem = re.sub(r"\b20\d\d\b", "", q)
    subs = [q] + [p for p in parts if p != q]
    subs += [f"{stem.strip()} {y}" for y in years]
    return {"plan": list(dict.fromkeys(subs))}

def researcher(s, tools: ToolRegistry):
    seen, ev = set(), []
    for sq in s["plan"]:
        for h in tools.call("search_corpus", {"query": sq, "k": 25}):
            k = (h["source"], h["sentence"])
            if k not in seen: seen.add(k); ev.append(h)
    return {"evidence": ev}

def extractor(s):
    claims, flags = [], list(s.get("flags", []))
    qt = set(tokenize(s.get("question", "")))  # scope: keep only claims whose subject overlaps the question (>=2 tokens)
    for h in s["evidence"]:
        if scan(h["sentence"]):  # injection attempt inside a source: quarantine, never extract from it
            flags.append(f"quarantined sentence from {h['source']} (prompt-injection pattern)"); continue
        for sent in re.split(r"(?<=[.!?])\s+", h["sentence"]):
            m = CLAIM.match(sent.strip())
            if m and (not qt or len({t for t in tokenize(m["subj"]) if len(t) > 1} & qt) >= 2): claims.append({"key": key_of(m["subj"], m["year"]), "subject": m["subj"], "year": m["year"], "value": float(m["val"].replace(",", "")),
                                 "unit": m["unit"], "source": h["source"], "text": sent.strip()})
    return {"claims": claims, "flags": flags}

def verifier(s):
    by = defaultdict(list)
    for c in s["claims"]: by[c["key"]].append(c)
    facts = []
    for k, cs in by.items():
        vals = defaultdict(set)
        for c in cs: vals[c["value"]].add(c["source"])
        srcs = sorted({c["source"] for c in cs})
        status = "conflict" if len(vals) > 1 else ("verified" if len(srcs) >= 2 else "single_source")
        facts.append({"key": k, "subject": cs[0]["subject"], "year": cs[0]["year"], "unit": cs[0]["unit"], "status": status, "sources": srcs,
                      "values": {f"{v:g}": sorted(x) for v, x in vals.items()}})
    return {"facts": sorted(facts, key=lambda f: (f["subject"], f["year"]))}

def conflict_detector(s):
    return {"conflicts": [{"key": f["key"], "subject": f["subject"], "year": f["year"], "unit": f["unit"], "values": f["values"]} for f in s["facts"] if f["status"] == "conflict"]}

def writer(s):
    order = {"verified": "Verified (2+ independent sources agree)", "single_source": "Single-source (treat with caution)", "conflict": "Conflicting evidence (do not rely on either value)"}
    ids = {src: i + 1 for i, src in enumerate(sorted({x for f in s["facts"] for x in f["sources"]}))}
    out = [f"# Research brief: {s['question']}"]
    for st, title in order.items():
        rows = [f for f in s["facts"] if f["status"] == st]
        if not rows: continue
        out.append(f"\n## {title}")
        for f in rows:
            if st == "conflict":
                vs = "; ".join(f"{v} {f['unit']} " + ",".join(f"[S{ids[x]}]" for x in xs) for v, xs in f["values"].items())
                out.append(f"- {f['subject']} ({f['year']}): sources disagree — {vs}")
            else:
                v = next(iter(f["values"])); out.append(f"- {f['subject']} ({f['year']}): {v} {f['unit']} " + ",".join(f"[S{ids[x]}]" for x in f["sources"]))
    out.append("\n## Sources\n" + "\n".join(f"- [S{i}] {src}" for src, i in ids.items()))
    return {"report": "\n".join(out), "source_ids": ids}

class ResearchSystem:
    def __init__(self, docs):
        self.docs = {d["id"]: d for d in docs}; self.tools = ToolRegistry(); fn, schema = corpus_search_tool(docs)
        self.tools.register("search_corpus", schema, fn); self.cost = CostTracker()
    def run(self, question: str) -> dict:
        s = {"question": question, "flags": []}; trace = []; self.tools.log.clear()
        for name, fn in [("Planner", planner), ("Researcher", lambda st: researcher(st, self.tools)), ("Extractor", extractor),
                         ("Verifier", verifier), ("ConflictDetector", conflict_detector), ("Writer", writer)]:
            t0 = time.perf_counter(); s.update(fn(s)); ms = round((time.perf_counter() - t0) * 1000, 2)
            trace.append({"agent": name, "ms": ms, "summary": {"Planner": f"{len(s.get('plan', []))} sub-queries", "Researcher": f"{len(s.get('evidence', []))} evidence sentences via {len(self.tools.log)} tool calls",
                          "Extractor": f"{len(s.get('claims', []))} claims, {len([f for f in s['flags'] if 'quarantined' in f])} quarantined", "Verifier": f"{len(s.get('facts', []))} facts classified",
                          "ConflictDetector": f"{len(s.get('conflicts', []))} conflicts", "Writer": "cited report"}.get(name, "")})
        usage = self.cost.add("offline-extractive", est_tokens(question + str(s["evidence"])), est_tokens(s["report"]))
        return {"question": question, "plan": s["plan"], "trace": trace, "facts": s["facts"], "conflicts": s["conflicts"], "report": s["report"],
                "flags": s["flags"], "usage": usage, "total_ms": round(sum(t["ms"] for t in trace), 2), "tool_calls": list(self.tools.log)}
