import google.generativeai as genai
# Replace with your actual key
genai.configure(api_key="AIzaSyC8mkCXVl7ooKvARAbg4JfsRoy0oVbU2Uo")

for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"Supported Model: {m.name}")