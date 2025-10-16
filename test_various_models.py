from openai import OpenAI
import sys

def test_model(model_name, api_key):
    try:
        client = OpenAI(api_key=api_key, base_url="http://localhost:7000/v1")
        result = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": "Say 'test ok' in 3 words."}],
            max_tokens=20
        )
        response = result.choices[0].message.content
        print(f"✅ Model: {model_name:20} | API Key: {api_key:15} | Response: {response[:50]}")
        return True
    except Exception as e:
        print(f"❌ Model: {model_name:20} | API Key: {api_key:15} | Error: {str(e)[:50]}")
        return False

# Test various model names
models = ["gpt-5", "gpt-4", "gpt-4-turbo", "claude-3-opus", "gemini-pro"]
api_keys = ["sk-any", "sk-test", "sk-fake-key-123"]

print("=" * 100)
print("Testing Universal Model and API Key Support")
print("=" * 100)

for model in models:
    for api_key in api_keys:
        test_model(model, api_key)
        
print("=" * 100)
