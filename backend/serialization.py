"""JSON serialization that tolerates NaN/Inf (renders them as null)."""
import json
import math

from fastapi.responses import JSONResponse


def json_safe(obj):
    """Recursively replace NaN/Inf floats with None so the payload is valid JSON."""
    if isinstance(obj, float):
        return obj if math.isfinite(obj) else None
    if isinstance(obj, dict):
        return {k: json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [json_safe(v) for v in obj]
    return obj


class SafeJSONResponse(JSONResponse):
    """JSONResponse that renders NaN/Inf as null instead of raising."""

    def render(self, content) -> bytes:
        return json.dumps(
            json_safe(content),
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8")
