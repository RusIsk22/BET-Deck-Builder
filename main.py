"""
BET Deck Builder — FastAPI Build Service

POST /build with outline JSON → returns .pptx file
Deploy on Railway. Connect from Dify via HTTP Request node.
"""

import io
import json
import os
import tempfile

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import StreamingResponse
from typing import Optional

from build_deck import build

app = FastAPI(title="BET Deck Builder", version="1.0.0")

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "Master_Ergebnis.pptx")
BUILD_SECRET = os.environ.get("BUILD_SECRET", "")


def verify_secret(authorization: Optional[str]):
    """Simple bearer token auth."""
    if not BUILD_SECRET:
        return  # No secret configured = no auth (dev mode)
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    token = authorization.replace("Bearer ", "").strip()
    if token != BUILD_SECRET:
        raise HTTPException(status_code=403, detail="Invalid token")


@app.get("/health")
async def health():
    return {"status": "ok", "template_exists": os.path.exists(TEMPLATE_PATH)}


@app.post("/build")
async def build_deck(
    request: Request,
    authorization: Optional[str] = Header(None),
):
    """
    Accepts outline JSON, builds .pptx, returns as download.
    
    Expects JSON body with structure:
    {
        "title": "...",
        "subtitle": "...",
        "footer": "...",
        "slides": [...]
    }
    
    Or wrapped in {"outline": "..."} or {"outline": {...}}
    (for Dify compatibility).
    """
    verify_secret(authorization)

    # Parse body
    body = await request.body()
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Handle Dify wrapping: {"outline": "..."} or {"outline": {...}}
    if "outline" in data:
        outline = data["outline"]
        if isinstance(outline, str):
            try:
                outline = json.loads(outline)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400, detail="Could not parse 'outline' string as JSON"
                )
        data = outline

    # Validate
    if "title" not in data:
        raise HTTPException(status_code=400, detail="Missing 'title' in outline")
    if "slides" not in data or not data["slides"]:
        raise HTTPException(status_code=400, detail="Missing or empty 'slides' in outline")
    if len(data["slides"]) > 30:
        raise HTTPException(status_code=400, detail="Max 30 slides allowed")

    # Validate kacheln on layout 6
    for i, s in enumerate(data["slides"]):
        if s.get("layout") == 6:
            kacheln = s.get("kacheln", [])
            if len(kacheln) != 4:
                raise HTTPException(
                    status_code=400,
                    detail=f"Slide {i+1}: Layout 6 requires exactly 4 Kacheln, got {len(kacheln)}",
                )

    # Build the .pptx
    try:
        with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as tmp:
            tmp_path = tmp.name

        build(TEMPLATE_PATH, data, tmp_path)

        with open(tmp_path, "rb") as f:
            pptx_bytes = f.read()

        os.unlink(tmp_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Build failed: {str(e)}")

    # Generate filename
    safe_title = "".join(
        c if c.isalnum() or c in " -_" else "" for c in data["title"]
    )[:50].strip().replace(" ", "_")
    filename = f"{safe_title or 'deck'}.pptx"

    return StreamingResponse(
        io.BytesIO(pptx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
