import asyncio
import os
import re
from pathlib import Path
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import CommandStart
import yt_dlp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get bot token from environment
BOT_TOKEN = os.getenv("BOT_TOKEN")
DOWNLOAD_PATH = Path("downloads")
DOWNLOAD_PATH.mkdir(exist_ok=True)

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# YouTube URL pattern
YT_PATTERN = re.compile(
    r'(https?://)?(www\.)?(youtube\.com/(shorts/|watch\?v=)|youtu\.be/)[^\s]+'
)

def get_ydl_opts(output_path: str) -> dict:
    """Get yt-dlp options for 720p download"""
    return {
        'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
        'merge_output_format': 'mp4',
    }

async def download_video(url: str, output_path: str) -> dict:
    """Download video using yt-dlp asynchronously"""
    loop = asyncio.get_event_loop()
    ydl_opts = get_ydl_opts(output_path)
    
    def _download():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return {
                'title': info.get('title', 'video'),
                'duration': info.get('duration', 0),
                'filepath': ydl.prepare_filename(info)
            }
    
    return await loop.run_in_executor(None, _download)

def cleanup_file(filepath: str):
    """Remove downloaded file"""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Cleaned up: {filepath}")
    except Exception as e:
        logger.error(f"Error cleaning up {filepath}: {e}")

@dp.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command"""
    await message.answer(
        "👋 Hello! I'm a YouTube Shorts downloader bot.\n\n"
        "Send me a YouTube Shorts link and I'll download it in 720p for you!\n\n"
        "Supported formats:\n"
        "• youtube.com/shorts/...\n"
        "• youtu.be/...\n"
        "• youtube.com/watch?v=..."
    )

@dp.message(F.text)
async def handle_message(message: Message):
    """Handle incoming messages with YouTube links"""
    text = message.text
    
    # Check if message contains a YouTube link
    if not YT_PATTERN.search(text):
        await message.answer("❌ Please send a valid YouTube link!")
        return
    
    # Extract URL
    url_match = YT_PATTERN.search(text)
    url = url_match.group(0)
    
    # Send initial "please wait" message
    status_msg = await message.answer("⏳ Downloading video, please wait...")
    
    try:
        # Generate unique filename
        timestamp = int(asyncio.get_event_loop().time())
        output_template = str(DOWNLOAD_PATH / f"{message.from_user.id}_{timestamp}.%(ext)s")
        
        # Download video
        video_info = await download_video(url, output_template)
        filepath = video_info['filepath']
        
        # Check file size (Telegram limit is 50MB for bots)
        file_size = os.path.getsize(filepath)
        if file_size > 50 * 1024 * 1024:  # 50MB
            await status_msg.edit_text(
                "❌ Video is too large (>50MB). Telegram doesn't allow sending files this big via bot."
            )
            cleanup_file(filepath)
            return
        
        # Update status
        await status_msg.edit_text("📤 Uploading video...")
        
        # Send video
        video_file = FSInputFile(filepath)
        await message.answer_video(
            video=video_file,
            caption=f"🎬 {video_info['title']}"
        )
        
        # Delete status message
        await status_msg.delete()
        
    except yt_dlp.utils.DownloadError as e:
        await status_msg.edit_text(f"❌ Download failed: Unable to download this video.")
        logger.error(f"Download error: {e}")
        
    except Exception as e:
        await status_msg.edit_text(f"❌ An error occurred. Please try again later.")
        logger.error(f"Unexpected error: {e}")
        
    finally:
        # Cleanup downloaded file
        if 'filepath' in locals():
            cleanup_file(filepath)

async def cleanup_old_files():
    """Periodic cleanup of old files (fallback)"""
    while True:
        try:
            await asyncio.sleep(3600)  # Run every hour
            for file in DOWNLOAD_PATH.glob("*"):
                # Remove files older than 1 hour
                if file.is_file() and (asyncio.get_event_loop().time() - file.stat().st_mtime) > 3600:
                    cleanup_file(str(file))
        except Exception as e:
            logger.error(f"Cleanup task error: {e}")

async def main():
    """Start the bot"""
    # Start cleanup task
    asyncio.create_task(cleanup_old_files())
    
    # Start polling
    logger.info("Bot started!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())