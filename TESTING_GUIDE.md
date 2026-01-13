# Testing Guide: TMDB Authentication

This guide will help you test your TMDB authentication locally and deploy to Streamlit Cloud.

## 🔑 Your TMDB Bearer Token

Based on your curl command, your Bearer token is:
```
eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI3YWE4ZWQwMmRiMjgyODQxNDU2MjM0ZTM1ZjE0MDFhMSIsIm5iZiI6MTU5MTI3MzgzMC4zMjksInN1YiI6IjVlZDhlOTY2ZmVhMGQ3MDAxZjhkNjBlMSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.-Tg-DA_11HGtYZdurd2RmB3E21-kaYHpEyhW1WJsXO0
```

---

## 📍 Step 1: Test Locally (On Your Computer)

### Option A: Test with the Test Script (Recommended)

1. **Open PowerShell or Command Prompt** in your project directory

2. **Set the environment variable** (choose one based on your shell):

   **PowerShell:**
   ```powershell
   $env:TMDB_ACCESS_TOKEN="eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI3YWE4ZWQwMmRiMjgyODQxNDU2MjM0ZTM1ZjE0MDFhMSIsIm5iZiI6MTU5MTI3MzgzMC4zMjksInN1YiI6IjVlZDhlOTY2ZmVhMGQ3MDAxZjhkNjBlMSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.-Tg-DA_11HGtYZdurd2RmB3E21-kaYHpEyhW1WJsXO0"
   ```

   **Command Prompt (CMD):**
   ```cmd
   set TMDB_ACCESS_TOKEN=eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI3YWE4ZWQwMmRiMjgyODQxNDU2MjM0ZTM1ZjE0MDFhMSIsIm5iZiI6MTU5MTI3MzgzMC4zMjksInN1YiI6IjVlZDhlOTY2ZmVhMGQ3MDAxZjhkNjBlMSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.-Tg-DA_11HGtYZdurd2RmB3E21-kaYHpEyhW1WJsXO0
   ```

3. **Run the test script:**
   ```bash
   python test_tmdb_api_key.py
   ```

4. **Expected output:**
   ```
   ============================================================
   🔑 TMDB Authentication Tester
   ============================================================
   
   Testing Bearer token: eyJhbGci...
   (Using v4 API with Bearer token authentication)
   
   ✅ Bearer token is VALID!
      Test movie: The Matrix (1999-03-30)
   
   ============================================================
   ✅ Your Bearer token is working correctly!
   ============================================================
   ```

### Option B: Test by Running the Streamlit App Locally

1. **Set the environment variable** (same as above)

2. **Run Streamlit:**
   ```bash
   streamlit run app/main.py
   ```

3. **Check if it works:**
   - The app should open in your browser
   - Try searching for a movie
   - If poster images appear, your token is working! ✅
   - If no posters appear, check the terminal for errors

### Option C: Create a .env File (Permanent Local Setup)

1. **Create a file named `.env`** in your project root (same folder as `app/` and `src/`)

2. **Add this line to `.env`:**
   ```
   TMDB_ACCESS_TOKEN=eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI3YWE4ZWQwMmRiMjgyODQxNDU2MjM0ZTM1ZjE0MDFhMSIsIm5iZiI6MTU5MTI3MzgzMC4zMjksInN1YiI6IjVlZDhlOTY2ZmVhMGQ3MDAxZjhkNjBlMSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.-Tg-DA_11HGtYZdurd2RmB3E21-kaYHpEyhW1WJsXO0
   ```

