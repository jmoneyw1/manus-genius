import os
import openai
from flask import Flask, request, render_template, jsonify
from flask_cors import CORS

# Init Flask app
app = Flask(__name__)
CORS(app)

# Set OpenAI key from env variable
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    user_input = request.json.get('prompt')

    if not user_input:
        return jsonify({'error': 'No prompt provided'}), 400

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You're a helpful AI coding assistant."},
                {"role": "user", "content": user_input}
            ],
            temperature=0.4,
            max_tokens=800
        )

        answer = response['choices'][0]['message']['content']
        return jsonify({'response': answer})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting Manus-Genius with ChatGPT integration")
    app.run(host='0.0.0.0', port=5001, debug=True)
