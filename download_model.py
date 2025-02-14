from rembg import new_session

from config import model_name


def preload_model():
    """
    Preloads the background removal model and caches it for future use.
    This function ensures that the model is downloaded and ready before being used.
    """
    new_session(model_name)


if __name__ == "__main__":
    preload_model()
    print("Model downloaded and cached!")
