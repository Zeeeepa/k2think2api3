# 🐍 Using Python with K2Think API

## ⚠️ Important: Always Use the Virtual Environment

This project uses a Python virtual environment (`venv`) to manage dependencies. **You must activate it before running Python scripts.**

## 🚀 Quick Start (Recommended)

### Option 1: Use the Python Wrapper
```bash
./python-k2 your_script.py
```
or
```bash
./python-k2 -c "from openai import OpenAI; print('Works!')"
```

The `python-k2` wrapper automatically:
- Activates the virtual environment
- Sets `OPENAI_API_KEY` 
- Sets `OPENAI_BASE_URL`
- Runs your Python script

### Option 2: Activate Environment Manually
```bash
source activate-k2.sh
python3 your_script.py
```

### Option 3: Traditional venv Activation
```bash
source venv/bin/activate
export OPENAI_API_KEY="sk-k2think-proxy-xxx"
export OPENAI_BASE_URL="http://localhost:7321/v1"
python3 your_script.py
```

## ❌ Common Mistake

**DON'T** run Python scripts directly without activating the venv:
```bash
python your_script.py  # ❌ This will fail!
```

You'll get errors like:
- `externally-managed-environment`
- `ModuleNotFoundError: No module named 'openai'`

## ✅ Correct Usage

```bash
# Always use one of these methods:
./python-k2 your_script.py           # Method 1 (easiest)
source activate-k2.sh && python3 ... # Method 2  
source venv/bin/activate && python3 ...  # Method 3
```

## 📝 Example Script

Create a file `test.py`:
```python
from openai import OpenAI

client = OpenAI()  # Uses env vars automatically

response = client.chat.completions.create(
    model="gpt-4",  # Any model name works!
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)
```

Run it:
```bash
./python-k2 test.py
```

That's it! 🎉
