"""Thin wrapper over app.engine.content_loader, pointed at this adapter's
own indicators.yaml. See app/adapters/fair/content.py for the identical
pattern -- the loading logic itself is generic and lives in the engine.
"""

from functools import partial
from pathlib import Path

from app.engine import content_loader as _cl

_YAML_PATH = Path(__file__).parent / "indicators.yaml"

load_adapter_metadata = partial(_cl.load_adapter_metadata, _YAML_PATH)
load_indicators = partial(_cl.load_indicators, _YAML_PATH)
load_options_by_indicator_id = partial(_cl.load_options_by_indicator_id, _YAML_PATH)
