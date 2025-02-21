import concurrent.futures
import io
import logging
import uuid

import cv2
import numpy as np
from PIL import Image
from flask import Flask
from flask import request, jsonify, send_file
from rembg import remove

from config import API_KEY, session

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")

# Thread pool for background processing
executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

# Dictionaries to store task statuses and results
task_status = {}  # {"task_id": "queued" | "processing" | "completed" | "failed"}
task_results = {}  # {"task_id": image_data}


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


@app.route("/")
def index():
    """
    Root endpoint providing a health check message.
    """
    logging.info("Health check triggered on '/' endpoint.")
    return jsonify({"message": "BackgroundRemoverAPI is up and running."}), 200


@app.route("/remove-bg", methods=["POST"])
def remove_background():
    """
    Synchronously remove the background from an uploaded image.
    """
    image_data, error_response, status_code = validate_request()
    if error_response:
        return error_response, status_code

    try:
        logging.info("Synchronously removing background from image.")
        output_data = remove(image_data, session=session)

        output_image = Image.open(io.BytesIO(output_data))
        img_io = io.BytesIO()
        output_image.save(img_io, format="PNG")
        img_io.seek(0)

        logging.info("Returning processed image (synchronous mode).")
        return send_file(img_io, mimetype="image/png", as_attachment=False, download_name="output.png")

    except Exception as e:
        logging.error(f"Error while processing image: {str(e)}")
        return jsonify({"error": "Failed to process the image."}), 500


@app.route("/remove-bg-async", methods=["POST"])
def remove_background_async():
    """
    Initiate an asynchronous background removal process for the uploaded image.
    """
    image_data, error_response, status_code = validate_request()
    if error_response:
        return error_response, status_code

    task_id = str(uuid.uuid4())
    task_status[task_id] = "queued"

    executor.submit(process_image, image_data, task_id)

    logging.info(f"Background task started (task_id={task_id}).")
    return jsonify({"task_id": task_id, "message": "Processing started, check status later."}), 202


def process_image(image_data, task_id):
    """
    Process the image to remove its background using rembg.
    Executed asynchronously.
    """
    try:
        logging.info(f"Processing image in background (task_id={task_id}).")
        task_status[task_id] = "processing"

        output_data = remove(image_data, session=session)

        output_image = Image.open(io.BytesIO(output_data))

        img_io = io.BytesIO()
        output_image.save(img_io, format="PNG")
        img_io.seek(0)

        task_results[task_id] = img_io
        task_status[task_id] = "completed"
        logging.info(f"Task {task_id} completed successfully.")

    except Exception as e:
        logging.error(f"Error while processing image (task_id={task_id}): {str(e)}")
        task_status[task_id] = "failed"


@app.route("/task-status/<task_id>", methods=["GET"])
def get_task_status(task_id):
    """
    Check the status of a background image processing task.
    """

    status = task_status.get(task_id)

    if status is None:
        logging.warning(f"Task ID {task_id} not found.")
        return jsonify({"error": "Invalid task ID."}), 404

    return jsonify({"task_id": task_id, "status": status}), 200


@app.route("/get-result/<task_id>", methods=["GET"])
def get_result(task_id):
    """
    Retrieve the processed image if the task is completed.
    """

    if task_status.get(task_id) != "completed":
        logging.warning(f"Task {task_id} is not yet completed or failed.")
        return jsonify({"error": "Task not completed or invalid task ID."}), 400

    result = task_results.pop(task_id, None)
    task_status.pop(task_id, None)

    if result is None:
        return jsonify({"error": "Image result not found."}), 500

    logging.info(f"Returning processed image for task {task_id}.")
    return send_file(result, mimetype="image/png", as_attachment=False, download_name="output.png")


@app.route("/remove-signature-bg", methods=["POST"])
def remove_signature_bg():
    """
    Removes the background from a signature image using Otsu's thresholding (OpenCV),
    returning a PNG with a transparent background. You can optionally resize the image.

    Form parameters (multipart/form-data):
      - image: Required, the uploaded signature image.
      - width (int): Optional, desired final width.
      - height (int): Optional, desired final height.
    """
    logging.info("Starting signature background removal (Otsu's threshold).")

    image_data, error_response, status_code = validate_request()
    if error_response:
        logging.warning("Request validation failed.")
        return error_response, status_code

    width = request.form.get("width", None)
    height = request.form.get("height", None)

    try:
        np_img = np.frombuffer(image_data, dtype=np.uint8)
        color_img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
        if color_img is None:
            logging.error("Invalid image data or unable to decode image.")
            return jsonify({"error": "Invalid image data."}), 400

        if width or height:
            orig_h, orig_w = color_img.shape[:2]
            if width and height:
                w = int(width)
                h = int(height)
                logging.info(f"Resizing image to {w}x{h}.")
            elif width:
                w = int(width)
                h = int(round(w * (orig_h / float(orig_w))))
                logging.info(f"Resizing image to {w}x{h} (width set, height auto).")
            else:
                h = int(height)
                w = int(round(h * (orig_w / float(orig_h))))
                logging.info(f"Resizing image to {w}x{h} (height set, width auto).")
            color_img = cv2.resize(color_img, (w, h), interpolation=cv2.INTER_LANCZOS4)

        gray = cv2.cvtColor(color_img, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)

        _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)

        b, g, r = cv2.split(color_img)
        rgba = cv2.merge([b, g, r, mask])
        rgba = cv2.cvtColor(rgba, cv2.COLOR_BGRA2RGBA)

        pil_img = Image.fromarray(rgba)
        buf = io.BytesIO()
        pil_img.save(buf, format="PNG")
        buf.seek(0)

        logging.info("Signature background removed successfully (Otsu), returning PNG.")
        return send_file(buf, mimetype="image/png", download_name="signature_transparent.png")

    except Exception as e:
        logging.error(f"Error removing signature background: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    from waitress import serve

    serve(app, host="0.0.0.0", port=8080)
