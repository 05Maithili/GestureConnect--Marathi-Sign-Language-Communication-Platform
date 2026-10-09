#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
INCLUDE ISL Dataset Optimization Pipeline  v2.0 (Final)
============================================================
Final Year Project -- Translation Studio (ISL/MSL)

SOURCE  : F:\\Final_Year_Project\\01_INCLUDE_Dataset_Original\\<Category>\\<Word>\\video.mov
OUTPUT  : F:\\Final_Year_Project\\02_INCLUDE_Dataset_Optimized\\<Word>\\video.mov
          ^^^  NO category layer in output  ^^^

USAGE:
  Step 1 (always first):   python optimize_include_dataset.py --dry-run
  Step 2 (after review):   python optimize_include_dataset.py --run
  Inspect only:            python optimize_include_dataset.py --inspect-only

SAFETY GUARANTEES:
  - Original dataset is NEVER modified, moved, renamed, or deleted.
  - All reads from source are 100% read-only filesystem operations.
  - Files are COPIED ONLY (shutil.copy2) -- no moves, no deletes.
  - Duplicate word names across categories are detected and SKIPPED.
  - No destination file is EVER overwritten.
  - A 5-second abort window exists before any live copy begins.
  - No cleanup/deletion logic exists anywhere in this script.
============================================================
"""

import os
import sys
import csv
import copy
import json
import time
import shutil
import logging
import argparse
import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple

# ── OpenCV (optional but strongly recommended) ─────────────────────────────────
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

# ==============================================================================
#  CONFIGURATION
#  Edit only these values if you need to override paths or thresholds.
# ==============================================================================
CONFIG = {
    # ── Dataset paths ──────────────────────────────────────────────────────────
    "ORIGINAL_DATASET_ROOT":  r"F:\Final_Year_Project\01_INCLUDE_Dataset_Original",
    "OPTIMIZED_DATASET_ROOT": r"F:\Final_Year_Project\02_INCLUDE_Dataset_Optimized",
    "LOGS_DIR":               r"F:\Final_Year_Project\Scripts\Logs",

    # ── Video selection ────────────────────────────────────────────────────────
    "MIN_VIDEOS_PER_WORD":    3,   # Warn if fewer valid videos exist for a word
    "TARGET_VIDEOS_PER_WORD": 4,   # Prefer selecting this many per word

    # ── Accepted video file extensions ────────────────────────────────────────
    "VIDEO_EXTENSIONS": {
        ".mp4", ".mov", ".avi", ".mkv",
        ".MP4", ".MOV", ".AVI", ".MKV",
    },

    # ── OpenCV validation thresholds ──────────────────────────────────────────
    "MIN_FRAME_COUNT":  10,    # Reject videos with fewer frames than this
    "MIN_FPS":           5.0,  # Reject videos with FPS below this
    "MIN_DURATION_SEC":  0.5,  # Reject videos shorter than this (seconds)
    "MAX_DURATION_SEC": 30.0,  # Warn on very long videos

    # ── Report filenames ───────────────────────────────────────────────────────
    # On --dry-run  : written to LOGS_DIR
    # On --run      : written to OPTIMIZED_DATASET_ROOT  (the 02_INCLUDE_Dataset_Optimized folder)
    "METADATA_FILENAME": "dataset_metadata.csv",
    "SUMMARY_FILENAME":  "optimization_summary.json",
}

# ==============================================================================
#  LOGGING
# ==============================================================================
def setup_logging(logs_dir: str, dry_run: bool) -> logging.Logger:
    Path(logs_dir).mkdir(parents=True, exist_ok=True)
    ts     = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = "DRY_RUN" if dry_run else "LIVE_RUN"
    log_file = os.path.join(logs_dir, f"{prefix}_{ts}.log")

    logger = logging.getLogger("IncludeOptimizer")
    logger.setLevel(logging.DEBUG)

    # Console: INFO and above — readable summary
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("%(levelname)-8s  %(message)s"))
    logger.addHandler(ch)

    # File: DEBUG and above — full detail
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    logger.addHandler(fh)

    logger.info(f"Full log  : {log_file}")
    return logger


def _section(logger: logging.Logger, title: str) -> None:
    logger.info("")
    logger.info("=" * 68)
    logger.info(f"  {title}")
    logger.info("=" * 68)

# ==============================================================================
#  SAFETY GATE — must pass before any other operation
# ==============================================================================
def safety_check(source: str, dest: str, logger: logging.Logger) -> None:
    """
    Hard abort if source and destination paths overlap in any direction.
    Prevents accidental writes into the original dataset folder.
    """
    try:
        src_r  = str(Path(source).resolve()).lower().rstrip(os.sep)
        dest_r = str(Path(dest).resolve()).lower().rstrip(os.sep)
    except Exception:
        # Path may not exist yet (dest) -- compare raw strings
        src_r  = source.lower().rstrip(os.sep).rstrip("\\").rstrip("/")
        dest_r = dest.lower().rstrip(os.sep).rstrip("\\").rstrip("/")

    if dest_r == src_r:
        logger.critical("SAFETY ABORT: Source and destination are the same path!")
        sys.exit(2)

    if dest_r.startswith(src_r + os.sep) or dest_r.startswith(src_r + "\\"):
        logger.critical(
            "SAFETY ABORT: Destination is inside the source directory!\n"
            f"  Source : {source}\n"
            f"  Dest   : {dest}"
        )
        sys.exit(2)

    if os.path.exists(dest) and (
        src_r.startswith(dest_r + os.sep) or src_r.startswith(dest_r + "\\")
    ):
        logger.critical(
            "SAFETY ABORT: Source is inside the destination directory!\n"
            f"  Source : {source}\n"
            f"  Dest   : {dest}"
        )
        sys.exit(2)

    logger.info(f"  Safety check   : PASSED")
    logger.info(f"  Source         : {source}")
    logger.info(f"  Destination    : {dest}")
    logger.info("")

# ==============================================================================
#  PHASE 1 — STRUCTURE INSPECTION  (100% read-only)
# ==============================================================================
def inspect_dataset(
    root: str, logger: logging.Logger
) -> Dict[str, Dict[str, List[str]]]:
    """
    Walk source directory and build catalogue:
        { category: { word: [absolute_video_path, ...] } }

    SAFETY: This function only calls os.listdir(), os.path.isdir(),
    os.path.isfile(), and os.path.splitext(). Nothing is written,
    moved, renamed, or deleted.
    """
    _section(logger, "PHASE 1 — STRUCTURE INSPECTION (read-only)")
    logger.info(f"  Source : {root}")
    logger.info("")

    if not os.path.exists(root):
        logger.critical(f"  FATAL: Source path does not exist: {root}")
        sys.exit(1)

    catalogue: Dict[str, Dict[str, List[str]]] = {}
    vext = CONFIG["VIDEO_EXTENSIONS"]

    for category in sorted(os.listdir(root)):
        cat_path = os.path.join(root, category)
        if not os.path.isdir(cat_path):
            continue

        catalogue[category] = {}

        for word in sorted(os.listdir(cat_path)):
            word_path = os.path.join(cat_path, word)
            if not os.path.isdir(word_path):
                continue

            videos = sorted([
                os.path.join(word_path, f)
                for f in os.listdir(word_path)
                if os.path.splitext(f)[1] in vext
                and os.path.isfile(os.path.join(word_path, f))
            ])
            catalogue[category][word] = videos

    total_cats  = len(catalogue)
    total_words = sum(len(w) for w in catalogue.values())
    total_vids  = sum(
        len(v) for w in catalogue.values() for v in w.values()
    )

    logger.info(f"  Categories found  : {total_cats}")
    logger.info(f"  Words found       : {total_words}")
    logger.info(f"  Video files found : {total_vids}")
    logger.info("")

    for cat, words in catalogue.items():
        wc = len(words)
        vc = sum(len(v) for v in words.values())
        logger.info(f"  [{cat}]  {wc} words  |  {vc} videos")
        for word, vids in words.items():
            logger.debug(f"      {word}: {len(vids)} video(s)")

    logger.info("")
    return catalogue

# ==============================================================================
#  PHASE 2 — DUPLICATE WORD DETECTION
# ==============================================================================
def detect_duplicates(
    catalogue: Dict[str, Dict[str, List[str]]],
    logger: logging.Logger,
) -> Tuple[Set[str], Dict[str, List[str]]]:
    """
    Find every word name that appears in more than one category.
    Duplicate words are EXCLUDED from the optimized dataset because
    flattening Category/Word -> Word creates an ambiguous merge.

    Returns:
        duplicate_words : set of ambiguous word names
        word_to_cats    : { word: [cat1, cat2, ...] }  for ALL words
    """
    _section(logger, "PHASE 2 — DUPLICATE WORD DETECTION")

    word_to_cats: Dict[str, List[str]] = {}
    for cat, words in catalogue.items():
        for word in words:
            word_to_cats.setdefault(word, []).append(cat)

    duplicate_words: Set[str] = {
        word for word, cats in word_to_cats.items() if len(cats) > 1
    }

    if not duplicate_words:
        logger.info("  No duplicate word names detected across categories.")
        logger.info("  All words are unique -- safe to flatten to Word/Video.")
    else:
        logger.warning(f"  {len(duplicate_words)} DUPLICATE WORD NAME(S) DETECTED:")
        logger.warning("")
        for word in sorted(duplicate_words):
            cats = word_to_cats[word]
            logger.warning(f"  DUPLICATE WORD DETECTED : {word!r}")
            logger.warning(f"    Categories            : {', '.join(cats)}")
            logger.warning(f"    Action                : SKIPPED until resolved")
            logger.warning("")
        logger.warning(
            "  Duplicate words are EXCLUDED from the optimized dataset.\n"
            "  To resolve: rename one category's word folder, then re-run."
        )

    logger.info("")
    return duplicate_words, word_to_cats

# ==============================================================================
#  PHASE 3 — VIDEO VALIDATION  (OpenCV)
# ==============================================================================
def _probe_video(path: str) -> Tuple[bool, str, dict]:
    """
    Open a video with OpenCV and verify basic quality metrics.
    Returns (is_valid, reason, stats_dict).
    """
    if not CV2_AVAILABLE:
        return True, "opencv_skipped", {}

    try:
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            cap.release()
            return False, "cannot_open", {}

        fps    = cap.get(cv2.CAP_PROP_FPS)         or 0.0
        frames = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0
        w      = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h      = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()

        duration = (frames / fps) if fps > 0 else 0.0
        stats = {
            "fps":      round(fps, 2),
            "frames":   int(frames),
            "width":    w,
            "height":   h,
            "duration": round(duration, 2),
        }

        if frames < CONFIG["MIN_FRAME_COUNT"]:
            return False, f"too_few_frames({int(frames)})", stats
        if fps < CONFIG["MIN_FPS"]:
            return False, f"fps_too_low({fps:.1f})", stats
        if duration < CONFIG["MIN_DURATION_SEC"]:
            return False, f"too_short({duration:.2f}s)", stats

        return True, "ok", stats

    except Exception as exc:
        return False, f"exception:{exc}", {}


def validate_catalogue(
    catalogue: Dict[str, Dict[str, List[str]]],
    duplicate_words: Set[str],
    logger: logging.Logger,
) -> Tuple[Dict[str, Dict[str, List[str]]], List[dict]]:
    """
    Validate every video using OpenCV.
    Duplicate words are skipped (they will not be copied regardless).

    Returns:
        validated : same structure as catalogue, only valid videos kept
        vlog      : per-video validation records (written to metadata CSV)
    """
    _section(logger, "PHASE 3 — VIDEO VALIDATION (OpenCV)")

    if not CV2_AVAILABLE:
        logger.warning("  opencv-python is NOT installed.")
        logger.warning("  All found videos will be treated as VALID (unverified).")
        logger.warning("  Install with:  pip install opencv-python")
        logger.info("")
        # Pass-through: mark duplicates empty, keep everything else
        validated = {
            cat: {
                word: ([] if word in duplicate_words else list(vids))
                for word, vids in words.items()
            }
            for cat, words in catalogue.items()
        }
        return validated, []

    validated: Dict[str, Dict[str, List[str]]] = {}
    vlog: List[dict] = []
    chk = ok_count = bad_count = warn_count = 0

    for cat, words in catalogue.items():
        validated[cat] = {}
        for word, videos in words.items():
            # Duplicate words will be skipped in selection; no need to validate
            if word in duplicate_words:
                validated[cat][word] = []
                continue

            valid_vids: List[str] = []
            for vpath in videos:
                chk += 1
                is_valid, reason, stats = _probe_video(vpath)
                long_video = (
                    stats.get("duration", 0) > CONFIG["MAX_DURATION_SEC"]
                    if stats else False
                )

                vlog.append({
                    "category":        cat,
                    "word":            word,
                    "filename":        os.path.basename(vpath),
                    "full_path":       vpath,
                    "is_valid":        is_valid,
                    "reject_reason":   "" if is_valid else reason,
                    "fps":             stats.get("fps", ""),
                    "frames":          stats.get("frames", ""),
                    "width":           stats.get("width", ""),
                    "height":          stats.get("height", ""),
                    "duration_sec":    stats.get("duration", ""),
                    "long_video_warn": long_video,
                })

                if is_valid:
                    valid_vids.append(vpath)
                    ok_count += 1
                    if long_video:
                        warn_count += 1
                        logger.warning(
                            f"  LONG VIDEO  {cat}/{word}/"
                            f"{os.path.basename(vpath)}"
                            f"  ({stats.get('duration', 0):.1f}s)"
                        )
                else:
                    bad_count += 1
                    logger.debug(
                        f"  REJECTED  {cat}/{word}/"
                        f"{os.path.basename(vpath)}  reason={reason}"
                    )

            validated[cat][word] = valid_vids

    logger.info(f"  Videos checked          : {chk}")
    logger.info(f"  Valid                   : {ok_count}")
    logger.info(f"  Rejected (corrupted)    : {bad_count}")
    logger.info(
        f"  Warnings (> {CONFIG['MAX_DURATION_SEC']}s duration)  : {warn_count}"
    )
    logger.info("")
    return validated, vlog

# ==============================================================================
#  PHASE 4 — DETERMINISTIC VIDEO SELECTION
# ==============================================================================
def _deterministic_select(videos: List[str], n: int) -> List[str]:
    """
    Select exactly `n` items from a sorted list using uniform-spread indexing.
    Fully deterministic — no randomness, always reproducible.
    """
    if len(videos) <= n:
        return videos[:]
    indices = [
        int(round(i * (len(videos) - 1) / (n - 1)))
        for i in range(n)
    ]
    seen: Set[int] = set()
    result: List[str] = []
    for idx in indices:
        if idx not in seen:
            seen.add(idx)
            result.append(videos[idx])
    return result


def select_videos(
    validated: Dict[str, Dict[str, List[str]]],
    duplicate_words: Set[str],
    logger: logging.Logger,
) -> Tuple[Dict[str, List[str]], List[dict]]:
    """
    Select 3–4 representative videos per word.

    Rules:
      - 4 or more valid videos -> select 4  (deterministic uniform spread)
      - Exactly 3 valid videos -> select all 3
      - Fewer than 3 valid videos -> select what's available, flag as WARNING
      - Duplicate words -> SKIP entirely
      - No valid videos -> SKIP, flag as WARNING

    Output selection_map is intentionally FLAT:
        { word: [selected_video_paths] }
    There is NO category key — this enforces the flat output structure.
    """
    _section(logger, "PHASE 4 — REPRESENTATIVE VIDEO SELECTION")
    logger.info(
        f"  Strategy : uniform-spread deterministic selection, "
        f"target {CONFIG['TARGET_VIDEOS_PER_WORD']} videos/word"
    )
    logger.info(
        f"  Minimum  : {CONFIG['MIN_VIDEOS_PER_WORD']} valid videos/word "
        f"(below this is flagged as WARNING)"
    )
    logger.info("")

    # FLAT map: word -> [paths]  (no category)
    selection_map: Dict[str, List[str]] = {}
    slog: List[dict] = []

    words_4:    List[str] = []
    words_3:    List[str] = []
    words_lt3:  List[str] = []
    skipped_dup: List[str] = []
    skipped_empty: List[str] = []

    sel_total = 0

    for cat, words in validated.items():
        for word, valid_vids in words.items():

            # ── Duplicate: skip ───────────────────────────────────────────────
            if word in duplicate_words:
                skipped_dup.append(f"{word!r}  [found in: {cat}]")
                slog.append({
                    "category":        cat,
                    "word":            word,
                    "valid_available": len(valid_vids),
                    "selected_count":  0,
                    "status":          "skipped_duplicate",
                    "selected_files":  "",
                })
                continue

            count = len(valid_vids)

            # ── No valid videos: skip ─────────────────────────────────────────
            if count == 0:
                skipped_empty.append(f"{cat}/{word}")
                slog.append({
                    "category":        cat,
                    "word":            word,
                    "valid_available": 0,
                    "selected_count":  0,
                    "status":          "skipped_no_valid_videos",
                    "selected_files":  "",
                })
                continue

            # ── Determine target ──────────────────────────────────────────────
            target_n = CONFIG["TARGET_VIDEOS_PER_WORD"]

            if count < CONFIG["MIN_VIDEOS_PER_WORD"]:
                target_n = count
                status   = f"below_minimum_{count}_available"
                words_lt3.append(f"{cat}/{word}  ({count} video(s))")
                logger.warning(
                    f"  BELOW MIN  {cat}/{word}  "
                    f"-- only {count} valid video(s) available"
                )
            elif count == CONFIG["MIN_VIDEOS_PER_WORD"]:
                target_n = CONFIG["MIN_VIDEOS_PER_WORD"]   # select exactly 3
                status   = "selected_3"
                words_3.append(word)
            else:
                target_n = CONFIG["TARGET_VIDEOS_PER_WORD"]  # select 4
                status   = "selected_4"
                words_4.append(word)

            chosen = _deterministic_select(valid_vids, target_n)

            # Store in FLAT map (word only — no category)
            selection_map[word] = chosen
            sel_total += len(chosen)

            slog.append({
                "category":        cat,
                "word":            word,
                "valid_available": count,
                "selected_count":  len(chosen),
                "status":          status,
                "selected_files":  " | ".join(
                    os.path.basename(p) for p in chosen
                ),
            })

            logger.debug(
                f"  SELECT  {cat}/{word}  "
                f"{count} valid -> {len(chosen)} chosen"
            )

    # ── Console summary ───────────────────────────────────────────────────────
    logger.info(f"  Words with 4 videos selected : {len(words_4)}")
    logger.info(f"  Words with 3 videos selected : {len(words_3)}")
    logger.info(f"  Words below minimum (<3)     : {len(words_lt3)}")
    logger.info(f"  Words skipped (duplicate)    : {len(skipped_dup)}")
    logger.info(f"  Words skipped (no videos)    : {len(skipped_empty)}")
    logger.info(f"  Total videos selected        : {sel_total}")
    logger.info("")

    if words_lt3:
        logger.warning(
            f"  Words with fewer than {CONFIG['MIN_VIDEOS_PER_WORD']} valid videos:"
        )
        for entry in words_lt3:
            logger.warning(f"    {entry}")
        logger.info("")

    if skipped_dup:
        logger.warning("  Duplicate words SKIPPED (resolve manually to include):")
        for entry in skipped_dup:
            logger.warning(f"    {entry}")
        logger.info("")

    if skipped_empty:
        logger.warning("  Words with zero valid videos SKIPPED:")
        for entry in skipped_empty:
            logger.warning(f"    {entry}")
        logger.info("")

    return selection_map, slog

# ==============================================================================
#  PHASE 5 — DRY-RUN PLAN  (writes nothing to disk)
# ==============================================================================
def dry_run_report(
    selection_map: Dict[str, List[str]],
    word_to_cats:  Dict[str, List[str]],
    duplicate_words: Set[str],
    optimized_root: str,
    logger: logging.Logger,
) -> List[dict]:
    """
    Build the copy plan and print a readable summary.

    DESTINATION FORMAT:
        <optimized_root> / <WORD> / <filename>
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        NO category directory between optimized_root and WORD.

    Nothing is written to disk in this function.
    """
    _section(logger, "PHASE 5 — DRY-RUN PLAN (nothing is written)")

    plan: List[dict] = []
    total_bytes = 0
    collision_warnings: List[str] = []

    for word, chosen in sorted(selection_map.items()):
        for src in chosen:
            fname = os.path.basename(src)

            # ── CRITICAL: word/filename only — NO category sub-directory ──────
            dest = os.path.join(optimized_root, word, fname)
            # ─────────────────────────────────────────────────────────────────

            sz_bytes = os.path.getsize(src) if os.path.exists(src) else 0
            sz_mb    = sz_bytes / (1024 * 1024)
            total_bytes += sz_bytes

            # Check for pre-existing file at destination (collision detection)
            if os.path.exists(dest):
                collision_warnings.append(f"{dest}")

            plan.append({
                "word":     word,
                # category stored for CSV traceability ONLY; never used for path
                "category": word_to_cats.get(word, ["unknown"])[0],
                "src":      src,
                "dest":     dest,
                "size_mb":  round(sz_mb, 3),
            })

            logger.debug(
                f"  WOULD COPY  {word}/{fname}  ({sz_mb:.2f} MB)\n"
                f"             SRC  : {src}\n"
                f"             DEST : {dest}"
            )

    total_mb = total_bytes / (1024 * 1024)
    total_gb = total_mb / 1024

    logger.info(f"  Total files that would be copied  : {len(plan)}")
    logger.info(f"  Estimated size                    : {total_mb:.1f} MB  ({total_gb:.3f} GB)")
    logger.info(f"  Destination root                  : {optimized_root}")
    logger.info(f"  Destination structure             : <dest>/<WORD>/<video>")
    logger.info(f"  Category layer in output          : NONE (correctly omitted)")
    logger.info("")

    # Duplicate-word reminder in plan output
    if duplicate_words:
        logger.warning(
            f"  {len(duplicate_words)} word(s) excluded from plan due to duplicate names:"
        )
        for w in sorted(duplicate_words):
            cats = word_to_cats.get(w, [])
            logger.warning(f"    {w!r}  [categories: {', '.join(cats)}]")
        logger.info("")

    if collision_warnings:
        logger.warning(
            f"  {len(collision_warnings)} file(s) already exist at destination:"
        )
        for path in collision_warnings[:10]:  # cap console noise
            logger.warning(f"    {path}")
        if len(collision_warnings) > 10:
            logger.warning(f"    ... and {len(collision_warnings)-10} more (see log file)")
        logger.warning("  These will be SKIPPED during --run (no overwriting).")
        logger.info("")

    logger.info("  [OK] DRY-RUN COMPLETE -- no files were written.")
    logger.info("       Review the summary above, then run:")
    logger.info("       python optimize_include_dataset.py --run")
    logger.info("")
    return plan

# ==============================================================================
#  PHASE 6 — ACTUAL COPY  (only executed on --run)
# ==============================================================================
def execute_copy(plan: List[dict], logger: logging.Logger) -> List[dict]:
    """
    Copy each selected video to its flat destination.

    Directory creation:
        Creates <optimized_root>/<word>/  ONLY.
        Never creates <optimized_root>/<category>/  or any deeper nesting.

    File handling:
        - Skips if destination file already exists (no overwriting).
        - Uses shutil.copy2() which preserves file metadata.
        - Verifies file size after copy.

    Nothing is ever deleted from source or destination.
    """
    _section(logger, "PHASE 6 — EXECUTING COPY")

    results = copy.deepcopy(plan)
    ok_count = skip_count = fail_count = 0

    for i, item in enumerate(results, 1):
        src      = item["src"]
        dest     = item["dest"]
        dest_dir = os.path.dirname(dest)   # = <optimized_root>/<word>

        try:
            # Create the word-level directory only — never a category directory
            Path(dest_dir).mkdir(parents=True, exist_ok=True)

            if os.path.exists(dest):
                item["copy_status"] = "skipped_exists"
                skip_count += 1
                logger.debug(f"  SKIP (already exists) : {dest}")
                continue

            shutil.copy2(src, dest)  # copy2 preserves timestamps/metadata

            # Verify size after copy
            src_size  = os.path.getsize(src)
            dest_size = os.path.getsize(dest)

            if src_size != dest_size:
                item["copy_status"] = (
                    f"size_mismatch(src={src_size},dest={dest_size})"
                )
                fail_count += 1
                logger.error(
                    f"  SIZE MISMATCH  {item['word']}/"
                    f"{os.path.basename(dest)}"
                )
            else:
                item["copy_status"] = "ok"
                ok_count += 1
                logger.info(
                    f"  [{i:4d}/{len(results)}]  COPIED  "
                    f"{item['word']}/{os.path.basename(dest)}"
                    f"  ({item['size_mb']:.2f} MB)"
                )

        except Exception as exc:
            item["copy_status"] = f"error:{exc}"
            fail_count += 1
            logger.error(
                f"  FAILED  {item['word']}/{os.path.basename(src)}  |  {exc}"
            )

    logger.info("")
    logger.info(
        f"  Copy finished:  {ok_count} copied,  "
        f"{skip_count} skipped (exists),  {fail_count} failed"
    )
    logger.info("")
    return results

# ==============================================================================
#  PHASE 7 — REPORTS
# ==============================================================================
def write_metadata_csv(
    vlog:      List[dict],
    slog:      List[dict],
    plan:      List[dict],
    output_dir: str,
    logger:    logging.Logger,
) -> str:
    """
    Write dataset_metadata.csv.

    The 'category' column records the original source category for every video.
    This is for TRACEABILITY ONLY — it has ZERO effect on the output folder
    structure. The optimized dataset contains no category subdirectories.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    csv_path = os.path.join(output_dir, CONFIG["METADATA_FILENAME"])

    copy_lookup: Dict[Tuple, str] = {
        (i["word"], os.path.basename(i["src"])): i.get("copy_status", "dry_run_only")
        for i in plan
    }
    sel_set: Set[Tuple] = {
        (i["word"], os.path.basename(i["src"])) for i in plan
    }
    dest_lookup: Dict[Tuple, str] = {
        (i["word"], os.path.basename(i["src"])): i["dest"]
        for i in plan
    }

    fields = [
        "category",              # original source category (traceability only)
        "word",
        "filename",
        "is_valid",
        "reject_reason",
        "fps",
        "frames",
        "width",
        "height",
        "duration_sec",
        "long_video_warn",
        "selected_for_optimized",
        "copy_status",
        "optimized_dest_path",   # e.g. ...\02_INCLUDE_Dataset_Optimized\dog\video1.mov
    ]

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in vlog:
            key = (row["word"], row["filename"])
            writer.writerow({
                "category":               row["category"],
                "word":                   row["word"],
                "filename":               row["filename"],
                "is_valid":               row["is_valid"],
                "reject_reason":          row["reject_reason"],
                "fps":                    row["fps"],
                "frames":                 row["frames"],
                "width":                  row["width"],
                "height":                 row["height"],
                "duration_sec":           row["duration_sec"],
                "long_video_warn":        row["long_video_warn"],
                "selected_for_optimized": key in sel_set,
                "copy_status":            copy_lookup.get(key, "not_selected"),
                "optimized_dest_path":    dest_lookup.get(key, ""),
            })

    logger.info(f"  Metadata CSV    --> {csv_path}")
    return csv_path


