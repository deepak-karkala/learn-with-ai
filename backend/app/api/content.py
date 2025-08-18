from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
from pathlib import Path

router = APIRouter()

# Get the content directory path relative to the backend
CONTENT_DIR = Path(__file__).parent.parent.parent.parent / "content"

@router.get("/content/{module_id}/tutorial.md")
async def get_tutorial_content(module_id: str):
    """Get tutorial markdown content for a specific module"""
    try:
        file_path = CONTENT_DIR / module_id / "tutorial.md"
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"Tutorial content not found for module: {module_id}")
        
        # Read the file content
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        return {"content": content, "module_id": module_id}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading tutorial content: {str(e)}")

@router.get("/content/{module_id}/video")
async def get_video_content(module_id: str):
    """Get video content for a specific module"""
    try:
        # Look for common video file extensions
        video_extensions = ['.mp4', '.webm', '.mov', '.avi']
        
        for ext in video_extensions:
            file_path = CONTENT_DIR / module_id / f"video{ext}"
            if file_path.exists():
                return FileResponse(
                    path=str(file_path),
                    media_type="video/mp4",
                    filename=f"{module_id}_video{ext}"
                )
        
        raise HTTPException(status_code=404, detail=f"Video content not found for module: {module_id}")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error accessing video content: {str(e)}")

@router.get("/content/{module_id}/audio")
async def get_audio_content(module_id: str):
    """Get audio content for a specific module"""
    try:
        # Look for common audio file extensions
        audio_extensions = ['.mp3', '.wav', '.ogg', '.m4a']
        
        for ext in audio_extensions:
            file_path = CONTENT_DIR / module_id / f"audio{ext}"
            if file_path.exists():
                return FileResponse(
                    path=str(file_path),
                    media_type="audio/mpeg",
                    filename=f"{module_id}_audio{ext}"
                )
        
        raise HTTPException(status_code=404, detail=f"Audio content not found for module: {module_id}")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error accessing audio content: {str(e)}")

@router.get("/content/modules")
async def list_available_modules():
    """List all available learning modules"""
    try:
        modules = []
        
        if CONTENT_DIR.exists():
            for item in CONTENT_DIR.iterdir():
                if item.is_dir():
                    module_info = {
                        "id": item.name,
                        "title": item.name.replace('_', ' ').title(),
                        "has_tutorial": (item / "tutorial.md").exists(),
                        "has_video": any((item / f"video{ext}").exists() for ext in ['.mp4', '.webm', '.mov', '.avi']),
                        "has_audio": any((item / f"audio{ext}").exists() for ext in ['.mp3', '.wav', '.ogg', '.m4a'])
                    }
                    modules.append(module_info)
        
        return {"modules": modules}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing modules: {str(e)}")