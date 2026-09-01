import os
import jwt
from functools import wraps
from flask import request, jsonify

_jwks_client = jwt.PyJWKClient(
    f"{os.environ.get('SUPABASE_URL')}/auth/v1/.well-known/jwks.json"
)

def verify_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or malformed token"}), 401

        token = auth_header.split(" ")[1]

        try:
            signing_key = _jwks_client.get_signing_key_from_jwt(token)
            decoded = jwt.decode(
                token,
                signing_key.key,
                algorithms=["ES256"],
                audience="authenticated"
            )
            request.user = decoded
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        return f(*args, **kwargs)
    return decorated
