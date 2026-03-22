def get_interpreter(model_path):

    try:
        # -------- Raspberry Pi / lightweight --------
        from tflite_runtime.interpreter import Interpreter #type: ignore
        print("[INFO] Using tflite-runtime")

    except ImportError:
        # -------- PC fallback --------
        from tensorflow.lite.python.interpreter import Interpreter #type: ignore
        print("[INFO] Using TensorFlow Lite")

    return Interpreter(model_path=model_path)