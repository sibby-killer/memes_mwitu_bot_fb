import os
import asyncio
import time
import uuid
from typing import Dict, Any
from collections import defaultdict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

import config
import groq_client
import facebook_client
from keep_alive import keep_alive

# Define States for ConversationHandler
AWAITING_CAPTION = 1

# Temporary storage for downloaded images/videos
# { user_id: {"files": ["path/to/img1.jpg", "path/to/vid.mp4"], "caption": "original caption"} }
user_media_cache: Dict[int, Dict[str, Any]] = defaultdict(lambda: {"files": [], "caption": ""})

# Keep track of active progress messages
progress_messages: Dict[int, int] = {}

# Keep track of running background tasks: { "task_id" : {"task": asyncio.Task, "description": "...", "start_time": time.time(), "user_id": int} }
active_tasks: Dict[str, Dict[str, Any]] = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        "🚀 Meme Mwitu Bot is online!\n\n"
        "Here's how to use me:\n"
        "1. Forward or send up to 10 images/videos at once. Use albums if you like.\n"
        "2. If your forwarded album already has a caption, I will automatically process and post it!\n"
        "3. If there is no caption, I will ask you for one.\n"
        "4. Send `\\text [Your message]` to immediately post a text-only status.\n"
        "5. Send `/menu` to view tasks or `/schedule` to schedule posts for later."
    )

async def handle_text_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle \text [message] commands"""
    text = update.message.text
    if not text.startswith('\\text'):
        return
        
    content = text.replace('\\text', '').strip()
    if not content:
        await update.message.reply_text("Please provide text after the command. Example: `\\text Hello Facebook!`")
        return

    msg = await update.message.reply_text("🔄 Processing text-only post via AI...")
    
    vibe = groq_client.enhance_vibe(content)
    final_caption = f"{content}\n\n{vibe['hashtags']}"
    
    # Check if a schedule time is universally set
    scheduled_time = context.user_data.get('schedule_time')
    if scheduled_time:
        context.user_data['schedule_time'] = None # consume it
        
    try:
        post_id = facebook_client.publish_text_only(final_caption, scheduled_time)
        if scheduled_time:
            await context.bot.edit_message_text(f"✅ Successfully SCHEDULED to Facebook!\n\n**Note**: CTA comments cannot be added to unpublished scheduled posts.", chat_id=update.effective_chat.id, message_id=msg.message_id)
        else:
            facebook_client.post_comment(post_id, vibe['cta'])
            await context.bot.edit_message_text(f"✅ Successfully posted to Facebook!\n\n**Comment added**: {vibe['cta']}", chat_id=update.effective_chat.id, message_id=msg.message_id)
    except Exception as e:
        await context.bot.edit_message_text(f"❌ {str(e)}", chat_id=update.effective_chat.id, message_id=msg.message_id)

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle incoming photos and videos.
    Extracts existing captions if they exist in the forwarded album.
    """
    user_id = update.effective_user.id
    os.makedirs("temp_images", exist_ok=True)
    
    # Check if this media has a caption attached
    if update.message.caption:
        user_media_cache[user_id]["caption"] = update.message.caption
        
    # Download the media
    if update.message.photo:
        file = await update.message.photo[-1].get_file()
        ext = "jpg"
    elif update.message.video:
        file = await update.message.video.get_file()
        ext = "mp4"
    else:
        return AWAITING_CAPTION
        
    file_path = f"temp_images/{file.file_id}.{ext}"
    await file.download_to_drive(file_path)
    
    user_media_cache[user_id]["files"].append(file_path)
    
    # Cancel any existing timeout job for this user
    current_job = context.chat_data.get(f"timeout_job_{user_id}")
    if current_job:
        current_job.schedule_removal()
    
    # Wait 4 seconds for the rest of the album to arrive
    new_job = context.job_queue.run_once(
        trigger_caption_request, 
        when=4, 
        data={"user_id": user_id, "chat_id": update.effective_chat.id}
    )
    context.chat_data[f"timeout_job_{user_id}"] = new_job
    
    return AWAITING_CAPTION

