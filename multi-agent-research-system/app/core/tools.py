"""Tool registry with JSON-schema-style argument validation (the same shape LLM tool-calling APIs use)."""
from .bm25 import BM25

class ToolError(ValueError): ...

class ToolRegistry:
    def __init__(self):
        self.tools, self.log = {}, []
    def register(self, name, schema, fn):
        self.tools[name] = (schema, fn)
    def specs(self):  # pass to an LLM provider as `tools=`
        return [{"type": "function", "function": {"name": n, "parameters": s}} for n, (s, _) in self.tools.items()]
    def call(self, name, args: dict):
        if name not in self.tools: raise ToolError(f"unknown tool {name}")
        schema, fn = self.tools[name]; types = {"string": str, "integer": int}
        for k in schema.get("required", []):
            if k not in args: raise ToolError(f"{name}: missing argument '{k}'")
        for k, v in args.items():
            spec = schema["properties"].get(k)
            if not spec: raise ToolError(f"{name}: unexpected argument '{k}'")
            if not isinstance(v, types[spec["type"]]): raise ToolError(f"{name}: '{k}' must be {spec['type']}")
        self.log.append({"tool": name, "args": args}); return fn(**args)

def corpus_search_tool(docs):
    import re
    sents = [(d["id"], d["title"], s) for d in docs for s in re.split(r"(?<=[.!?])\s+", d["text"]) if s]
    bm = BM25([s for _, _, s in sents])
    def search(query: str, k: int = 20):
        sc = bm.scores(query); idx = sorted(range(len(sents)), key=lambda i: -sc[i])[:k]
        return [{"source": sents[i][0], "title": sents[i][1], "sentence": sents[i][2], "score": round(sc[i], 3)} for i in idx if sc[i] > 0]
    return search, {"type": "object", "required": ["query"], "properties": {"query": {"type": "string"}, "k": {"type": "integer"}}}
