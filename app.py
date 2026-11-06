import logging
import os
import uuid

from logging_config import configure_logging

configure_logging()

from flask import Flask, jsonify, request

from automation import ExtensionError, run_extension

logger = logging.getLogger("api")

app = Flask(__name__)


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/pythonanywhere/run-until-one-month")
def pythonanywhere_run_until_one_month():
    """Log in to PythonAnywhere and click 'Run until 1 month from today' for the web app."""
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or request.form.get("username") or "").strip()
    password = payload.get("password") or request.form.get("password") or ""

    if not username or not password:
        logger.warning("request_id=%s rejected: missing username or password", request_id)
        return jsonify({"error": "username and password are required"}), 400

    logger.info(
        "request_id=%s POST /pythonanywhere/run-until-one-month username=%s",
        request_id,
        username,
    )

    try:
        result = run_extension(username, password, request_id=request_id)
        logger.info("request_id=%s completed successfully username=%s", request_id, username)
        return jsonify({**result, "request_id": request_id}), 200
    except ValueError as exc:
        logger.warning("request_id=%s validation error: %s", request_id, exc)
        return jsonify({"error": str(exc), "request_id": request_id}), 400
    except ExtensionError as exc:
        logger.warning("request_id=%s extension failed: %s", request_id, exc)
        return jsonify({"error": str(exc), "request_id": request_id}), 422
    except Exception as exc:
        logger.exception("request_id=%s unexpected error", request_id)
        return jsonify(
            {"error": "unexpected error", "detail": str(exc), "request_id": request_id}
        ), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
