# BackgroundRemoverAPI

A simple Flask-based API that removes the background from an uploaded image.  
It uses the [rembg](https://github.com/danielgatis/rembg) library for background removal, and it provides API key-based
authentication.

---

## Table of Contents

1. [Features](#features)
2. [Installation](#installation)
3. [Usage](#usage)
4. [Environment Variables](#environment-variables)
5. [Endpoints](#endpoints)
6. [Security](#security)
7. [Contributing](#contributing)
8. [License](#license)

---

## Features

- **Background removal** using the `rembg` library.
- **API key authentication** to secure the endpoints.
- **Supports both synchronous and asynchronous processing** for improved performance.
- **Task-based processing** with status tracking.
- **Easy deployment** on DigitalOcean or any cloud provider.
- Includes a script to **generate new API keys**.

---

## Installation

1. Clone the repository:

   ```bash
   git clone https://your-repo-url background_remover_api
   ```

2. Change directory:

   ```bash
   cd background_remover_api
   ```

3. Create and activate a virtual environment (optional but recommended):

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\\Scripts\\activate`
   ```

4. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

1. **Generate an API key** (optional, if you want to change the default key):

   ```bash
   python generate_api_key.py
   ```

    - Copy the generated key, and either set it as an environment variable (`API_KEY`) or place it in `config.py`.

2. **Run the server**:

   ```bash
   python app.py
   ```

3. The API will be running at `http://localhost:8080` by default.

---

## Environment Variables

To avoid storing sensitive keys in the code, you can set the `API_KEY` environment variable on your system or directly
in the DigitalOcean droplet settings. For example:

```bash
export API_KEY="YOUR_SECURE_KEY_HERE"
```

Or in DigitalOcean App Platform, set the environment variable in the project's "Settings" -> "Environment Variables".

---

## Endpoints

### 1. **Health Check**

**URL**: `GET /`  
**Response**:

```json
{
  "message": "BackgroundRemoverAPI is up and running."
}
```

### 2. **Remove Background (Synchronous Processing)**

**URL**: `POST /remove-bg`  
**Headers**:

- `X-API-KEY: YOUR_API_KEY_HERE`

**Body** (`multipart/form-data`):

- `image`: The image file (jpg, png, etc.) to be processed.

**Response**: Returns a PNG image with the background removed.

**Example using `curl`**:

```bash
curl -X POST \
  -H "X-API-KEY: YOUR_API_KEY_HERE" \
  -F "image=@/path/to/image.jpg" \
  http://localhost:8080/remove-bg --output output.png
```

### 3. **Remove Background (Asynchronous Processing)**

**URL**: `POST /remove-bg-async`  
**Headers**:

- `X-API-KEY: YOUR_API_KEY_HERE`

**Body** (`multipart/form-data`):

- `image`: The image file (jpg, png, etc.) to be processed.

**Response**:

```json
{
  "task_id": "your-task-id",
  "message": "Processing started, check status later."
}
```

**Example using `curl`**:

```bash
curl -X POST \
  -H "X-API-KEY: YOUR_API_KEY_HERE" \
  -F "image=@/path/to/image.jpg" \
  http://localhost:8080/remove-bg-async
```

### 4. **Check Task Status**

**URL**: `GET /task-status/<task_id>`  
**Response**:

```json
{
  "task_id": "your-task-id",
  "status": "queued | processing | completed | failed"
}
```

### 5. **Retrieve Processed Image**

**URL**: `GET /get-result/<task_id>`  
**Response**: Returns a PNG image if processing is completed.

**Example using `curl`**:

```bash
curl -X GET http://localhost:8080/get-result/your-task-id --output output.png
```

---

## Security

- This project uses a simple API Key mechanism.
- For production, ensure that HTTPS is used so the API key is sent securely.
- Avoid exposing the API key in client-side applications.

---

## Contributing

Feel free to open issues or merge requests. Any feedback is welcome.

---

## License

This project is provided under the [MIT License](https://opensource.org/licenses/MIT).
