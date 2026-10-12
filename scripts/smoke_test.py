import os                                   # read environment variables
import time                                 # time each call
from dotenv import load_dotenv              # loads .env into the environment
from openai import OpenAI                   # OpenAI client, works with Foundry's v1 endpoint

load_dotenv()                               # read .env from the repo root

client = OpenAI(                            # one client for all four deployments
    base_url=os.environ["FOUNDRY_ENDPOINT"],    # .../openai/v1/
    api_key=os.environ["FOUNDRY_API_KEY"],      # your Foundry key
)

MODELS = {                                  # role -> deployment name from .env
    "cheap": os.environ["MODEL_CHEAP"],
    "general": os.environ["MODEL_GENERAL"],
    "balanced": os.environ["MODEL_BALANCED"],
    "strong": os.environ["MODEL_STRONG"],
}

PROMPT = "In one sentence, what is model routing?"   # same prompt for a fair comparison

for role, deployment in MODELS.items():     # try each model in turn
    start = time.perf_counter()             # start the timer
    try:
        resp = client.chat.completions.create(
            model=deployment,               # the deployment name picks the model
            messages=[{"role": "user", "content": PROMPT}],
        )
        secs = time.perf_counter() - start  # how long the call took
        text = resp.choices[0].message.content.strip()   # the answer text
        usage = resp.usage                  # token counts, which you'll need later for cost
        print(f"[OK]   {role:8} {deployment:22} {secs:5.1f}s  "
              f"in={usage.prompt_tokens} out={usage.completion_tokens}")
        print(f"       {text}\n")
    except Exception as e:                  # one failure shouldn't stop the other models
        print(f"[FAIL] {role:8} {deployment:22} {type(e).__name__}: {e}\n")