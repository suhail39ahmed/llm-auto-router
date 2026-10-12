import json                                      # read the JSONL file
import sys                                       # command-line arguments
from collections import Counter                  # tally the mistakes

if len(sys.argv) > 1 and sys.argv[1] == "llm":   # "llm" argument picks the LLM router
    from src.router.llm_router import route      # LLM router
else:
    from src.router.rules import route           # rule router (default)

rows = [json.loads(l) for l in open("eval/golden_prompts.jsonl", encoding="utf-8") if l.strip()]  # skip blank lines
tier_ok = tool_ok = 0                            # correct counts
misses = Counter()                               # (expected -> got) pairs

for r in rows:                                   # one golden prompt at a time
    d = route(r["prompt"])                       # ask the router
    tier_ok += d["tier"] == r["expected_tier"]   # True counts as 1
    tool_ok += d["tool"] == r["tool"]            # tool match (None == None counts)
    if d["tier"] != r["expected_tier"]:          # print every tier mistake
        misses[(r["expected_tier"], d["tier"])] += 1
        print(f'MISS {r["id"]} want={r["expected_tier"]:8} got={d["tier"]:8} {r["prompt"][:60]}')

print(f"\nTier accuracy: {tier_ok}/{len(rows)}   Tool accuracy: {tool_ok}/{len(rows)}")
print("Most common mistakes:", misses.most_common(5))