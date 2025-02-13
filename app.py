"""
This module contains the main Flask application
that provides a route to remove the background from an uploaded image.
It uses an API key for authentication.
"""

import io
import logging

from PIL import Image
from flask import Flask, request, send_file, jsonify
from rembg import remove
from waitress import serve

from config import API_KEY

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")


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
    Remove background from the uploaded image and return the result.
    Expects a form-data file with key 'image' and an 'X-API-KEY' in the header.
    """

    # Step 1: Check if 'X-API-KEY' header is present
    header_api_key = request.headers.get("X-API-KEY")
    if not header_api_key:
        logging.warning("No API key provided.")
        return jsonify({"error": "No API key provided."}), 401

    # Step 2: Validate the provided API key
    if header_api_key != API_KEY:
        logging.warning("Invalid API key provided.")
        return jsonify({"error": "Invalid API key."}), 403

    # Step 3: Check if an image has been provided in the request
    if "image" not in request.files:
        logging.warning("No image file found in the request.")
        return jsonify({"error": "No image file found in the request."}), 400

    # Step 4: Read the image from the request
    file = request.files["image"]
    image_data = file.read()

    # Step 5: Use rembg to remove the background
    try:
        logging.info("Removing background from the uploaded image.")
        output_data = remove(image_data)
    except Exception as e:
        logging.error(f"Error while removing background: {str(e)}")
        return jsonify({"error": "Failed to process the image."}), 500

    # Step 6: Return the image with removed background
    # We return a PNG by default
    try:
        output_image = Image.open(io.BytesIO(output_data))
        img_io = io.BytesIO()
        output_image.save(img_io, format="PNG")
        img_io.seek(0)
        logging.info("Returning image with background removed.")
        return send_file(img_io, mimetype="image/png", as_attachment=False, download_name="output.png")
    except Exception as e:
        logging.error(f"Error while returning processed image: {str(e)}")
        return jsonify({"error": "Failed to return the processed image."}), 500


if __name__ == "__main__":
    # Run the Flask app using Waitress
    serve(app, host="0.0.0.0", port=8080)
