"""
Local-only Echo Web API.

This backend exposes Echo chat capabilities for a future local web frontend.
The future frontend should call /chat for general Echo questions. LLM live
mode remains controlled entirely by environment variables such as
ECHO_LLM_PROVIDER, ECHO_LLM_LIVE, OPENAI_API_KEY, and ECHO_OPENAI_MODEL.
"""

import os

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

try:
    from fastapi import FastAPI, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
except ImportError as import_error:
    FastAPI = None
    Request = None
    CORSMiddleware = None
    JSONResponse = None
    FASTAPI_IMPORT_ERROR = import_error
else:
    FASTAPI_IMPORT_ERROR = None

from echo import (
    echo_ask_agent,
    echo_generate_llm_answer,
    get_echo_orchestrator_status,
    get_echo_tool_registry,
    get_llm_provider_status
)


LOCALHOST_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000"
]


def _load_local_env():

    if load_dotenv is not None:
        load_dotenv()


def _error_response(message, status_code=400, code="BAD_REQUEST"):

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ERROR",
            "error": code,
            "message": message
        }
    )


async def _json_body(request):

    try:
        body = await request.json()
    except Exception:
        return None

    if not isinstance(body, dict):
        return None

    return body


def _message_from_body(body):

    message = " ".join(str((body or {}).get("message") or "").split())
    return message


def create_app():

    if FastAPI is None:
        raise RuntimeError(
            "FastAPI dependency missing. Run: pip install fastapi uvicorn"
        ) from FASTAPI_IMPORT_ERROR

    _load_local_env()

    app = FastAPI(
        title="Echo Local API",
        version="1.0",
        description="Local-only API for Echo deterministic and LLM-gated chat."
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=LOCALHOST_ORIGINS,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"]
    )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request, exc):
        return _error_response(
            "Echo API request failed without exposing internal details.",
            status_code=500,
            code="INTERNAL_ERROR"
        )

    @app.get("/health")
    async def health():
        return {
            "status": "ok",
            "system": "Echo",
            "mode": "local_api",
            "llm_status": get_llm_provider_status()
        }

    @app.post("/chat")
    async def chat(request: Request):
        body = await _json_body(request)

        if body is None:
            return _error_response(
                "Request body must be a JSON object with a non-empty message."
            )

        message = _message_from_body(body)

        if not message:
            return _error_response("Message is required.")

        return echo_generate_llm_answer(message)

    @app.post("/ask")
    async def ask(request: Request):
        return await chat(request)

    @app.post("/agent/ask")
    async def agent_ask(request: Request):
        body = await _json_body(request)

        if body is None:
            return _error_response(
                "Request body must be a JSON object with agent and message."
            )

        agent = " ".join(str(body.get("agent") or "").split())
        message = _message_from_body(body)

        if not agent:
            return _error_response("Agent is required.")

        if not message:
            return _error_response("Message is required.")

        return echo_ask_agent(agent, message)

    @app.get("/tools")
    async def tools():
        return get_echo_tool_registry()

    @app.get("/status")
    async def status():
        return {
            "orchestrator_status": get_echo_orchestrator_status(),
            "llm_provider_status": get_llm_provider_status(),
            "tools": get_echo_tool_registry()
        }

    return app


if FastAPI is not None:
    app = create_app()
else:
    app = None


def main():

    if FastAPI is None:
        raise SystemExit(
            "FastAPI dependency missing. Run: pip install fastapi uvicorn"
        )

    try:
        import uvicorn
    except ImportError as import_error:
        raise SystemExit(
            "uvicorn dependency missing. Run: pip install uvicorn"
        ) from import_error

    host = os.getenv("ECHO_API_HOST") or "127.0.0.1"
    port_text = os.getenv("ECHO_API_PORT") or "8000"

    try:
        port = int(port_text)
    except ValueError:
        raise SystemExit("ECHO_API_PORT must be an integer.")

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
