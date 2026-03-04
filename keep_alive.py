from flask import Flask
from threading import Thread
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Meme Mwitu Bot is fully online and polling Telegram! 🚀\nEverything is running smoothly."

def run():
    # Render automatically provisions a PORT environment variable.
    # We bind the Flask server to this port so Render thinks the Web Service is healthy.
    port = int(os.environ.get('PORT', 8080))
    # We run the flask app without debug mode inside the background thread.
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    """
    Spawns a background thread to run the Flask web server.
    This prevents the main Telegram polling loop from being blocked,
    while fulfilling Render's Web Service requirements.
    """
    server_thread = Thread(target=run)
    server_thread.start()
