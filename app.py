import io
import logging

import cv2
import numpy as np
from PIL import Image
from flask import Flask, request, jsonify, send_file

from config import API_KEY

app = Flask(__name__)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")


def validate_request():
    """
    Validate the API key and check for an uploaded image.
    Returns (image_data, None, None) if successful,
    otherwise (None, response, status_code).
    """
    header_api_key = request.headers.get("X-API-KEY")
    if not header_api_key or header_api_key != API_KEY:
        logging.warning("Invalid or missing API key.")
        return None, jsonify({"error": "Invalid or missing API key."}), 403

    if "image" not in request.files:
        logging.warning("No image file found in the request.")
        return None, jsonify({"error": "No image file found in the request."}), 400

    file = request.files["image"]
    return file.read(), None, None


@app.route("/")  # Deprecated
@app.route("/health-check")
def index():
    """
    Root endpoint providing a health check message.
    """
    logging.info("Health check triggered on '/' endpoint.")
    return jsonify({"message": "BackgroundRemoverAPI is up and running."}), 200


@app.route("/remove-signature-bg", methods=["POST"])  # Deprecated
@app.route("/clean-signature", methods=["POST"])
def remove_signature_bg():
    """
    Removes the background from a signature image using Otsu's thresholding (OpenCV),
    returning a PNG with a transparent background. Optionally resizes the image.

    Form parameters (multipart/form-data):
      - image: Required, the uploaded signature image.
      - width (int): Optional, desired final width.
      - height (int): Optional, desired final height.
    """
    logging.info("Starting signature background removal using Otsu's threshold.")

    image_data, error_response, status_code = validate_request()
    if error_response:
        logging.warning("Request validation failed.")
        return error_response, status_code

    width_param = request.form.get("width", None)
    height_param = request.form.get("height", None)

    try:
        np_img = np.frombuffer(image_data, dtype=np.uint8)
        color_img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
        if color_img is None:
            logging.error("Invalid image data or unable to decode image.")
            return jsonify({"error": "Invalid image data."}), 400

        orig_h, orig_w = color_img.shape[:2]
        logging.info(f"Original dimensions: {orig_w}x{orig_h}")

        gray = cv2.cvtColor(color_img, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)

        b, g, r = cv2.split(color_img)
        rgba = cv2.merge([b, g, r, mask])
        rgba = cv2.cvtColor(rgba, cv2.COLOR_BGRA2RGBA)

        pil_img = Image.fromarray(rgba)

        if width_param or height_param:
            if width_param and height_param:
                final_w = int(width_param)
                final_h = int(height_param)
                logging.info(f"Resizing final image to {final_w}x{final_h}.")
            elif width_param:
                final_w = int(width_param)
                final_h = int(round(final_w * (orig_h / float(orig_w))))
                logging.info(f"Resizing final image to {final_w}x{final_h} (width set, height auto-calculated).")
            else:
                final_h = int(height_param)
                final_w = int(round(final_h * (orig_w / float(orig_h))))
                logging.info(f"Resizing final image to {final_w}x{final_h} (height set, width auto-calculated).")
            pil_img = pil_img.resize((final_w, final_h), resample=Image.Resampling.LANCZOS)
        else:
            logging.info("No resize parameters provided; resizing final image to original dimensions.")
            pil_img = pil_img.resize((orig_w, orig_h), resample=Image.Resampling.LANCZOS)

        pil_img = pil_img.convert("RGBA")
        pil_img = pil_img.quantize(method=Image.Quantize.FASTOCTREE)

        buf = io.BytesIO()
        pil_img.save(buf, format="PNG", optimize=True, compress_level=9)
        buf.seek(0)

        logging.info("Signature background removed successfully; returning optimized PNG.")
        return send_file(buf, mimetype="image/png", download_name="signature_transparent.png")

    except Exception as e:
        logging.error(f"Error removing signature background: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    from waitress import serve

    serve(app, host="0.0.0.0", port=8080)
