"""Loads adapters/fair/indicators.yaml into the database. Idempotent: safe
to re-run after editing indicators.yaml — upserts by primary key rather
than failing on a duplicate.

Usage: python scripts/seed_indicators.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session

from app.adapters.fair import content as fair_content
from app.adapters.harmonization import content as harmonization_content
from app.db import engine, init_db

# Every adapter's content module, looped over below. Kept in sync with
# app/adapters/registry.py -- both are "the one place allowed to know every
# concrete adapter exists," per registry.py's own docstring.
_CONTENT_MODULES = [fair_content, harmonization_content]


def seed() -> None:
    init_db()

    with Session(engine) as session:
        for content_module in _CONTENT_MODULES:
            adapter = content_module.load_adapter_metadata()
            indicators = content_module.load_indicators()
            adapter_id = adapter.id  # captured now — reading adapter.id after
            indicator_count = len(indicators)  # the session closes below would
            # raise DetachedInstanceError once SQLAlchemy expires the instance.

            existing_adapter = session.get(type(adapter), adapter.id)
            if existing_adapter is None:
                session.add(adapter)
            else:
                existing_adapter.name = adapter.name
                existing_adapter.version = adapter.version

            for indicator in indicators:
                existing = session.get(type(indicator), indicator.id)
                if existing is None:
                    session.add(indicator)
                else:
                    for field in (
                        "adapter_id",
                        "external_code",
                        "principle_group",
                        "title",
                        "definition",
                        "plain_language_question",
                        "help_text",
                        "example",
                        "priority",
                        "display_order",
                        "scoring_rubric",
                    ):
                        setattr(existing, field, getattr(indicator, field))

            session.commit()
            print(f"Seeded adapter {adapter_id!r} with {indicator_count} indicators.")


if __name__ == "__main__":
    seed()
