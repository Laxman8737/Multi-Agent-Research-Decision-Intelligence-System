# API Reference
Base URL `http://localhost:8000` · OpenAPI at `/docs` · if `API_KEY` is set send `X-API-Key`.

## POST /api/research
```bash
curl -X POST localhost:8000/api/research -H 'content-type: application/json' \
  -d '{"question":"What do the sources say about India solar installed capacity in 2024 and 2025?"}'
```
`question`: string, 8–500 chars. Response (200):
```json
{"question":"...","plan":["...","..."],
 "trace":[{"agent":"Planner","ms":0.1,"summary":"4 sub-queries"}, "... Researcher, Extractor, Verifier, ConflictDetector, Writer"],
 "facts":[{"key":"capacity india installed solar 2025","subject":"India solar installed capacity","year":"2025","unit":"GW","status":"verified|conflict|single_source","sources":["Meridian Research"],"values":{"110":["Meridian Research"]}}],
 "conflicts":[{"subject":"...","year":"2024","unit":"GW","values":{"88":["A"],"118.8":["B"]}}],
 "report":"# Research brief: ...\n## Verified ... [S1]\n## Sources\n- [S1] Meridian Research",
 "flags":["quarantined sentence from Industry Ledger (prompt-injection pattern)"],
 "usage":{"model":"offline-extractive","tokens_in":998,"tokens_out":210,"usd":0.0,"inr":0.0},"total_ms":0.9,
 "tool_calls":[{"tool":"search_corpus","args":{"query":"...","k":25}}]}
```
## GET /api/tools → tool specs in LLM function-calling format · GET /api/metrics → cumulative cost · GET /api/health

## Errors
| code | meaning |
|---|---|
| 400 | blank question |
| 401 | bad/missing API key |
| 422 | validation error (question too short/long) |
Tool-argument errors inside the workflow raise `ToolError` (unknown tool, missing/extra/mistyped argument) and are never executed.
