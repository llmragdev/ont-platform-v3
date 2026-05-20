import os
import google.generativeai as genai
from dotenv import load_dotenv

def list_models():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set.")

    # This handles the authentication globally for the library
    genai.configure(api_key=api_key)

    print("Available models:")
    for model in genai.list_models():
        print(f"- Name: {model.name}")
        print(f"  Description: {model.description}")
        print(f"  Methods: {model.supported_generation_methods}\n")

if __name__ == "__main__":
    list_models()