import os, io, uuid, datetime, requests
from pathlib import Path
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS

try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

UPLOAD_FOLDER = Path("uploads")
UPLOAD_FOLDER.mkdir(exist_ok=True)
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
POKEMONTCG_API_KEY = os.environ.get("POKEMONTCG_API_KEY", "")

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
CORS(app)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def save_upload(file_storage):
    ext = file_storage.filename.rsplit(".", 1)[-1].lower() if "." in file_storage.filename else "jpg"
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_name = f"card_{timestamp}_{uuid.uuid4().hex[:6]}.{ext}"
    dest = UPLOAD_FOLDER / unique_name
    file_storage.save(dest)
    return dest

@app.route("/")
def index():
    return jsonify({
        "status": "running",
        "message": "PokéScan backend is live"
    })

@app.route("/upload", methods=["POST"])
def upload():
    if "card_image" not in request.files:
        return jsonify({"ok": False, "error": "No image received."}), 400
    file = request.files["card_image"]
    if not file.filename or not allowed_file(file.filename):
        return jsonify({"ok": False, "error": "Invalid file type."}), 415
    saved_path = save_upload(file)
    size_bytes = saved_path.stat().st_size
    image_info = {"size_bytes": size_bytes}
    if PILLOW_AVAILABLE:
        with Image.open(saved_path) as img:
            image_info.update({"width": img.width, "height": img.height, "format": img.format})
    return jsonify({
        "ok": True,
        "filename": saved_path.name,
        "image_info": image_info,
        "result": f"Image saved successfully ({image_info.get('width','?')}×{image_info.get('height','?')}px). Ready for identification.",
    })

@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route("/health")
def health():
    return jsonify({"status": "ok", "pillow": PILLOW_AVAILABLE})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))