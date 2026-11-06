"""CLI entry: reads PYTHONANYWHERE_USERNAME and PYTHONANYWHERE_PASSWORD from the environment."""

import os

from automation import ExtensionError, run_extension


def main():
    username = os.environ.get("PYTHONANYWHERE_USERNAME", "").strip()
    password = os.environ.get("PYTHONANYWHERE_PASSWORD", "")

    if not username or not password:
        raise ValueError(
            "Set PYTHONANYWHERE_USERNAME and PYTHONANYWHERE_PASSWORD environment variables."
        )

    try:
        result = run_extension(username, password)
        print(result["message"])
        print("Current URL:", result["final_url"])
    except ExtensionError as exc:
        print("Failed:", exc)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
