"""Dump the FastAPI OpenAPI schema to backend/openapi.json.

Used to (re)generate the frontend TypeScript types without a running server:
    python export_openapi.py
    (then, in frontend/) pnpm gen:api
"""
import json
import os

from api import app


def main() -> None:
    out = os.path.join(os.path.dirname(__file__), "openapi.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(app.openapi(), f, indent=2, ensure_ascii=False)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
