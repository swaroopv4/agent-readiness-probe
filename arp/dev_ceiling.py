"""Exactly four development attempts for the authorized ceiling check; no M3 runs."""
from pathlib import Path
import json
from .adapters import AdapterConfig
from .m2 import ROOT, run_batch

MODEL = "gpt-5.6-luna"
EFFORT = "low"


def catalog_config(catalog):
    models = json.loads(catalog.read_text(encoding="utf-8"))
    model = next((m for m in models if m["slug"] == MODEL and m["visibility"] == "list"), None)
    if not model or EFFORT not in [v["effort"] for v in model["supported_reasoning_levels"]]:
        raise ValueError("Required smallest standard coding model/reasoning absent from live login catalog; stop")
    return AdapterConfig(MODEL, EFFORT)


def main():
    config = catalog_config(ROOT/"artifacts/private/dev-catalog-001/catalog.json")
    run_batch(ROOT/"artifacts/private/m1-v7", ROOT/"artifacts/private/dev-ceiling-001",
              Path.home()/".codex/auth.json", "arp-m2-agent:linux-v1", "arp-m2-proxy:linux-v1",
              ceiling_config=config)


if __name__ == "__main__": main()
