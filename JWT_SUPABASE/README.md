# Supabase + JWT Demo

A minimal demo project showing how [Supabase](https://supabase.com) issues and verifies **JWT (JSON Web Tokens)** for authenticated API access. It covers signing up/logging in a user, inspecting the JWT Supabase returns, and verifying that token on a protected backend route.

## What This Demo Covers

- Creating a Supabase project and enabling email/password auth
- Signing up and logging in a user via the Supabase client SDK
- Decoding and inspecting the JWT Supabase issues on login
- Sending the JWT to a backend API in the `Authorization: Bearer <token>` header
- Verifying the JWT server-side (using Supabase's JWT secret / public key)
- Accessing a protected route only with a valid token

## Tech Stack

- **Client**: Python using `supabase-py`
- **Backend**: Python + Flask (verifies incoming JWTs)
- **Auth Provider**: Supabase Auth (issues JWTs on login/signup)
- **JWT Verification**: `PyJWT` package

## Project Structure

```
supabase-jwt-demo/
├── client/
│   ├── signup.py         # Signs up a new user
│   ├── login.py          # Logs in and prints the JWT
│   └── supabase_client.py
├── server/
│   ├── app.py             # Flask server with protected route
│   └── verify_token.py    # JWT verification decorator
├── .env.example
├── requirements.txt
└── README.md
```

## Prerequisites

- Python 3.9+
- A free [Supabase](https://supabase.com) account and project
- pip (or a virtual environment tool like `venv`)

## Setup

### 1. Create a Supabase Project

1. Go to [supabase.com](https://supabase.com) and create a new project.
2. Under **Project Settings → API**, note down:
   - `Project URL`
   - `anon public` key
   - `JWT Secret` (under **Project Settings → API → JWT Settings**)

### 2. Clone and Install

```bash
git clone <your-repo-url>
cd supabase-jwt-demo
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

`requirements.txt`:

```
supabase
flask
pyjwt
python-dotenv
```

### 3. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_JWT_SECRET=your-jwt-secret
PORT=4000
```

## Running the Demo

### 1. Sign Up a User

```bash
python client/signup.py
```

### 2. Log In and Get a JWT

```bash
python client/login.py
```

This prints the `access_token` (JWT) Supabase issues. Copy it — you'll use it to call the protected route.

### 3. Start the Backend Server

```bash
python server/app.py
```

Server runs at `http://localhost:4000`.

### 4. Call the Protected Route

```bash
curl http://localhost:4000/protected \
  -H "Authorization: Bearer <paste-your-jwt-here>"
```

- **Valid token** → returns the decoded user info (`sub`, `email`, `exp`, etc.)
- **Missing/invalid/expired token** → returns `401 Unauthorized`

## Example Client Code

`client/supabase_client.py`:

```python
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_ANON_KEY")

supabase: Client = create_client(url, key)
```

`client/login.py`:

```python
from supabase_client import supabase

response = supabase.auth.sign_in_with_password({
    "email": "test@example.com",
    "password": "password123"
})

access_token = response.session.access_token
print("JWT:", access_token)
```

## How JWT Verification Works Here

1. Supabase signs JWTs using your project's **JWT secret** (HS256 by default).
2. The Flask server's `verify_token.py` decorator:
   - Extracts the token from the `Authorization` header
   - Verifies the signature using `SUPABASE_JWT_SECRET`
   - Checks the `exp` claim to reject expired tokens
   - Attaches the decoded user payload to `request.user`

```python
import os
import jwt
from functools import wraps
from flask import request, jsonify

SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET")

def verify_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or malformed token"}), 401

        token = auth_header.split(" ")[1]

        try:
            decoded = jwt.decode(
                token,
                SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated"
            )
            request.user = decoded
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        return f(*args, **kwargs)
    return decorated
```

`server/app.py`:

```python
from flask import Flask, jsonify, request
from verify_token import verify_token

app = Flask(__name__)

@app.route("/protected")
@verify_token
def protected():
    return jsonify({"message": "Access granted", "user": request.user})

if __name__ == "__main__":
    app.run(port=4000)
```

## Notes & Gotchas

- Supabase JWTs expire by default (commonly after 1 hour) — use the `refresh_token` to get a new one without re-login.
- Never expose your `SUPABASE_JWT_SECRET` or `service_role` key on the client — only the `anon` key belongs in frontend code.
- For production apps, prefer Supabase's built-in **Row Level Security (RLS)** policies over manual JWT checks wherever possible — RLS uses the JWT's claims automatically at the database level.

## References

- [Supabase Auth Docs](https://supabase.com/docs/guides/auth)
- [Supabase JWT Docs](https://supabase.com/docs/guides/auth/jwts)
- [PyJWT (PyPI)](https://pypi.org/project/PyJWT/)
- [supabase-py (PyPI)](https://pypi.org/project/supabase/)
