# Meme Mwitu - Telegram to Facebook Automation
## Project Overview
The goal of this project is to automate the process of posting memes and content from Telegram directly to a Facebook Page. This saves time and ensures consistent engagement while leveraging AI to generate unique hashtags and Call-To-Action (CTA) comments.

## Problem Solving
Currently, manually saving memes, copying captions, generating tags, and posting them to Facebook is repetitive and time-consuming. This bot solves that by acting as a pipeline: 
1. Receive images + caption on Telegram.
2. Automatically generate trending hashtags and a unique, funny/foolish CTA without changing the original caption.
3. Post everything seamlessly to Facebook with the correct layout.
4. Auto-comment the CTA to boost algorithmic visibility (engagement).

## Core Features
1. **Telegram Listener Interface**: 
   - Accepts media groups (multiple meme forwarding).
   - Prompts the user for a caption if media is provided.
   - Accepts text-only posts via a specific command (`\text`).

2. **AI Augmentation (Groq API)**:
   - **Strict Rule**: The original caption is NEVER changed.
   - Groq is exclusively used to generate 5 trending hashtags and a short, funny, foolish CTA.
   - The CTA is uniquely generated every single time so it doesn't look like a bot.

3. **Facebook Publishing Algorithm (Graph API)**:
   - **Visuals**: Uses a consistent frame/carousel layout for multiple images (avoiding the classic messy FB collage crop).
   - **Auto-Commenting**: Immediately after the post goes live, the bot uses the Post ID to automatically drop the unique AI-generated CTA as the first comment.
   - **Text Only**: The `\text` command skips the image pipeline and simply posts the raw text to the page as a status.

## Hosting & Deployment (Free Tier)
Due to the nature of Telegram polling and webhooks, the application needs to run continuously.
- **Recommended Free Host**: **Render.com** (using a Web Service or Background Worker) or **PythonAnywhere**. 
- *Note on Streamlit*: Streamlit apps automatically "sleep" when no user is interacting with the web dashboard, meaning the bot would go offline. Therefore, a standard Python background worker on Render is the superior free choice.

## Necessary Setup / API Keys
1. **Facebook Graph API**: Page Access Token (configured to never expire) with `pages_manage_posts` and `pages_read_engagement` permissions.
2. **Telegram Bot Token**: From BotFather.
3. **Groq API Key**: For ultra-fast LLaMA-based AI inference.
