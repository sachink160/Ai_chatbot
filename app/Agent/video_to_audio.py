import os
import shutil
import subprocess
import sys
import imageio_ffmpeg

# Use imageio-ffmpeg to get the ffmpeg executable path
ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

BASE_UPLOAD_DIR = os.path.join(os.getcwd(), 'uploads')
BASE_PROCESSED_DIR = os.path.join(os.getcwd(), 'processed')
os.makedirs(BASE_UPLOAD_DIR, exist_ok=True)
os.makedirs(BASE_PROCESSED_DIR, exist_ok=True)

def get_user_dir(base_dir: str, user_id: str) -> str:
    """
    Returns the user-specific directory path, creating it if it doesn't exist.
    """
    user_dir = os.path.join(base_dir, f"user_{user_id}")
    os.makedirs(user_dir, exist_ok=True)
    return user_dir

def save_upload(file, user_id: str):
    """
    Saves the uploaded file to the user's upload directory.
    Returns the full path to the saved file.
    """
    upload_dir = get_user_dir(BASE_UPLOAD_DIR, user_id)
    input_path = os.path.join(upload_dir, file.filename)
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return input_path

def process_video(input_path: str, user_id: str, filename: str):
    """
    Processes the uploaded video: creates a 720p version and extracts audio as mp3.
    Returns paths to the processed video and audio files.
    """
    processed_dir = get_user_dir(BASE_PROCESSED_DIR, user_id)
    base = os.path.splitext(filename)[0]
    output_video = os.path.join(processed_dir, f"{base}_720p.mp4")
    output_audio = os.path.join(processed_dir, f"{base}_audio.mp3")

    subprocess.run([
        ffmpeg_path, '-i', input_path, '-t', '10', '-vf', 'scale=1280:720', output_video
    ], check=True)
    subprocess.run([
        ffmpeg_path, '-i', input_path, '-q:a', '0', '-map', 'a', output_audio
    ], check=True)
    return output_video, output_audio

def get_processed_file(user_id: str, filename: str):
    """
    Returns the path to a processed file for a user, or None if it doesn't exist.
    """
    file_path = os.path.join(BASE_PROCESSED_DIR, f"user_{user_id}", filename)
    if not os.path.exists(file_path):
        return None
    return file_path