async def trigger_caption_request(context: ContextTypes.DEFAULT_TYPE):
    """Fired when an album finishes uploading to the bot."""
    data = context.job.data
    user_id = data["user_id"]
    chat_id = data["chat_id"]
    
    cached_data = user_media_cache.get(user_id, {})
    files = cached_data.get("files", [])
    num_files = len(files)
    
    if num_files == 0:
        return
        
    # Check if a caption was extracted from the forwarded album
    existing_caption = cached_data.get("caption", "").strip()
    
    if existing_caption:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"✅ Received {num_files} items.\n\nFound caption: *'{existing_caption}'*\n\nStarting processing now...",
            parse_mode="Markdown"
        )
        # We start the background upload wrapped in tracking
        start_tracking_process(user_id, context.bot, chat_id, context.user_data)
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"✅ Received {num_files} images/videos.\n\n⚠️ No caption found. Please send the caption you want to use."
        )

async def handle_manual_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receives the manual caption if none was forwarded."""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    caption = update.message.text
    
    cached_data = user_media_cache.get(user_id, {})
    if not cached_data.get("files"):
        await update.message.reply_text("No media found in memory. Please send the images again.")
        return ConversationHandler.END
        
    user_media_cache[user_id]["caption"] = caption
    start_tracking_process(user_id, context.bot, chat_id, context.user_data)
    
    return ConversationHandler.END

async def edit_progress(bot, chat_id: int, message_id: int, text: str):
    """Helper to safely edit progress messages."""
    try:
        await bot.edit_message_text(text, chat_id=chat_id, message_id=message_id)
    except Exception as e:
        print(f"Failed to edit progress: {e}")

def start_tracking_process(user_id: int, bot, chat_id: int, user_data: dict):
    """Wraps process_upload into an asyncio Task for the dashboard to track."""
    task_id = str(uuid.uuid4())[:8]
    files = user_media_cache.get(user_id, {}).get("files", [])
    
    # Store in global tasks so we can kill it
    task = asyncio.create_task(process_upload(user_id, bot, chat_id, user_data, task_id))
    active_tasks[task_id] = {
        'task': task,
        'description': f"Facebook Upload ({len(files)} items)",
        'start_time': time.time()
    }
    
    def cleanup_task(t):
        if task_id in active_tasks:
            del active_tasks[task_id]
            
    task.add_done_callback(cleanup_task)

async def process_upload(user_id: int, bot, chat_id: int, user_data: dict, task_id: str):
    """Handles the heavy lifting: AI generation, media uploading, publishing."""
    try:
        cached_data = user_media_cache.get(user_id, {})
        files = cached_data.get("files", [])
        caption = cached_data.get("caption", "")
        
        if not files:
            cleanup_temp_files(user_id)
            return
            
        # Check if we should schedule this instead of posting now
        scheduled_time = user_data.get('schedule_time')
        if scheduled_time:
            user_data['schedule_time'] = None # consume it
            
        sched_msg = f"\n\n⏰ **SCHEDULED TO POST IN {int((scheduled_time - time.time())/3600)} HOURS**" if scheduled_time else ""
            
        # Start Progress Message
        prog_msg = await bot.send_message(chat_id=chat_id, text=f"⏳ Processing {len(files)} items... [Task: {task_id}]{sched_msg}\n\nStep 1/3: Asking Groq AI for hashtags and CTA...")
        msg_id = prog_msg.message_id
        
        # 1. Enhance Vibe (Groq)
        vibe = groq_client.enhance_vibe(caption)
        final_caption = f"{caption}\n\n{vibe['hashtags']}"
        
        # Check if there's only 1 file and it's a video
        if len(files) == 1 and files[0].endswith(".mp4"):
            await edit_progress(bot, chat_id, msg_id, f"⏳ Step 2/3: Uploading Video direct to Facebook... [Task {task_id}]")
            try:
                post_id = facebook_client.upload_video(files[0], final_caption, scheduled_time)
                if scheduled_time:
                    await edit_progress(bot, chat_id, msg_id, f"✅ Successfully SCHEDULED the Video!\n\n**Note**: Facebook restricts adding CTA comments to unpublished scheduled posts.")
                else:
                    await edit_progress(bot, chat_id, msg_id, f"⏳ Step 3/3: Posting CTA Comment... [Task {task_id}]")
                    facebook_client.post_comment(post_id, vibe['cta'])
                    await edit_progress(bot, chat_id, msg_id, f"✅ Successfully posted the Video!\n\n**Comment added**: {vibe['cta']}")
            except Exception as e:
                await edit_progress(bot, chat_id, msg_id, f"❌ {str(e)}")
                
            cleanup_temp_files(user_id)
            return

        # 2. Upload photos to FB to get Media IDs (Carousel approach)
        media_ids = []
        
        for idx, path in enumerate(files):
            if path.endswith(".mp4"):
                continue 
                
            await edit_progress(bot, chat_id, msg_id, f"⏳ Step 2/3: Uploading photo {idx+1} of {len(files)} to Facebook... [Task {task_id}]")
            try:
                mid = facebook_client.upload_photo(path, is_local=True)
                media_ids.append(mid)
            except Exception as e:
                await edit_progress(bot, chat_id, msg_id, f"❌ {str(e)}")
                cleanup_temp_files(user_id)
                return
                
        if not media_ids:
            await edit_progress(bot, chat_id, msg_id, "❌ Failed to upload any images. Fb requires 1 video per post.")
            cleanup_temp_files(user_id)
            return
            
        # 3. Publish Carousel Post
        await edit_progress(bot, chat_id, msg_id, f"⏳ Step 3/3: Publishing Album/Carousel with {len(media_ids)} images... [Task {task_id}]")
        try:
            post_id = facebook_client.publish_carousel(media_ids, final_caption, scheduled_time)
            
            if scheduled_time:
                await edit_progress(bot, chat_id, msg_id, f"✅ Successfully SCHEDULED {len(media_ids)} images to Facebook!\n\n**Note**: Cannot post CTA comments to scheduled posts until they go live.")
            else:
                await edit_progress(bot, chat_id, msg_id, f"⏳ Almost done... Posting CTA comment...")
                facebook_client.post_comment(post_id, vibe['cta'])
                group_links = "\n\n💡 *Reminder: Share this post to your groups!*"
                await edit_progress(bot, chat_id, msg_id, f"✅ Successfully posted {len(media_ids)} images to Facebook!\n\n**Comment**: {vibe['cta']}{group_links}")
        except Exception as e:
            await edit_progress(bot, chat_id, msg_id, f"❌ {str(e)}")
            
    except asyncio.CancelledError:
        print(f"Task {task_id} was cancelled globally")
        try:
            await edit_progress(bot, chat_id, msg_id, f"🛑 Task {task_id} was forcefully terminated via Dashboard.")
        except:
            pass
    finally:
        cleanup_temp_files(user_id)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels and ends the conversation."""
    user_id = update.effective_user.id
    cleanup_temp_files(user_id)
    await update.message.reply_text("Cancelled. You can send an image album or command again.")
    return ConversationHandler.END
    
