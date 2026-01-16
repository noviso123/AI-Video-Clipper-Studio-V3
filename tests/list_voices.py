import pyttsx3

try:
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    print(f"Found {len(voices)} voices:")
    for v in voices:
        print(f"ID: {v.id}")
        print(f"Name: {v.name}")
        print(f"Gender: {v.gender}")
        print("-" * 20)
except Exception as e:
    print(f"Error: {e}")
