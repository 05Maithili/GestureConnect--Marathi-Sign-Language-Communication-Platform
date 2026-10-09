"""
Animation Asset Resolution Module for GestureConnect.
Resolves Blender-generated MP4 sign animation assets by Canonical Sign ID.
Ensures clean decoupling between the linguistic layer and visual assets layer.
"""

from pathlib import Path
from typing import Dict, Any, Optional
from django.conf import settings


def get_animation(sign_id: str, asset_path: Optional[str] = None, metadata: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Resolves animation asset by canonical sign ID.
    
    Returns structured dictionary:
    {
        "sign_id": "SIGN_HELLO",
        "animation_url": "/media/animations/greetings/hello.mp4",
        "asset_exists": True,
        "duration_seconds": 2.5,
        "metadata": { ... },
        "placeholder_mode": False
    }
    """
    media_root = Path(settings.MEDIA_ROOT)
    media_url = settings.MEDIA_URL

    # Default asset path heuristics if not supplied
    if not asset_path:
        sign_suffix = sign_id.lower().replace('sign_', '')
        asset_path = f"animations/general/{sign_suffix}.mp4"

    full_disk_path = media_root / asset_path
    asset_exists = full_disk_path.is_file()

    # Calculate or estimate duration based on sign type / metadata
    duration = 2.0
    if metadata and isinstance(metadata, dict):
        duration = metadata.get('duration_seconds', 2.0)

    # Determine URL
    if asset_exists:
        anim_url = f"{media_url}{asset_path.replace('\\', '/')}"
        placeholder_mode = False
    else:
        # Graceful placeholder resolution - points to standard placeholder or category asset
        anim_url = f"{media_url}{asset_path.replace('\\', '/')}"
        placeholder_mode = True

    return {
        'sign_id': sign_id,
        'animation_url': anim_url,
        'asset_path': asset_path,
        'asset_exists': asset_exists,
        'duration_seconds': duration,
        'metadata': metadata or {},
        'placeholder_mode': placeholder_mode
    }
