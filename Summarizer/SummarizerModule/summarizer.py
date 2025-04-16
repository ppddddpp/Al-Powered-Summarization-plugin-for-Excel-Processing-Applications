from flask import Flask, request, jsonify
from flask_cors import CORS
from google import genai
import logging
import json
import os

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from the add-ins

current_dir = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE_PATH = os.path.join(current_dir, "config.json")

def load_config_data(config_file=CONFIG_FILE_PATH):
    result = {
        "gemini_credentials": [],
    }

    if not os.path.exists(config_file):
        logging.info("No existing config file found.")
        return result

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config_data = json.load(f)

        gemini_credentials_list = []
        for credential_set in config_data.get("credentials", []):
            gemini_credentials = credential_set.get("gemini_credentials", [])
            if isinstance(gemini_credentials, list):
                gemini_credentials_list.extend(gemini_credentials)

        valid_gemini_credentials = [cred for cred in gemini_credentials_list if "api_key" in cred]
        if valid_gemini_credentials:
            result["gemini_credentials"] = valid_gemini_credentials
        else:
            logging.error("No valid gemini credentials found.")

    except (json.JSONDecodeError, FileNotFoundError) as e:
        logging.error(f"Error reading config file: {e}")

    return result

config_data = load_config_data(CONFIG_FILE_PATH)
GEMINI_API_CREDENTIALS = config_data["gemini_credentials"]

@app.route("/summarize", methods=["POST"])
def summarize():
    """
    Handle a POST request from the add-in with a JSON object containing the text to summarize,
    the custom format/prompt, and other parameters.

    The JSON object should have the following structure:

    {
        "text": string,        # The text to summarize
        "format": string,      # The summarization prompt/instructions
        "temperature": float,  # The temperature setting for creativity (default e.g. 0.7)
        "topP": float,         # (Optional) Output diversity parameter
        "topK": int,           # (Optional) Response focus parameter
        "model": string (optional)  # (Optional) Model to be used
    }

    Returns a JSON object with a key "summarized_text" containing the result,
    or an error object with a key "error" if something went wrong.
    """
    data = request.json
    source_text = data.get("text", "")
    format_prompt = data.get("format", "")
    temperature = float(data.get("temperature", 0.7))
    top_p = float(data.get("topP", 0.95))
    top_k = int(data.get("topK", 32))
    model = data.get("model", "gemini-2.0-flash")

    if not source_text:
        return jsonify({"error": "No text provided"}), 400

    if not format_prompt:
        return jsonify({"error": "Summarization format is required"}), 400

    command = (
        "Summarize the following text according to the specified format.\n"
        "Format instructions: " + format_prompt + "\n"
        "Apply a creativity level of " + str(temperature) + " and ensure concise output.\n"
    )
    prompt = command + source_text

    summarized_text = None
    for credentials in GEMINI_API_CREDENTIALS:
        api_key = credentials["api_key"]
        try:
            print("Using API key:", api_key)
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=model, contents=prompt
            )

            summarized_text = response.text
            print(summarized_text)
            logging.info(f"Summarization successful with API key: {api_key}")
            break

        except Exception as e:
            logging.error(f"Failed with API key {api_key}: {e}")
            continue

    if not summarized_text:
        return jsonify({"error": "Summarization failed"}), 500

    return jsonify({"summarized_text": summarized_text}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
