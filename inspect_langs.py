import inspect
try:
    from kokoro_onnx.tokenizer import Tokenizer
    print("Language mapping in Tokenizer:")
    # Some libraries have a LANGUAGES dict or list
    for name, obj in inspect.getmembers(Tokenizer):
        if not name.startswith('_'):
            print(f"- {name}")

    # Try to initialize and see what codes it accepts
    # This is a bit of a guess, but searching for 'supported' or 'langs'
except ImportError:
    print("Could not import Tokenizer")
