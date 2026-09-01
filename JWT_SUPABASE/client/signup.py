import sys, os
sys.path.append(os.path.dirname(__file__))

from supabase_client import supabase

response = supabase.auth.sign_up({
    "email": "demo.user182006@gmail.com",
    "password": "DemoPass182006!"
})

if response.user:
    print("Signed up:", response.user.email)
else:
    print("Signup response:", response)
