# Setup & Deployment Guide: Meme Mwitu Automation

This guide walks you through acquiring the necessary API keys, testing the bot on your Windows machine, and deploying it for free to PythonAnywhere.

---

## 🔑 Phase 1: Acquiring API Keys

### 1. Telegram Bot Token
1. Open Telegram and search for **@BotFather**.
2. Send the command `/newbot`.
3. Give your bot a display name (e.g., "Meme Mwitu Bot") and a unique username ending in `_bot`.
4. BotFather will reply with your **HTTP API Token** (it looks like `123456789:ABCdefGHI...`).
5. Copy this token and paste it into `.env` under `TELEGRAM_BOT_TOKEN`.

### 2. Groq API Key
1. Go to [console.groq.com](https://console.groq.com/) and create a free account.
2. Select "API Keys" from the sidebar and click **Create API Key**.
3. Name it and copy the key.
4. Paste it into `.env` under `GROQ_API_KEY`.

### 3. Facebook Page Access Token (The Tricky Part)
*Note: A standard Page Access Token expires after 60 days. This guide shows you how to get a **Never-Expiring** token so your bot never goes offline.*

#### Step A: Create a Facebook App
1. Go to [Facebook Developers](https://developers.facebook.com/) and log in.
2. Click **My Apps** (top right) -> **Create App**.
3. Select **Other** -> **Business** (or simply choose a standard app type if Business isn't visible).
4. Name your app "Meme Mwitu Poster" and link your Business Account if prompted. Create the App.

#### Step B: Get a Short-Lived User Token
1. In the developer sidebar, go to **Tools** -> **Graph API Explorer**.
2. On the right panel, under **Facebook App**, make sure your new app is selected.
3. Under **User or Page**, click the dropdown and select **Get Page Access Token**.
4. A popup will ask you to log into Facebook. **CRITICAL**: When it asks what pages you want to grant access to, select your *"Meme Mwitu"* page.
5. In the **Permissions** section on the Graph API Explorer, ensure you add:
   - `pages_manage_posts`
   - `pages_read_engagement`
6. Click **Generate Access Token**. You now have a short-lived *Page Access Token*. 
7. At the top of the Graph API Explorer, you'll see a query box containing `me?fields=id,name`. Change this to `me` and hit **Submit**.
8. Look at the JSON response box. Copy the `id` number. **Paste this into your `.env` as `FACEBOOK_PAGE_ID`**.

#### Step C: Convert to a Never-Expiring Token
1. Next to the "Access Token" field (where your new token is), click the **blue Info icon (i)**.
2. An "Access Token Info" box will popup. Click **Open in Access Token Tool**.
3. A new tab opens. Scroll down and click the blue button **Extend Access Token**. 
4. Facebook will generate a new, long-lived *User* Token. Copy this *User Token*.
5. Go back to the **Graph API Explorer**. Paste this new *long-lived User Token* into the Access Token box.
6. Under **User or Page**, click the dropdown and re-select your Page name. 
7. The token in the box will update one final time. **THIS is your Never-Expiring Page Access Token.** 
8. Copy it and paste it into `.env` as `FACEBOOK_PAGE_ACCESS_TOKEN`.

---

## 💻 Phase 2: Testing Locally (On Windows)

1. Open your terminal/command prompt in the `MEME MWITU AUTOMATION` folder.
2. Install the necessary Python packages by running:
   ```cmd
   pip install -r requirements.txt
   ```
3. Ensure your `.env` file is completely filled out. (Rename `.env.example` to `.env` if you haven't already).
4. Run the bot:
   ```cmd
   python bot.py
   ```
5. You should see `🤖 Meme Mwitu Bot is running`.
6. Open Telegram, find your bot, and send it `\text Testing my automated bot!`. Wait to see if it posts to Facebook!

---

## ☁️ Phase 3: Deploying to PythonAnywhere (Free 24/7 Hosting)

Once it works locally on your machine, we can move it to the cloud so it runs 24/7 without your computer needing to be on.

1. Create a free account at [PythonAnywhere.com](https://www.pythonanywhere.com/).
2. Once logged in, go to the **Files** tab.
3. Create a new folder named `meme_bot`.
4. Upload the following files into this folder:
   - `bot.py`
   - `config.py`
   - `facebook_client.py`
   - `groq_client.py`
   - `requirements.txt`
   - Your secret `.env` file.
5. Go to the **Consoles** tab and click **Bash** to open a cloud terminal.
6. Install dependencies in your cloud environment:
   ```bash
   pip3.10 install --user -r ~/meme_bot/requirements.txt
   ```
7. Go to the **Tasks** tab (also called "Always-on tasks", but free accounts don't have this. Instead, we use Scheduled Tasks or keep a console alive).
8. **Alternative Free Method (Since standard PythonAnywhere "Always-On" costs $5/mo):**
   - Open a **Bash Console** in PythonAnywhere.
   - Run: `cd ~/meme_bot`
   - Run: `python3.10 bot.py`
   - The bot will stay alive as long as PythonAnywhere doesn't reboot the server. If it stops, you'll just need to log in and restart that command. 
   *(If you want true "set-it-and-forget-it" free hosting, you may want to look into **Render.com** Background Workers instead).*
