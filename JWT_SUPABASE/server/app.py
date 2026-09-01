import os
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, jsonify, request
from verify_token import verify_token

app = Flask(__name__)

@app.route("/protected")
@verify_token
def protected():
    return jsonify({"message": "Access granted", "user": request.user})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 4000))
    app.run(port=port)
