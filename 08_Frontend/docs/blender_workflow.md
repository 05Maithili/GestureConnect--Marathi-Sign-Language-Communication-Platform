# Blender 3D Animation Asset Authoring & Integration Workflow

This document outlines the standard procedure for creating, rendering, and integrating 3D sign language animation assets into **GestureConnect**.

---

## 1. Avatar Model Guidelines
1. **Base Mesh:** Use a standardized humanoid 3D avatar with a full arm, neck, torso, and 5-finger hand armature.
2. **Rest Pose:** Neutral T-pose or relaxed A-pose with palms facing downwards.
3. **Rigging:** Ensure bone naming follows standard convention:
   - `Hand.L`, `Thumb01.L`..`Thumb03.L`, `Index01.L`..`Index03.L`, etc.
   - `Hand.R`, `Thumb01.R`..`Thumb03.R`, `Index01.R`..`Index03.R`, etc.
   - `UpperArm`, `Forearm`, `Shoulder`, `Head`, `Spine`.

---

## 2. Animation Authoring in Blender
1. Set scene frame rate to **24 FPS** or **30 FPS**.
2. Animate the specific sign using official Marathi Sign Language (MSL) reference dictionaries.
3. Keep the initial frame (Frame 1) and final frame (Frame N) in neutral resting transition posture to ensure seamless sequential concatenation between consecutive sign clips.
4. Typical duration for single lexical signs is **1.5 to 2.5 seconds** (36 to 60 frames).

---

## 3. Rendering & Video Export
1. **Resolution:** 640x480 or 1280x720 (16:9).
2. **File Format:** FFmpeg Video.
3. **Container:** MP4 / MPEG-4.
4. **Video Codec:** H.264 / AVC (High Profile).
5. **Background:** Studio gradient or neutral dark backdrop (#0d1527).
6. **Pixel Format:** `yuv420p` for maximum web browser compatibility.

---

## 4. Directory Placement
Store rendered MP4 video files inside `media/animations/` grouped by category:

```
media/animations/
├── greetings/
│   ├── hello.mp4
│   ├── thank_you.mp4
│   └── welcome.mp4
├── family/
│   ├── mother.mp4
│   ├── father.mp4
│   └── brother.mp4
├── pronouns/
│   ├── me.mp4
│   └── you.mp4
├── numbers/
│   ├── one.mp4
│   └── two.mp4
├── verbs/
│   ├── want.mp4
│   ├── eat.mp4
│   └── drink.mp4
├── objects/
│   ├── water.mp4
│   └── house.mp4
├── questions/
│   ├── what.mp4
│   └── where.mp4
├── time/
│   ├── today.mp4
│   └── tomorrow.mp4
└── fingerspelling/
    ├── mr_ka.mp4
    ├── mr_la.mp4
    └── en_a.mp4
```

---

## 5. Registering the Sign in GestureConnect
You can register new signs either through the Django Admin Panel or by adding entries to `data/vocabulary.json`:

### Via Django Admin Panel:
1. Navigate to `/admin/translator/signvocabulary/add/`.
2. Enter:
   - **Canonical Sign ID:** `SIGN_<ENGLISH_NAME>` (e.g., `SIGN_DOCTOR`)
   - **Marathi Term:** Primary Devanagari word (e.g., `डॉक्टर`)
   - **English Gloss:** `doctor`
   - **Category:** `objects`
   - **Sign Type:** `lexical`
   - **Animation Asset:** `animations/objects/doctor.mp4`
   - **Synonyms:** `["वैद्य", "चिकित्सक"]`
   - **Metadata:** Biomechanical details (hand shape, motion description).
3. Save the entry. The translation engine will immediately begin resolving and playing the asset.
