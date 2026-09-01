import sys, os
sys.path.append(os.path.dirname(__file__))

from supabase_client import supabase

response = supabase.auth.sign_in_with_password({
    "email": "demo.user182006@gmail.com",
    "password": "DemoPass182006!"
})

access_token = response.session.access_token
print("JWT:", access_token)
