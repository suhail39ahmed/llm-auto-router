import os                                         # read settings from the environment
import json                                       # parse the model's JSON reply
from dotenv import load_dotenv                    # load .env
from openai import OpenAI                         # same client as the smoke test

load_dotenv()                                     # read .env
client = OpenAI(base_url=os.environ["FOUNDRY_ENDPOINT"],   # Foundry v1 endpoint
                api_key=os.environ["FOUNDRY_API_KEY"])     # your key
ROUTER_MODEL = os.getenv("ROUTER_MODEL", os.environ["MODEL_GENERAL"])  # the model that decides; Mistral by default

SYSTEM = """You are a request router. Pick the CHEAPEST tier that answers correctly, and a tool if needed.
Tiers:
- cheap: greetings, short translation, fixed labels/classification, extracting text from the input, yes/no, single facts, unit conversions.
- general: summaries, rewrites, simple explanations of a concept.
- balanced: output that must be exactly right: code, scripts, queries, regex, cron, JSON/YAML, debugging.
- strong: design, architecture, trade-offs, multi-step reasoning, math/logic puzzles, plans, root-cause analysis.
Tools:
- rag: questions about OUR internal policies, limits, runbooks, error codes.
- sql: numbers about OUR company data (spend, customers, revenue, churn). Pair with balanced or strong.
- web: anything about current events, today's prices, recent news.
- null: none of the above.
Reply with JSON only: {"tier": "...", "tool": "...", "reason": "<10 words"}"""   # the rubric is the router's brain

VALID_TIERS = {"cheap", "general", "balanced", "strong"}   # allowed tier answers
VALID_TOOLS = {None, "rag", "sql", "web"}                  # allowed tool answers

def route(prompt: str) -> dict:
    """Ask the router model to classify one prompt."""
    try:
        resp = client.chat.completions.create(
            model=ROUTER_MODEL,                   # who decides
            messages=[{"role": "system", "content": SYSTEM},
                      {"role": "user", "content": prompt[:2000]}],   # cap length to keep routing cheap
            response_format={"type": "json_object"},                 # force JSON output
        )
        d = json.loads(resp.choices[0].message.content)              # string to dict
        tool = d.get("tool") or None                                 # "null"/"" become None
        tool = None if tool in ("null", "none") else tool            # normalise text "null"
        if d.get("tier") not in VALID_TIERS or tool not in VALID_TOOLS:   # never trust raw model output
            raise ValueError(f"bad decision: {d}")
        tier = d["tier"]                                             # the model's choice
        if tool and tier == "cheap":                                 # tool answers need synthesis
            tier = "general"                                         # so never send them to Phi
        return {"tier": tier, "tool": tool, "reason": d.get("reason", "")}   # final decision
    except Exception as e:                        # any failure falls back safely
        return {"tier": "strong", "tool": None, "reason": f"fallback: {type(e).__name__}"}   # safe = strong