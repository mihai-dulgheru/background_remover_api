"""
This module holds the API_KEY configuration for authentication.
It attempts to read the API_KEY from an environment variable,
otherwise it will default to the string below.
"""

import os

# Read the API key from an environment variable if available
API_KEY = os.environ.get("API_KEY", "YOUR_API_KEY_HERE")