def write_summary_json(
    catalogue:       Dict[str, Dict[str, List[str]]],
    validated:       Dict[str, Dict[str, List[str]]],
    selection_map:   Dict[str, List[str]],
    duplicate_words: Set[str],
    plan:            List[dict],
    dry_run:         bool,
    output_dir:      str,
    logger:          logging.Logger,
) -> str:
    """
    Write optimization_summary.json.

    On --dry-run : saved to F:\\Final_Year_Project\\Scripts\\Logs\\
    On --run     : saved to F:\\Final_Year_Project\\02_INCLUDE_Dataset_Optimized\\
                   (the actual optimized dataset root — NOT a new folder)
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    json_path = os.path.join(output_dir, CONFIG["SUMMARY_FILENAME"])

    total_original = sum(
        len(v) for w in catalogue.values() for v in w.values()
    )
    total_valid = sum(
        len(v) for w in validated.values() for v in w.values()
    )
    total_selected = sum(len(v) for v in selection_map.values())
    total_size_mb  = round(sum(i["size_mb"] for i in plan), 2)

    copy_ok   = sum(1 for i in plan if i.get("copy_status") == "ok")
    copy_skip = sum(1 for i in plan if i.get("copy_status") == "skipped_exists")
    copy_fail = sum(
        1 for i in plan
        if str(i.get("copy_status", "")).startswith(("error", "size_mismatch"))
    )

    words_4   = [w for w, v in selection_map.items() if len(v) == 4]
    words_3   = [w for w, v in selection_map.items() if len(v) == 3]
    words_lt3 = [w for w, v in selection_map.items() if 0 < len(v) < 3]

    summary = {
        "generated_at":    datetime.datetime.now().isoformat(),
        "script_version":  "2.0",
        "mode":            "dry_run" if dry_run else "live",
        "opencv_available": CV2_AVAILABLE,
        "paths": {
            "original_root":   CONFIG["ORIGINAL_DATASET_ROOT"],
            "optimized_root":  CONFIG["OPTIMIZED_DATASET_ROOT"],
            "logs_dir":        CONFIG["LOGS_DIR"],
        },
        "output_structure": "02_INCLUDE_Dataset_Optimized/<WORD>/<video>  (NO category layer)",
        "stats": {
            "categories":                  len(catalogue),
            "total_words_in_source":       sum(len(w) for w in catalogue.values()),
            "unique_words_in_output":      len(selection_map),
            "duplicate_words_excluded":    len(duplicate_words),
            "duplicate_word_names":        sorted(duplicate_words),
            "total_videos_original":       total_original,
            "total_videos_valid":          total_valid,
            "total_videos_selected":       total_selected,
            "words_with_4_videos":         len(words_4),
            "words_with_3_videos":         len(words_3),
            "words_below_minimum":         len(words_lt3),
            "words_below_minimum_list":    words_lt3,
            "estimated_size_mb":           total_size_mb,
        },
        "copy_results": (
            "dry_run_no_copy" if dry_run else {
                "ok":             copy_ok,
                "skipped_exists": copy_skip,
                "failed":         copy_fail,
                "total":          len(plan),
            }
        ),
        "selection_config": {
            "min_videos_per_word":    CONFIG["MIN_VIDEOS_PER_WORD"],
            "target_videos_per_word": CONFIG["TARGET_VIDEOS_PER_WORD"],
            "method":                 "deterministic_uniform_spread",
        },
        "per_category_breakdown": {
            cat: {
                "words":           len(catalogue[cat]),
                "original_videos": sum(len(v) for v in catalogue[cat].values()),
                "valid_videos":    sum(
                    len(v) for v in validated.get(cat, {}).values()
                ),
            }
            for cat in sorted(catalogue)
        },
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    logger.info(f"  Summary JSON    --> {json_path}")
    return json_path

# ==============================================================================
#  CLI ARGUMENT PARSER
# ==============================================================================
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="optimize_include_dataset.py",
        description=(
            "INCLUDE ISL Dataset Optimization Pipeline v2.0\n\n"
            "Output structure:\n"
            "  F:\\02_INCLUDE_Dataset_Optimized\\\n"
            "    <WORD>\\\n"
            "      video1.mov\n"
            "      video2.mov\n"
            "      ...\n\n"
            "Original dataset is NEVER modified.\n\n"
            "Step 1:  python optimize_include_dataset.py --dry-run\n"
            "Step 2:  python optimize_include_dataset.py --run"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument(
        "--dry-run", action="store_true",
        help="Inspect, validate, detect duplicates, plan -- write NOTHING",
    )
    g.add_argument(
        "--run", action="store_true",
        help="Execute full pipeline including actual file copy",
    )
    g.add_argument(
        "--inspect-only", action="store_true",
        help="Print folder structure only, stop after Phase 1",
    )
    p.add_argument(
        "--skip-validation", action="store_true",
        help="Skip OpenCV video validation (faster but not recommended)",
    )
    p.add_argument(
        "--min-videos", type=int,
        default=CONFIG["MIN_VIDEOS_PER_WORD"], metavar="N",
        help=f"Minimum valid videos required per word (default: {CONFIG['MIN_VIDEOS_PER_WORD']})",
    )
    p.add_argument(
        "--max-videos", type=int,
        default=CONFIG["TARGET_VIDEOS_PER_WORD"], metavar="N",
        help=f"Target videos to select per word (default: {CONFIG['TARGET_VIDEOS_PER_WORD']})",
    )
    p.add_argument(
        "--source", type=str,
        default=CONFIG["ORIGINAL_DATASET_ROOT"],
        help="Override source dataset path",
    )
    p.add_argument(
        "--dest", type=str,
        default=CONFIG["OPTIMIZED_DATASET_ROOT"],
        help="Override destination path",
    )
    return p.parse_args()

# ==============================================================================
#  MAIN
# ==============================================================================
def main() -> None:
    args = parse_args()

    # Apply CLI overrides
    CONFIG["ORIGINAL_DATASET_ROOT"]  = args.source
    CONFIG["OPTIMIZED_DATASET_ROOT"] = args.dest
    CONFIG["MIN_VIDEOS_PER_WORD"]    = args.min_videos
    CONFIG["TARGET_VIDEOS_PER_WORD"] = args.max_videos
    dry_run = args.dry_run or args.inspect_only

    logger = setup_logging(CONFIG["LOGS_DIR"], dry_run=dry_run)

    mode_label = (
        "DRY-RUN  (nothing will be written)"
        if dry_run else
        "LIVE COPY  (files will be COPIED to destination)"
    )

    logger.info("")
    logger.info("+------------------------------------------------------------------+")
    logger.info("|   INCLUDE ISL Dataset Optimization Pipeline  v2.0               |")
    logger.info(f"|   Mode   : {mode_label:<54}|")
    logger.info("+------------------------------------------------------------------+")
    logger.info(f"  Source  : {CONFIG['ORIGINAL_DATASET_ROOT']}")
    logger.info(f"  Dest    : {CONFIG['OPTIMIZED_DATASET_ROOT']}")
    logger.info(f"  Output  : <dest>/<WORD>/<video>  (NO category layer)")
    logger.info("")

    # ── OpenCV warning ────────────────────────────────────────────────────────
    if not CV2_AVAILABLE:
        logger.warning("  [NOTICE] opencv-python is NOT installed.")
        logger.warning("           Video validation will be SKIPPED.")
        logger.warning("           Run:  pip install opencv-python")
        logger.info("")
        if args.run and not args.skip_validation:
            logger.error(
                "  STOPPING: --run without OpenCV validation is unsafe.\n"
                "  Install opencv-python or add --skip-validation flag."
            )
            sys.exit(1)

    # ── Safety gate ───────────────────────────────────────────────────────────
    safety_check(
        CONFIG["ORIGINAL_DATASET_ROOT"],
        CONFIG["OPTIMIZED_DATASET_ROOT"],
        logger,
    )

    start = time.time()

    # ── Phase 1: Inspect ──────────────────────────────────────────────────────
    catalogue = inspect_dataset(CONFIG["ORIGINAL_DATASET_ROOT"], logger)

    if args.inspect_only:
        logger.info(f"  --inspect-only complete.  Elapsed: {time.time()-start:.1f}s")
        return

    # ── Phase 2: Detect duplicates ────────────────────────────────────────────
    duplicate_words, word_to_cats = detect_duplicates(catalogue, logger)

    # ── Phase 3: Validate ─────────────────────────────────────────────────────
    if args.skip_validation or not CV2_AVAILABLE:
        logger.warning("  Validation SKIPPED -- treating all found videos as valid.")
        validated = {
            cat: {
                word: ([] if word in duplicate_words else list(vids))
                for word, vids in words.items()
            }
            for cat, words in catalogue.items()
        }
        vlog: List[dict] = []
    else:
        validated, vlog = validate_catalogue(catalogue, duplicate_words, logger)

    # ── Phase 4: Select ───────────────────────────────────────────────────────
    selection_map, slog = select_videos(validated, duplicate_words, logger)

    # ── Phase 5: Dry-run plan ─────────────────────────────────────────────────
    plan = dry_run_report(
        selection_map, word_to_cats, duplicate_words,
        CONFIG["OPTIMIZED_DATASET_ROOT"], logger,
    )

    # ── Phase 6: Actual copy (--run only) ─────────────────────────────────────
    if args.run:
        logger.warning("")
        logger.warning("  [!] LIVE MODE: Files will be copied in 5 seconds.")
        logger.warning("      Press Ctrl+C NOW to abort without any changes.")
        logger.warning("")
        try:
            time.sleep(5)
        except KeyboardInterrupt:
            logger.info("  Aborted by user. No files were written.")
            sys.exit(0)
        plan = execute_copy(plan, logger)

    # ── Phase 7: Reports ──────────────────────────────────────────────────────
    _section(logger, "PHASE 7 — WRITING REPORTS")

    # On dry-run  : reports go to Logs dir
    # On live run : reports go to the actual 02_INCLUDE_Dataset_Optimized folder
    report_dir = (
        CONFIG["OPTIMIZED_DATASET_ROOT"] if args.run
        else CONFIG["LOGS_DIR"]
    )

    if vlog:
        write_metadata_csv(vlog, slog, plan, report_dir, logger)
    else:
        logger.info(
            "  (No validation log written -- OpenCV validation was skipped)"
        )

    write_summary_json(
        catalogue, validated, selection_map, duplicate_words,
        plan, dry_run, report_dir, logger,
    )

    elapsed = time.time() - start
    logger.info("")
    logger.info("=" * 68)
    logger.info(f"  Pipeline finished in {elapsed:.1f}s")
    if dry_run:
        logger.info("  DRY-RUN complete. No files were written.")
        logger.info("  When ready, execute the actual optimization:")
        logger.info(
            "  python optimize_include_dataset.py --run"
        )
    else:
        logger.info("  LIVE RUN complete.")
        logger.info(
            f"  Optimized dataset : {CONFIG['OPTIMIZED_DATASET_ROOT']}"
        )
    logger.info("=" * 68)
    logger.info("")


if __name__ == "__main__":
    main()
