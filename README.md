# GestureConnect 🤟

> **Bilingual Speech and Text to Marathi Sign Language Translation System**

GestureConnect is an assistive communication web platform designed to bridge communication gaps for the deaf and hard-of-hearing community. The system accepts **Marathi text**, **English text**, and **Marathi speech**, and translates the input into Marathi Sign Language (MSL).

---

## 1. Project Overview
GestureConnect implements a linguistic-to-visual translation architecture where linguistic rules, tokenization, and canonical sign mappings remain decoupled from visual rendering resources. Individual sign video clips are sequenced and played smoothly on a web video player to present continuous, sentence-level Marathi Sign Language output.

## 2. Actual Directory Structure
```
GestureConnect/
│
├── 02_INCLUDE_Dataset_Optimized/  # (Ignored) Original heavy ~13.2GB raw videos (.mov/.mp4)
├── 02_INCLUDE_Dataset_Web/        # Browser-compatible MP4 dataset for web streaming (~627MB)
├── 03_MediaPipe_Landmarks/        # Extracted hand/pose landmarks data
├── 04_Multilingual_Dictionary/    # Core mappings and JSON dictionaries
├── 05_AI_Model/                   # Future AI translation logic
├── 06_3D_Avatar/                  # Phase 2: Blender Avatar assets
├── 07_Backend/                    # Assorted backend utilities
├── 08_Frontend/                   # **Main Django Web Application**
│   ├── gestureconnect/            # Django settings & wsgi routing
│   ├── translator/                # Core translation views & services
│   ├── frontend/                  # HTML templates, CSS, JS
│   └── manage.py                  # Django entry point
├── Scripts/                       # Data processing & pipeline scripts
├── requirements.txt               # Unified project dependencies
└── README.md                      # This file
```

## 3. Python Version Requirements
This project strictly requires **Python 3.10, 3.11, or 3.12**.
*(Note: Ensure you have `pip` installed and configured in your system path).*

## 4. Virtual Environment Setup
It is highly recommended to isolate the project dependencies using a Python virtual environment:
```bash
# Create a virtual environment
python -m venv .venv

# Activate the virtual environment (Windows)
.venv\Scripts\activate

# Activate (macOS/Linux)
source .venv/bin/activate
```

## 5. Dependency Installation
Once the virtual environment is activated, install the required packages:
```bash
pip install -r requirements.txt
```

## 6. Django Configuration & Environment Variables
The application relies on environment variables for safe configuration.
1. Navigate to the frontend directory: `cd 08_Frontend`
2. Copy the example configuration:
   `copy .env.example .env` (Windows) or `cp .env.example .env` (Linux/Mac)
3. The `.env` file handles database config, DEBUG flags, and the SECRET_KEY.

## 7. Database Migrations
Initialize your database (SQLite by default):
```bash
cd 08_Frontend
python manage.py makemigrations
python manage.py migrate
```

## 8. Local Server Startup
To start the Django development server:
```bash
cd 08_Frontend
python manage.py runserver
```
Navigate to `http://127.0.0.1:8000/` in your browser.

## 9. Dataset Differences (Optimized vs Web-Video)
* **`02_INCLUDE_Dataset_Optimized`**: Contains the full raw original dataset weighing over 13.2 GB. It includes uncompressed formats like `.MOV`. This is solely used for offline AI model training and landmark extraction, and is never directly served to the web browser.
* **`02_INCLUDE_Dataset_Web`**: Contains precisely curated, compressed, H.264 `.mp4` format videos optimized for instantaneous web playback via HTTP 206 Partial Content streams. The Django application strictly reads from this web-dataset.

## 10. Configuring External Sign-Video Directory
To keep the massive video files decoupled from the codebase, the Django application resolves paths dynamically.
By default, it looks for `02_INCLUDE_Dataset_Web` and `04_Multilingual_Dictionary` relative to the project root.
If you host the dataset externally, define them in your `.env`:
```env
GESTURECONNECT_VIDEO_ROOT=/path/to/your/external/dataset
GESTURECONNECT_DICT_ROOT=/path/to/your/external/dictionary
```
If the external dataset path is completely missing, the app gracefully marks signs as `Video unavailable` instead of crashing.

## 11. Files Intentionally Excluded from Git
To keep the GitHub repository fast and clean, the following are strictly excluded via `.gitignore`:
* **All Virtual Environments** (`venv_mp`, `.venv`, etc.)
* **The 13.2 GB Optimized Dataset** (`02_INCLUDE_Dataset_Optimized/`)
* **Colab Training ZIPs** (`GestureConnect_Colab_Training_Data.zip`)
* **Local Databases & Secrets** (`db.sqlite3`, `.env`)
* **Temporary Cache** (`__pycache__`, `*.pyc`)

## 12. Current Deployment Blockers & Planned Resolution
Currently, this project runs flawlessly in local development. However, for a production deployment, the following issues are known and planned for resolution:
* **Missing WSGI Server**: A production server like `Gunicorn` or `uWSGI` must be added and configured.
* **Database Scaling**: The `db.sqlite3` must be swapped for PostgreSQL or MySQL via the `DB_ENGINE` env variables.
* **Static Asset Hosting**: We plan to implement `WhiteNoise` or configure NGINX to properly serve static files in production.
* **Video Asset Hosting (Large Files)**: The 627MB web-dataset requires external blob storage (like AWS S3) or Git LFS, as ordinary Git hosting cannot handle it gracefully.
