# 🤖 Meme Mwitu Automation Bot

An automated Telegram-to-Facebook bot designed to streamline meme posting, generate viral captions using AI, and maximize engagement for the "Memes Mwitu" Facebook page.

## ✨ Features
- **Effortless Telegram Forwarding:** Forward single images, videos, or full albums of up to 10 memes to the bot.
- **Smart Caption Extraction:** Automatically extracts existing captions from forwarded Telegram posts.
- **AI-Powered Vibe Enhancement:** Uses the Groq API (LLaMA 3) to strictly generate 5 trending hashtags and a unique, funny Call-To-Action (CTA). Original captions are *never* altered.
- **Auto-Commenting Strategy:** Automatically drops the AI-generated CTA as the very first comment on the published Facebook post to boost algorithmic visibility.
- **Direct Text/Status Posting:** Use the `\text [Your message]` command in Telegram to instantly publish text-only status updates.
- **Video Support:** Fully supports uploading `.mp4` video files directly to Facebook.
- **Live Progress Updates:** Real-time feedback in Telegram as your media processes and uploads.

---

## 🚀 Deployment to Render.com (Free Tier)

This bot is designed to run 24/7 in the cloud. We strongly recommend deploying to **Render.com** using their free **Background Worker** service.

### ⚠️ IMPORTANT: Choosing the Right Render Service
Do **NOT** choose "Web Service". A Web Service expects a web server (like Flask or Gunicorn) and will fail to deploy this bot.

You **MUST** select **Background Worker**. A Background Worker simply runs a python script continuously, which is exactly how a Telegram polling bot works.

### Step-by-step Render Setup:
1. Log into your [Render Console](https://dashboard.render.com).
2. Click **New +** at the top right, and select **Background Worker**.
3. Connect your GitHub account and select this repository (`sibby-killer/memes_mwitu_bot_fb`).
4. Configure the Background Worker exactly like this:
   - **Name**: `Meme Mwitu Bot`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py` (Do *not* use gunicorn)
   - **Instance Type**: `Free`
5. Scroll down to **Environment** and click **Add Environment Variable**. Add your 4 secret keys:
   - `TELEGRAM_BOT_TOKEN`: (Your Token from BotFather)
   - `GROQ_API_KEY`: (Your Token from Groq)
   - `FACEBOOK_PAGE_ID`: `958540217347416`
   - `FACEBOOK_PAGE_ACCESS_TOKEN`: (Your Never-Expiring Page Token)
6. Click **Create Background Worker**.

*Render will build the project and turn the bot on permanently.*

---

## 🛠️ Local Development & Testing
If you want to run or test the bot locally on your Windows/Mac/Linux machine:

1. Clone the repository.
2. Create a `.env` file based on the provided `.env.example`.
3. Install dependencies:
   ```cmd
   pip install -r requirements.txt
   ```
4. Start the bot:
   ```cmd
   python bot.py
   ```

## 📚 Built With
- `python-telegram-bot` (v20+)
- `groq` (LLaMA 3 Inference)
- `requests` (Facebook Graph API integration)
