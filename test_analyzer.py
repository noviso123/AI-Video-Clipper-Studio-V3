from src.modules.narrator import VoiceAnalyzer
import os

analyzer = VoiceAnalyzer()
samples_dir = os.path.join(os.getcwd(), 'models', 'custom_voice_pro')

print(f"Analyzing: {samples_dir}")
if os.path.exists(samples_dir):
    print(f"Files: {os.listdir(samples_dir)}")
    profile = analyzer.analyze_samples(samples_dir)
    print(f"Result: {profile}")
else:
    print("Directory not found")
