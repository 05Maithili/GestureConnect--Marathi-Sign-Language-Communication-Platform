"""
Management command to generate sample/demonstration MP4 animation clips
for all vocabulary entries and fingerspelling signs.
Uses OpenCV and PIL to render smooth 3D humanoid avatar visualization clips.
"""

from pathlib import Path
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import cv2
from django.core.management.base import BaseCommand
from django.conf import settings
from translator.models import SignVocabulary


def create_avatar_sign_video(
    output_path: Path,
    marathi_text: str,
    english_text: str,
    sign_id: str,
    category: str,
    duration_sec: float = 2.0,
    fps: int = 24
):
    """
    Renders an MP4 animation clip depicting a 3D humanoid avatar signing pose
    with sign identification overlays and fluid motion keyframes.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    width, height = 640, 480
    total_frames = int(duration_sec * fps)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

    # Background gradient colors
    bg_top = np.array([24, 32, 54], dtype=float)     # Deep dark blue
    bg_bottom = np.array([12, 18, 30], dtype=float)  # Dark slate

    for f in range(total_frames):
        t = f / total_frames
        wave = math.sin(t * math.pi * 2)
        hand_lift = math.sin(t * math.pi)

        # 1. Base Gradient Canvas
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        for y in range(height):
            ratio = y / height
            color = (bg_top * (1 - ratio) + bg_bottom * ratio).astype(np.uint8)
            frame[y, :] = color

        # 2. Draw 3D Avatar Humanoid Wireframe / Stylized Silhouette
        center_x = width // 2
        head_y = 150 + int(wave * 4)
        chest_y = 230
        pelvis_y = 350

        # Head (Stylized 3D Avatar sphere)
        cv2.circle(frame, (center_x, head_y), 42, (60, 160, 240), -1, cv2.LINE_AA)
        cv2.circle(frame, (center_x, head_y), 44, (200, 225, 255), 2, cv2.LINE_AA)
        # Face visor / eye line
        cv2.ellipse(frame, (center_x, head_y - 4), (22, 10), 0, 0, 180, (20, 40, 80), -1, cv2.LINE_AA)

        # Torso
        cv2.line(frame, (center_x, head_y + 42), (center_x, pelvis_y), (80, 180, 255), 18, cv2.LINE_AA)

        # Shoulders
        shoulder_l = (center_x - 70, head_y + 65)
        shoulder_r = (center_x + 70, head_y + 65)
        cv2.line(frame, shoulder_l, shoulder_r, (120, 200, 255), 14, cv2.LINE_AA)

        # Left Arm & Hand (Animated signing pose)
        elbow_l = (center_x - 110, head_y + 120 - int(hand_lift * 30))
        hand_l = (center_x - 60 - int(wave * 20), head_y + 80 - int(hand_lift * 60))
        cv2.line(frame, shoulder_l, elbow_l, (70, 150, 230), 10, cv2.LINE_AA)
        cv2.line(frame, elbow_l, hand_l, (90, 180, 255), 8, cv2.LINE_AA)
        cv2.circle(frame, hand_l, 14, (240, 220, 160), -1, cv2.LINE_AA)

        # Right Arm & Hand (Animated signing pose)
        elbow_r = (center_x + 110, head_y + 120 - int(hand_lift * 40))
        hand_r = (center_x + 60 + int(wave * 25), head_y + 70 - int(hand_lift * 70))
        cv2.line(frame, shoulder_r, elbow_r, (70, 150, 230), 10, cv2.LINE_AA)
        cv2.line(frame, elbow_r, hand_r, (90, 180, 255), 8, cv2.LINE_AA)
        cv2.circle(frame, hand_r, 14, (240, 220, 160), -1, cv2.LINE_AA)

        # Avatar Platform / Ground grid glow
        cv2.ellipse(frame, (center_x, 430), (160, 30), 0, 0, 360, (0, 120, 220), 2, cv2.LINE_AA)
        cv2.ellipse(frame, (center_x, 430), (120, 20), 0, 0, 360, (0, 180, 255), 1, cv2.LINE_AA)

        # UI Banner Overlays (OpenCV native overlay text)
        cv2.rectangle(frame, (15, 15), (width - 15, 75), (10, 20, 40), -1)
        cv2.rectangle(frame, (15, 15), (width - 15, 75), (0, 115, 230), 2)

        # Text banner
        cv2.putText(
            frame,
            f"MSL 3D SIGN: {english_text.upper()}",
            (30, 45),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (255, 255, 255),
            2,
            cv2.LINE_AA
        )

        cv2.putText(
            frame,
            f"[{sign_id}] Category: {category.title()}",
            (30, 68),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 200, 255),
            1,
            cv2.LINE_AA
        )

        # Progress bar at bottom
        prog_w = int((width - 40) * t)
        cv2.rectangle(frame, (20, height - 20), (width - 20, height - 12), (30, 45, 70), -1)
        cv2.rectangle(frame, (20, height - 20), (20 + prog_w, height - 12), (0, 160, 255), -1)

        writer.write(frame)

    writer.release()


class Command(BaseCommand):
    help = "Generates placeholder 3D avatar MP4 animation clips for all signs and fingerspelling"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Generating sample 3D avatar sign animation assets..."))
        media_root = Path(settings.MEDIA_ROOT)
        
        vocab_entries = SignVocabulary.objects.all()
        count = 0

        for entry in vocab_entries:
            asset_rel = entry.animation_asset
            target_file = media_root / asset_rel
            
            if not target_file.exists():
                create_avatar_sign_video(
                    output_path=target_file,
                    marathi_text=entry.marathi_term,
                    english_text=entry.english_gloss,
                    sign_id=entry.sign_id,
                    category=entry.category,
                    duration_sec=2.0
                )
                count += 1

        # Also generate common fingerspelling placeholder assets
        from translator.services.fingerspelling import DEVANAGARI_FINGERSPELLING_MAP, ENGLISH_FINGERSPELLING_MAP
        
        fs_dir = media_root / 'animations' / 'fingerspelling'
        fs_dir.mkdir(parents=True, exist_ok=True)

        for ch, sign_id in list(DEVANAGARI_FINGERSPELLING_MAP.items())[:20]:
            clean_id = sign_id.lower().replace('sign_fs_mr_', '')
            fs_path = fs_dir / f"mr_{clean_id}.mp4"
            if not fs_path.exists():
                create_avatar_sign_video(
                    output_path=fs_path,
                    marathi_text=ch,
                    english_text=f"Letter {ch}",
                    sign_id=sign_id,
                    category="fingerspelling",
                    duration_sec=1.5
                )
                count += 1

        for char, sign_id in list(ENGLISH_FINGERSPELLING_MAP.items())[:26]:
            fs_path = fs_dir / f"en_{char.lower()}.mp4"
            if not fs_path.exists():
                create_avatar_sign_video(
                    output_path=fs_path,
                    marathi_text=char,
                    english_text=f"Letter {char}",
                    sign_id=sign_id,
                    category="fingerspelling",
                    duration_sec=1.5
                )
                count += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully generated {count} sample animation MP4 assets in {media_root}"))
