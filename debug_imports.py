
import sys
import os

print("Checking imports...")
try:
    import flask
    print("Flask ok")
    import flask_cors
    print("CORS ok")
    import moviepy.editor
    print("Moviepy ok")
    import proglog
    print("Proglog ok")
    from src.core.config import Config
    print("Config ok")
    from src.modules.analyzer import ViralAnalyzer
    print("Analyzer ok")
    from src.modules.editor import VideoEditor
    print("Editor ok")
    print("ALL IMPORTS OK")
except Exception as e:
    print(f"IMPORT ERROR: {e}")
    import traceback
    traceback.print_exc()
