import os

from flask import Flask, jsonify, request

from automation import ExtensionError, run_extension

app = Flask(__name__)


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/pythonanywhere/run-until-one-month")
def pythonanywhere_run_until_one_month():
    """Log in to PythonAnywhere and click 'Run until 1 month from today' for the web app."""
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or request.form.get("username") or "").strip()
    password = payload.get("password") or request.form.get("password") or ""

    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400

    try:
        result = run_extension(username, password)
        return jsonify(result), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except ExtensionError as exc:
        return jsonify({"error": str(exc)}), 422
    except Exception as exc:
        return jsonify({"error": "unexpected error", "detail": str(exc)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
