"""Generic indicators.yaml loading, shared by every adapter's own content.py
(runtime scoring) and scripts/seed_indicators.py (DB seeding) so the parsing
logic exists exactly once, regardless of how many adapters exist.

Moved out of app/adapters/fair/content.py (issue #16): none of this was ever
FAIR-specific — it only became adapter-owned because there was a single
adapter's YAML to parse. A second adapter surfaced that it belonged here.

The YAML uses anchors (&default_rubric, &default_options) so most
indicators share one written definition — but PyYAML resolves an alias to
the *same* object, not a copy, so scoring_rubric/options must be
deep-copied per indicator here. Skipping that would mean every indicator
using the default anchor shares one literal dict/list in memory: mutating
one indicator's rubric in code would silently mutate all of them.
"""

import copy
from functools import lru_cache
from pathlib import Path

import yaml

from app.engine.models import Adapter, Indicator


@lru_cache(maxsize=None)
def _load_raw(yaml_path: Path) -> dict:
    """Parsed exactly once per (process, path) -- every adapter's own
    content.py reads through this instead of each re-parsing its file from
    disk, and different adapters' paths get independent cache entries."""
    return yaml.safe_load(yaml_path.read_text(encoding="utf-8"))


def load_adapter_metadata(yaml_path: Path) -> Adapter:
    a = _load_raw(yaml_path)["adapter"]
    return Adapter(id=a["id"], name=a["name"], version=a["version"])


def load_indicators(yaml_path: Path) -> list[Indicator]:
    data = _load_raw(yaml_path)
    adapter_id = data["adapter"]["id"]
    indicators = []
    for item in data["indicators"]:
        indicators.append(
            Indicator(
                id=item["id"],
                adapter_id=adapter_id,
                external_code=item["external_code"],
                principle_group=item["principle_group"],
                title=item["title"],
                definition=item["definition"].strip(),
                plain_language_question=item["plain_language_question"].strip(),
                help_text=item["help_text"].strip(),
                example=item["example"].strip(),
                priority=item["priority"],
                display_order=item["display_order"],
                scoring_rubric=copy.deepcopy(item["scoring_rubric"]),
            )
        )
    return sorted(indicators, key=lambda i: i.display_order)


def load_options_by_indicator_id(yaml_path: Path) -> dict[str, list[dict]]:
    """Options aren't stored on the Indicator DB row (they're not scored
    data, just UI affordances) — loaded straight from YAML wherever a
    Question needs to be built."""
    data = _load_raw(yaml_path)
    return {item["id"]: copy.deepcopy(item["options"]) for item in data["indicators"]}
