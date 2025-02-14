import os

from rembg import new_session

# Retrieve the API key from environment variables, or use a default one if not set.
# It's recommended to set the API_KEY in the environment for security reasons.
API_KEY = os.environ.get("API_KEY", "<YOUR_API_KEY_HERE>")

# Define the model used for background removal.
# You can change "u2net" to "isnet-general-use" for better quality results.
model_name = "u2net_lite"

# Create a new session for the selected model.
# This session will be used to process images throughout the application.
session = new_session(model_name)
