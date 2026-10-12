import os, json, time                            # env vars, JSONL, timing
from concurrent.futures import ThreadPoolExecutor   # run several prompts at once
from dotenv import load_dotenv                   # load .env
from openai import OpenAI                        # Foundry v1 client
from src.router.llm_router import route          # the router under test

load_dotenv()                                    # read .env
client = OpenAI(base_url=os.environ["LLM_BASE_URL"],
                api_key=os.environ["LLM_API_KEY"],
                timeout=60, max_retries=1)       # give up on a hung call after 60s

DEPLOY = {t: os.environ[f"MODEL_{t.upper()}"] for t in ["cheap", "general", "balanced", "strong"]}  # tier -> deployment

# USD per 1M tokens (input, output)
PRICE = {
    "cheap":    (0.075, 0.30),   # Phi-4-mini-instruct (Azure price list)
    "general":  (0.10, 0.30),    # Mistral-small-2503 - UNVERIFIED, confirm in Foundry
    "balanced": (0.25, 2.00),    # gpt-5-mini, Global Standard (Azure price list)
    "strong":   (2.50, 15.00),   # gpt-5.4, Global Standard (Azure price list)
}

def call(tier: str, prompt: str):
    """Run one prompt on one tier; return (cost_usd, seconds)."""
    extra = {"reasoning_effort": "minimal"} if tier == "balanced" else {}   # cut gpt-5-mini's hidden tokens
    start = time.perf_counter()                  # start timer
    r = client.chat.completions.create(model=DEPLOY[tier],
                                       messages=[{"role": "user", "content": prompt}],
                                       timeout=120 if tier == "strong" else 60,   # strong gets more time
                                       **extra)
    secs = time.perf_counter() - start           # latency
    pin, pout = PRICE[tier]                      # prices for this tier
    cost = (r.usage.prompt_tokens * pin + r.usage.completion_tokens * pout) / 1_000_000
    return cost, secs

def one(r):
    """Route one prompt, run it on the routed tier and on strong."""
    try:
        tier = route(r["prompt"])["tier"]        # router decision
        rc, rs = call(tier, r["prompt"])         # routed path
        sc, ss = call("strong", r["prompt"])     # baseline: always strong
        print(f"{r['id']} -> {tier:8}  ({rs:.1f}s vs {ss:.1f}s)", flush=True)
        return tier, rc, rs, sc, ss
    except Exception as e:                       # one failure shouldn't stop the run
        print(f"    skipped {r['id']}: {type(e).__name__}", flush=True)
        return None

rows = [json.loads(l) for l in open("eval/golden_prompts.jsonl", encoding="utf-8") if l.strip()]

with ThreadPoolExecutor(max_workers=8) as pool:  # 8 prompts in flight at once
    results = [x for x in pool.map(one, rows) if x]   # drop skipped ones

picks = {}                                       # how often each tier was chosen
for t, *_ in results:
    picks[t] = picks.get(t, 0) + 1
routed_cost = sum(x[1] for x in results); routed_time = sum(x[2] for x in results)
strong_cost = sum(x[3] for x in results); strong_time = sum(x[4] for x in results)

saving = 100 * (1 - routed_cost / strong_cost) if strong_cost else 0
print(f"\nScored {len(results)}/{len(rows)} prompts. Tier mix: {picks}")
print(f"Always strong : ${strong_cost:.4f}  total {strong_time:.0f}s")
print(f"Routed        : ${routed_cost:.4f}  total {routed_time:.0f}s")
print(f"Saving        : {saving:.1f}% cost, {strong_time - routed_time:.0f}s faster")