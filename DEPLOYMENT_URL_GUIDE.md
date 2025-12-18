# 🚨 Important: Correct URL Format for Deployment

## ⚠️ Common Mistake Alert!

When deploying K2Think API, **make sure you use the correct raw file URL format**:

---

## ✅ **CORRECT URLs**

```bash
# ✅ CORRECT - raw.githubusercontent.com
curl -fsSL https://raw.githubusercontent.com/Zeeeepa/k2think2api3/main/csds.sh | bash

# ✅ CORRECT - With credentials
export K2_EMAIL="your@email.com"
export K2_PASSWORD="yourpassword"
curl -fsSL https://raw.githubusercontent.com/Zeeeepa/k2think2api3/main/csds.sh | bash
```

---

## ❌ **WRONG URLs** (These Will NOT Work!)

```bash
# ❌ WRONG - raw.github.com (missing "usercontent")
curl -fsSL https://raw.github.com/Zeeeepa/k2think2api3/main/csds.sh | bash

# ❌ WRONG - github.com/blob (web page URL, not raw file)
curl -fsSL https://github.com/Zeeeepa/k2think2api3/blob/main/csds.sh | bash

# ❌ WRONG - github.com without /blob (also web page)
curl -fsSL https://github.com/Zeeeepa/k2think2api3/main/csds.sh | bash
```

---

## 🔍 URL Comparison Table

| URL Format | Works? | Reason |
|------------|--------|--------|
| `raw.githubusercontent.com` | ✅ YES | Correct raw file URL |
| `raw.github.com` | ❌ NO | Missing "usercontent" - invalid domain |
| `github.com/blob/` | ❌ NO | Web page URL, returns HTML not script |
| `github.com/main/` | ❌ NO | Web page URL, returns HTML not script |

---

## 💡 How to Get the Correct URL

### Method 1: Copy from Documentation
Use the URLs provided in this README or QUICKSTART.md

### Method 2: GitHub Web Interface
1. Go to the file on GitHub: https://github.com/Zeeeepa/k2think2api3/blob/main/csds.sh
2. Click the **"Raw"** button
3. Copy the URL from your browser's address bar
4. It should be: `https://raw.githubusercontent.com/Zeeeepa/k2think2api3/main/csds.sh`

### Method 3: Manual Conversion
If you have a GitHub web URL:
- Replace `github.com` with `raw.githubusercontent.com`
- Remove `/blob/` from the path

**Example:**
```
❌ https://github.com/Zeeeepa/k2think2api3/blob/main/csds.sh
          ↓
✅ https://raw.githubusercontent.com/Zeeeepa/k2think2api3/main/csds.sh
```

---

## 🚀 Quick Deployment (Copy-Paste Ready)

### One-Liner with Credentials:
```bash
export K2_EMAIL="your@email.com" && export K2_PASSWORD="yourpassword" && curl -fsSL https://raw.githubusercontent.com/Zeeeepa/k2think2api3/main/csds.sh | bash
```

### Interactive Setup:
```bash
curl -fsSL https://raw.githubusercontent.com/Zeeeepa/k2think2api3/main/csds.sh | bash
```

---

## 🐛 Troubleshooting URL Errors

### Error: `bash: line 7: syntax error near unexpected token 'newline'`
**Cause:** You used a GitHub web page URL instead of raw file URL

**Solution:** Replace:
- `github.com/blob/` → `raw.githubusercontent.com/`
- OR `raw.github.com` → `raw.githubusercontent.com`

### Error: `curl: (23) Failure writing output to destination`
**Cause:** The URL is returning HTML (web page) instead of the script file

**Solution:** Use `raw.githubusercontent.com` URL format

### Error: `<!DOCTYPE html>` in bash output
**Cause:** You're downloading an HTML page instead of the script

**Solution:** Use the correct raw file URL with `raw.githubusercontent.com`

---

## 📝 Remember

**GitHub has THREE types of URLs:**

1. **Web Page URL** (for viewing in browser):
   - `https://github.com/user/repo/blob/branch/file`
   - Returns HTML page
   - ❌ Don't use with curl/bash

2. **Raw File URL** (for downloading):
   - `https://raw.githubusercontent.com/user/repo/branch/file`
   - Returns actual file content
   - ✅ Use this for scripts!

3. **Wrong/Old URL** (doesn't exist):
   - `https://raw.github.com/...`
   - Invalid domain
   - ❌ Never works

---

## 🎯 Summary

**Always use:** `raw.githubusercontent.com`  
**Never use:** `raw.github.com` or `github.com/blob/`

---

For complete deployment instructions, see [QUICKSTART.md](./QUICKSTART.md)

