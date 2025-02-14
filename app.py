import concurrent.futures
import io
import logging
import uuid

from PIL import Image
from flask import Flask, request, send_file, jsonify
from rembg import remove

from config import API_KEY, session

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")

# Thread pool for background processing
executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

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
    return jsonify({"message": "BackgroundRemoverAPI is up and running."})


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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