def cleanup_temp_files(user_id: int):
    """Deletes temporary images and clears user cache."""
    cached_data = user_media_cache.get(user_id, {})
    files = cached_data.get("files", [])
    for path in files:
        if os.path.exists(path):
            try:
                os.remove(path)
            except:
                pass
    user_media_cache[user_id] = {"files": [], "caption": ""}

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows the interactive dashboard."""
    keyboard = [
        [InlineKeyboardButton("📊 View Active Uploads", callback_data="view_tasks")],
        [InlineKeyboardButton("🛑 Kill All Tasks", callback_data="kill_all")],
        [InlineKeyboardButton("📅 Schedule Next Post", callback_data="schedule_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🎛 **Meme Mwitu Control Panel**", reply_markup=reply_markup, parse_mode="Markdown")

async def schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Alias for schedule via menu."""
    keyboard = [
        [InlineKeyboardButton("1 Hour", callback_data="sched_1"), InlineKeyboardButton("3 Hours", callback_data="sched_3")],
        [InlineKeyboardButton("6 Hours", callback_data="sched_6"), InlineKeyboardButton("12 Hours", callback_data="sched_12")],
        [InlineKeyboardButton("24 Hours", callback_data="sched_24"), InlineKeyboardButton("Cancel", callback_data="sched_cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📅 **Schedule Next Post**\nWhen should the next post be published on Facebook?", reply_markup=reply_markup, parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles all inline keyboard button taps."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    
    if data == "view_tasks":
        if not active_tasks:
            await query.edit_message_text("✅ No active uploads or processes running.")
            return
            
        text = "📊 **Active Processes:**\n\n"
        for tid, tinfo in active_tasks.items():
            elapsed = int(time.time() - tinfo['start_time'])
            text += f"- `[Task {tid}]` {tinfo['description']} ({elapsed}s ago)\n"
            
        keyboard = [
            [InlineKeyboardButton("🛑 Kill All", callback_data="kill_all")], 
            [InlineKeyboardButton("🔄 Refresh", callback_data="view_tasks")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        
    elif data == "kill_all":
        count = 0
        for tid, tinfo in list(active_tasks.items()):
            tinfo['task'].cancel()
            count += 1
            
        active_tasks.clear()
        
        # forcefully delete anything left over
        for root, dirs, files in os.walk("temp_images"):
            for file in files:
                try: os.remove(os.path.join(root, file))
                except: pass
        
        await query.edit_message_text(f"🛑 Terminated {count} background processes and cleared cache.")
        
    elif data == "schedule_menu":
        keyboard = [
            [InlineKeyboardButton("1 Hour", callback_data="sched_1"), InlineKeyboardButton("3 Hours", callback_data="sched_3")],
            [InlineKeyboardButton("6 Hours", callback_data="sched_6"), InlineKeyboardButton("12 Hours", callback_data="sched_12")],
            [InlineKeyboardButton("24 Hours", callback_data="sched_24"), InlineKeyboardButton("Cancel", callback_data="sched_cancel")]
        ]
        await query.edit_message_text("📅 **Schedule Next Post**\nWhen should the next post be published on Facebook?", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        
    elif data.startswith("sched_"):
        val = data.split("_")[1]
        if val == "cancel":
            context.user_data['schedule_time'] = None
            await query.edit_message_text("❌ Scheduled mode cancelled. Next post will publish immediately.")
        else:
            hours = int(val)
            publish_time = int(time.time()) + (hours * 3600)
            context.user_data['schedule_time'] = publish_time
            await query.edit_message_text(f"✅ **Schedule Mode ON!**\n\nThe VERY NEXT post you forward/upload will be published in exactly **{hours} hours** on Meta Business Suite.\n\nSend me the images when ready!", parse_mode="Markdown")

def main():
    """Start the bot."""
    if not config.TELEGRAM_BOT_TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN is missing in .env")
        return

    # Start the background flask web server to keep Render happy
    keep_alive()

    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.PHOTO | filters.VIDEO, handle_media)],
        states={
            AWAITING_CAPTION: [
                MessageHandler(filters.PHOTO | filters.VIDEO, handle_media),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_manual_caption)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("schedule", schedule_command))
    application.add_handler(MessageHandler(filters.Regex(r'^\\text'), handle_text_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(conv_handler)

    print("Meme Mwitu Bot is running. Waiting for messages...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
