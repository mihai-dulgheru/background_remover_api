from rembg import new_session


def preload_model():
    new_session("u2net")


if __name__ == "__main__":
    preload_model()
    print("Model downloaded and cached!")
