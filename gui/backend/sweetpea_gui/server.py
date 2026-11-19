"""HTTP API for the GUI front end, which also serves the built front end."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .codegen import generate
from .examples import list_examples
from .parse import Unsupported, parse_program
from .run import DesignError, check, synthesize

app = FastAPI(title="SweetPea GUI")


@app.post("/api/render")
def render(model: dict) -> dict:
    return {"code": generate(model), "check": check(model)}


@app.post("/api/parse")
def parse(body: dict) -> dict:
    try:
        model = parse_program(body["code"])
    except Unsupported as e:
        return {"error": str(e), "line": e.line}
    return {"model": model, "check": check(model)}


@app.get("/api/examples")
def examples() -> list:
    return list_examples()


@app.post("/api/synthesize")
def sample(model: dict):
    try:
        return synthesize(model)
    except DesignError as e:
        return JSONResponse({"error": str(e)}, status_code=400)


DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if DIST.is_dir():
    app.mount("/", StaticFiles(directory=DIST, html=True), name="frontend")
