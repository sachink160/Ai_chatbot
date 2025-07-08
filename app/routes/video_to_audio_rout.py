from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from fastapi.responses import FileResponse, JSONResponse
from app.Agent import video_to_audio
from app.auth import get_current_user
import subprocess
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor

router = APIRouter(tags=["Video to Audio"])

# ThreadPoolExecutor for CPU-bound processing
executor = ThreadPoolExecutor()

@router.post("/video-to-audio/upload")
async def upload_video(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload a video file, process it (convert to 720p and extract audio),
    and store results in user-specific folders. Only authenticated users can upload.
    Video processing is offloaded to a thread to avoid blocking the event loop.
    """
    user_id = str(current_user.id)  # or current_user["id"] depending on your user model

    if not file.filename.lower().endswith((".mp4", ".mov", ".avi", ".mkv")):
        raise HTTPException(status_code=400, detail="Invalid file type.")

    try:
        # Save upload synchronously
        input_path = video_to_audio.save_upload(file, user_id)
        # Offload processing to a thread
        loop = asyncio.get_event_loop()
        output_video, output_audio = await loop.run_in_executor(
            executor,
            video_to_audio.process_video,
            input_path, user_id, file.filename
        )
    except subprocess.CalledProcessError as e:
        return JSONResponse(status_code=500, content={"error": f"Processing failed: {e}"})

    return {
        "video_url": f"/video-to-audio/download/{user_id}/{os.path.basename(output_video)}",
        "audio_url": f"/video-to-audio/download/{user_id}/{os.path.basename(output_audio)}"
    }

@router.get("/video-to-audio/uploads")
def list_uploaded_files(current_user: dict = Depends(get_current_user)):
    """
    List all uploaded files for the current user.
    """
    user_id = str(current_user.id)
    upload_dir = video_to_audio.get_user_dir(video_to_audio.BASE_UPLOAD_DIR, user_id)
    if not os.path.exists(upload_dir):
        return []
    return {"uploads": [f for f in os.listdir(upload_dir) if os.path.isfile(os.path.join(upload_dir, f))]}

@router.get("/video-to-audio/processed")
def list_processed_files(current_user: dict = Depends(get_current_user)):
    """
    List all processed files for the current user.
    """
    user_id = str(current_user.id)
    processed_dir = video_to_audio.get_user_dir(video_to_audio.BASE_PROCESSED_DIR, user_id)
    if not os.path.exists(processed_dir):
        return []
    return {"processed": [f for f in os.listdir(processed_dir) if os.path.isfile(os.path.join(processed_dir, f))]}

@router.get("/video-to-audio/download/{user_id}/{filename}")
def download_file(user_id: str, filename: str, current_user: dict = Depends(get_current_user)):
    """
    Download a processed file for a specific user. Only the owner can access their files.
    """
    if str(current_user.id) != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized.")
    file_path = video_to_audio.get_processed_file(user_id, filename)
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(file_path, filename=filename)
