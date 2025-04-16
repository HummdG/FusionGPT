"""
Test script to verify your OpenAI API key is working with OpenAI v1.0+ API.
Save this as a .py file in your add-in root directory and run it from the command line.
"""

import os

# Try to import from config.py
try:
    print("Trying to import API key from config.py...")
    from config import OPENAI_API_KEY
    api_key = OPENAI_API_KEY
    print(f"API key from config.py: {'*' * (len(api_key) - 4) + api_key[-4:] if api_key else 'Not found'}")
except:
    print("Could not import from config.py, checking environment variable...")
    api_key = os.environ.get("OPENAI_API_KEY", "")
    print(f"API key from environment: {'*' * (len(api_key) - 4) + api_key[-4:] if api_key else 'Not found'}")

# Verify the API key
if not api_key:
    print("ERROR: No API key found! Please set your OpenAI API key in config.py or as an environment variable.")
    exit(1)

# Try to use the API with the new v1.0+ format
try:
    print("\nTesting API key with OpenAI v1.0+ API...")
    from openai import OpenAI
    
    client = OpenAI(api_key=api_key)
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hello, this is a test."}],
        max_tokens=10
    )
    
    print(f"API test successful!")
    print(f"Model responded: {response.choices[0].message.content}")
    print("\nYour API key is working correctly with the OpenAI v1.0+ API.")
    
except Exception as e:
    print(f"ERROR: API test failed with error: {str(e)}")
    print("\nPlease check your API key and internet connection.")