3. **Make sure `.env` is in `.gitignore`** (so you don't accidentally commit your token)

4. **Now you can run Streamlit without setting environment variables:**
   ```bash
   streamlit run app/main.py
   ```

---

## ☁️ Step 2: Deploy to Streamlit Cloud

### Step 2.1: Commit and Push Your Changes

1. **Check what files changed:**
   ```bash
   git status
   ```

2. **Add the changed files:**
   ```bash
   git add app/main.py src/config.py test_tmdb_api_key.py
   ```

3. **Commit:**
   ```bash
   git commit -m "Add Bearer token support for TMDB API"
   ```

4. **Push to GitHub:**
   ```bash
   git push origin main
   ```

### Step 2.2: Set Environment Variable in Streamlit Cloud

1. **Go to Streamlit Cloud:**
   - Visit: https://share.streamlit.io/
   - Log in with your GitHub account

2. **Open your app settings:**
   - Click on your app (or create a new one if you haven't)
   - Click the **"⋮" (three dots)** menu in the top right
   - Select **"Settings"**

3. **Add the secret:**
   - Scroll down to **"Secrets"** section
   - Click **"Edit secrets"** or **"Add secret"**
   - Add this line:
     ```
     TMDB_ACCESS_TOKEN=eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI3YWE4ZWQwMmRiMjgyODQxNDU2MjM0ZTM1ZjE0MDFhMSIsIm5iZiI6MTU5MTI3MzgzMC4zMjksInN1YiI6IjVlZDhlOTY2ZmVhMGQ3MDAxZjhkNjBlMSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.-Tg-DA_11HGtYZdurd2RmB3E21-kaYHpEyhW1WJsXO0
     ```

4. **Save the secrets**

### Step 2.3: Verify App Configuration

1. **Check your app settings:**
   - Make sure **"Main file path"** is set to: `app/main.py`
   - Make sure **"Python version"** is appropriate (3.8+)

2. **Redeploy:**
   - If your app is already deployed, Streamlit Cloud will automatically redeploy when you:
     - Push changes to GitHub, OR
     - Update secrets
   - You can also manually trigger a redeploy by clicking **"Reboot app"** in the settings

### Step 2.4: Test on Streamlit Cloud

1. **Wait for deployment to complete:**
   - Check the deployment logs in Streamlit Cloud
   - Look for: `✅ The service is healthy and ready to accept traffic`

2. **Open your app:**
   - Click **"Open app"** or visit your app URL

3. **Test the functionality:**
   - Search for a movie (e.g., "The Matrix")
   - Check if poster images appear
   - If posters show up → ✅ Your token is working!
   - If no posters → Check the logs for errors

---

## 🐛 Troubleshooting

### Local Testing Issues

**Problem:** `python test_tmdb_api_key.py` says token is invalid
- **Solution:** Double-check you copied the entire token (it's very long)
- Make sure there are no extra spaces or quotes

**Problem:** Streamlit app runs but no posters appear
- **Solution:** 
  1. Check terminal for error messages
  2. Verify the environment variable is set: `echo $env:TMDB_ACCESS_TOKEN` (PowerShell)
  3. Try the test script first to verify the token works

### Streamlit Cloud Issues

**Problem:** App still shows health check error
- **Solution:**
  1. Check deployment logs for specific errors
  2. Verify `app/main.py` is the correct main file path
  3. Make sure all dependencies are in `requirements.txt`

**Problem:** App runs but no posters
- **Solution:**
  1. Check that `TMDB_ACCESS_TOKEN` is set in Secrets (not `TMDB_API_KEY`)
  2. Verify the token value is correct (no extra spaces)
  3. Check the app logs for API errors

**Problem:** "Connection refused" error
- **Solution:**
  1. This usually means the app crashed during startup
  2. Check the logs for Python errors
  3. Make sure all imports work (database, config, etc.)

---

## ✅ Quick Checklist

Before deploying to Streamlit Cloud:

- [ ] Tested locally with `test_tmdb_api_key.py` → ✅ Works
- [ ] Tested locally with `streamlit run app/main.py` → ✅ Posters appear
- [ ] Committed and pushed changes to GitHub
- [ ] Set `TMDB_ACCESS_TOKEN` in Streamlit Cloud Secrets
- [ ] Verified main file path is `app/main.py`
- [ ] App deploys successfully on Streamlit Cloud
- [ ] Posters appear in the deployed app

---

## 📝 Notes

- **Bearer tokens** are preferred over API keys (newer, more secure)
- The app will work without authentication, but won't show poster images
- Your token is sensitive - never commit it to GitHub
- If your token expires, you'll need to generate a new one from TMDB

---

## 🆘 Need Help?

If something doesn't work:
1. Check the error messages in the terminal/logs
2. Verify your token is correct by testing with the test script
3. Make sure all files are saved and committed
4. Try redeploying on Streamlit Cloud
