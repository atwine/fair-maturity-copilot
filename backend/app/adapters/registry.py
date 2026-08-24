"""The one place allowed to know every concrete adapter exists. The API
layer (app/api/*) depends only on this registry and the Adapter Protocol —
never imports app.adapters.fair directly — so adding the future OMOP
adapter means one new entry here, not changes scattered through the API.
"""

from app.adapters.fair.adapter import FairAdapter
from app.engine.ports import Adapter

_ADAPTERS: dict[str, Adapter] = {
    "fair-v0": FairAdapter(),
}


def get_adapter(adapter_id: str) -> Adapter:
    adapter = _ADAPTERS.get(adapter_id)
    if adapter is None:
        raise KeyError(f"Unknown adapter_id: {adapter_id!r}")
    return adapter


def list_adapter_ids() -> list[str]:
    return list(_ADAPTERS.keys())
