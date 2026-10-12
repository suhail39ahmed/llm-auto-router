import re                                        # regular expressions for pattern matching

TIERS = ["cheap", "general", "balanced", "strong"]   # ordered from cheapest to strongest

# Patterns that suggest each tool (implied intent, not keywords the user must say)
TOOL_PATTERNS = {
    "sql": r"\b(how much|how many|top \d+|total|spend|revenue|last (quarter|month|year)|per (user|customer))\b",
    "rag": r"\b(our (policy|limit|runbook)|ERR-\w+|VaR|investment policy|procedure)\b",
    "web": r"\b(today|latest|right now|current price|news|last night|this week)\b",
}

# Patterns that suggest each tier
STRONG = r"\b(should we|design|architecture|trade-?offs?|strategy|compare|vs|or .+ for us|why is)\b"
BALANCED = r"(def |\{|\[|regex|cron|function|script|query|schema|json|bug|error|returns? none)"
CHEAP = r"^(hi|hello|thanks|ok|yes|no)\b|\b(translate|classify|extract|is .+ (earlier|bigger|true))\b"

def route(prompt: str) -> dict:
    """Return {'tier': ..., 'tool': ..., 'reason': ...} for one prompt."""
    p = prompt.lower().strip()                   # normalise once

    tool = None                                  # default: no tool
    for name, pattern in TOOL_PATTERNS.items():  # first matching tool wins
        if re.search(pattern, p, re.I):
            tool = name
            break

    if re.search(STRONG, p):                     # hard reasoning beats everything
        return {"tier": "strong", "tool": tool, "reason": "strong pattern"}
    if re.search(BALANCED, p):                   # code-like or exact output
        return {"tier": "balanced", "tool": tool, "reason": "balanced pattern"}
    if tool == "sql":                            # data questions need a precise query
        return {"tier": "balanced", "tool": tool, "reason": "sql tool"}
    if re.search(CHEAP, p) or len(p.split()) <= 4:   # trivial or very short
        return {"tier": "cheap", "tool": tool, "reason": "cheap pattern/short"}
    return {"tier": "general", "tool": tool, "reason": "default"}   # everything else