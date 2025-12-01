import logging
import os
import time
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory, g

APP_ROOT = Path(__file__).resolve().parent
FLAG = os.environ.get("FLAG", "CSBC{3L3V3N_51GN4L_574710N_D3M0}")
FAIL_LIMIT = 5
FAIL_WINDOW = 60
LOCK_DURATION = 30

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

app = Flask(__name__, static_folder=str(APP_ROOT))

attempt_tracker = {}


def now() -> float:
    return time.time()


def client_ip() -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


def extract_last(multi_dict, key: str) -> str:
    values = multi_dict.getlist(key)
    return values[-1].strip() if values else ""


def prune_attempts(state: dict, current: float) -> None:
    state["fails"] = [ts for ts in state["fails"] if current - ts <= FAIL_WINDOW]


def log_attempt(ip: str, raw_body: str, parsed: dict) -> None:
    logging.info(
        "api_send attempt ip=%s body=%s parsed=%s",
        ip,
        raw_body.replace("\n", "\\n"),
        parsed,
    )


@app.before_request
def detect_operator():
    g.is_operator = False
    source = request.form if request.method == "POST" else request.args
    user_value = extract_last(source, "user")
    if user_value == "operator":
        g.is_operator = True


@app.route("/", methods=["GET"])
def index():
    return send_from_directory(APP_ROOT, "index.html")


@app.route("/client.js", methods=["GET"])
def client_asset():
    return send_from_directory(APP_ROOT, "client.js")


@app.route("/api/send", methods=["POST"])
def api_send():
    ip = client_ip()
    state = attempt_tracker.setdefault(ip, {"fails": [], "lock_until": 0.0})
    current = now()
    if current < state["lock_until"]:
        retry = int(state["lock_until"] - current)
        return (
            jsonify(
                {
                    "status": "locked",
                    "message": "Relay cooling down. Try later.",
                    "retry_after": max(retry, 1),
                }
            ),
            429,
        )

    raw_body = request.get_data(as_text=True)
    user = extract_last(request.form, "user")
    message = extract_last(request.form, "message")
    log_attempt(
        ip,
        raw_body,
        {"user": user, "message": message},
    )

    if user == "operator":
        state["fails"].clear()
        state["lock_until"] = 0.0
        return jsonify({"status": "ok", "privileged": True})

    prune_attempts(state, current)
    state["fails"].append(current)
    if len(state["fails"]) >= FAIL_LIMIT:
        state["lock_until"] = current + LOCK_DURATION
        return (
            jsonify(
                {
                    "status": "locked",
                    "message": "Too many noisy attempts. Station locked.",
                    "retry_after": LOCK_DURATION,
                }
            ),
            429,
        )

    return jsonify({"status": "ok", "privileged": False})


@app.route("/visions/eleven-only", methods=["GET"])
def visions():
    if not g.get("is_operator"):
        return jsonify({"error": "Access denied. Signal not elevated."}), 403
    return jsonify({"vision": FLAG})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

