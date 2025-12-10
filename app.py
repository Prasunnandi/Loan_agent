from flask import Flask, request, jsonify, send_file, render_template
import io
import os

from agents.master_agent import (
    handle_message,
    process_salary_slip,
    generate_sanction_letter
)

app = Flask(__name__)
# Optional: limit upload size to 2 MB
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024  # 2 MB

# Simple in-memory session store (OK for hackathon demo)
sessions = {}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}

    session_id = data.get("session_id")
    message = data.get("message", "")

    if not session_id:
        return jsonify({"error": "Missing session_id"}), 400

    # Get or create session
    session = sessions.setdefault(session_id, {})

    reply, updated_session = handle_message(message, session)
    sessions[session_id] = updated_session

    return jsonify({
        "reply": reply,
        "session_id": session_id,
        "state": updated_session.get("state")
    })


@app.route("/upload", methods=["POST"])
def upload():
    session_id = request.form.get("session_id")
    file = request.files.get("file")

    if not session_id or not file:
        return jsonify({"error": "Missing session_id or file"}), 400

    session = sessions.get(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    # Optional: make sure user followed the normal flow
    if session.get("state") not in ("WAIT_UPLOAD", "ASK_PAN", "ASK_SALARY"):
        return jsonify({
            "reply": (
                "Please complete the basic details (loan amount, salary & PAN) "
                "before uploading your salary slip."
            ),
            "session_id": session_id,
            "state": session.get("state"),
        })

    reply, updated_session = process_salary_slip(file, session)
    sessions[session_id] = updated_session

    return jsonify({
        "reply": reply,
        "session_id": session_id,
        "state": updated_session.get("state")
    })


@app.route("/sanction_letter/<session_id>", methods=["GET"])
def download_sanction_letter(session_id):
    session = sessions.get(session_id)

    if not session:
        return "Session not found", 404

    pdf_bytes = generate_sanction_letter(session)
    if not pdf_bytes:
        return "Sanction letter not available", 400

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name="sanction_letter.pdf"
    )


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "Digital Loan Officer"})


if __name__ == "__main__":
    # Render (and most PaaS) provide the port via environment variable
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
