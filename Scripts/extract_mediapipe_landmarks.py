#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INCLUDE Dataset - MediaPipe Landmark Extraction Pipeline
Extracts pose and hand landmarks for sign language modeling.
"""

import os
import sys
import csv
import glob
import time
import argparse
import traceback
from pathlib import Path
import numpy as np

try:
    import cv2
    import mediapipe as mp
except ImportError:
    print("FATAL: OpenCV and MediaPipe are required. Run: pip install opencv-python mediapipe numpy")
    sys.exit(1)

CONFIG = {
    "SOURCE_ROOT": r"D:\Colonel\final_year_project\02_INCLUDE_Dataset_Optimized",
    "OUTPUT_ROOT": r"D:\Colonel\final_year_project\03_MediaPipe_Landmarks",
    "TEST_SAMPLE_SIZE": 5,
    "MIN_DETECTION_CONFIDENCE": 0.5,
    "MIN_TRACKING_CONFIDENCE": 0.5,
    "MODEL_COMPLEXITY": 0, # 0 is faster, 1 is more accurate. 0 chosen for i5 laptop performance.
}

def setup_output_dirs(base_path):
    dirs = {
        "raw": os.path.join(base_path, "Raw_Landmarks"),
        "norm": os.path.join(base_path, "Normalized_Landmarks"),
        "meta": os.path.join(base_path, "Metadata"),
        "vis": os.path.join(base_path, "Visualizations"),
        "logs": os.path.join(base_path, "Logs")
    }
    for d in dirs.values():
        os.makedirs(d, exist_ok=True)
        
    # Write a quick README
    readme_path = os.path.join(base_path, "README.md")
    if not os.path.exists(readme_path):
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write("# MediaPipe Landmarks Dataset\n\n")
            f.write("Extracted temporal sequences of pose and hand landmarks from the INCLUDE dataset.\n\n")
            f.write("## Structure\n")
            f.write("- `Raw_Landmarks/`: Unmodified world-coordinate landmarks (.npz)\n")
            f.write("- `Normalized_Landmarks/`: Landmarks translated to shoulder-midpoint origin and scaled (.npz)\n")
            f.write("- `Metadata/`: CSV logs mapping videos to extraction status\n")
            f.write("- `Visualizations/`: Test-run visualization videos\n")
            f.write("- `Logs/`: System logs\n")
    return dirs

def extract_landmarks_from_results(results):
    # Pose: 33 landmarks, Hand: 21 landmarks each
    pose = np.full((33, 4), np.nan) # x, y, z, visibility
    lh = np.full((21, 3), np.nan)   # x, y, z
    rh = np.full((21, 3), np.nan)
    
    if results.pose_landmarks:
        for i, lm in enumerate(results.pose_landmarks.landmark):
            pose[i] = [lm.x, lm.y, lm.z, lm.visibility]
            
    if results.left_hand_landmarks:
        for i, lm in enumerate(results.left_hand_landmarks.landmark):
            lh[i] = [lm.x, lm.y, lm.z]
            
    if results.right_hand_landmarks:
        for i, lm in enumerate(results.right_hand_landmarks.landmark):
            rh[i] = [lm.x, lm.y, lm.z]
            
    return pose, lh, rh

def normalize_landmarks(pose, lh, rh):
    """
    Normalizes coordinates relative to the midpoint between the shoulders.
    Scale is determined by the distance between the shoulders.
    """
    norm_pose = np.copy(pose)
    norm_lh = np.copy(lh)
    norm_rh = np.copy(rh)
    
    # Check if shoulders (11 and 12) exist and are valid
    if not np.isnan(pose[11, 0]) and not np.isnan(pose[12, 0]):
        shoulder_l = pose[11, :3]
        shoulder_r = pose[12, :3]
        origin = (shoulder_l + shoulder_r) / 2.0
        
        # Euclidean distance between shoulders
        scale = np.linalg.norm(shoulder_l - shoulder_r)
        if scale < 1e-5:
            scale = 1.0
            
        norm_pose[:, :3] = (pose[:, :3] - origin) / scale
        norm_lh = (lh - origin) / scale
        norm_rh = (rh - origin) / scale
        
    return norm_pose, norm_lh, norm_rh

def process_video(video_path, mp_holistic, draw=False, vis_out_path=None):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise Exception(f"Cannot open video: {video_path}")
        
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    frames_pose = []
    frames_lh = []
    frames_rh = []
    
    frames_norm_pose = []
    frames_norm_lh = []
    frames_norm_rh = []
    
    pose_detected = 0
    lh_detected = 0
    rh_detected = 0
    
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles
    mp_pose = mp.solutions.pose
    mp_hands = mp.solutions.hands
    
    vis_writer = None
    if draw and vis_out_path:
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        vis_writer = cv2.VideoWriter(vis_out_path, fourcc, fps, (w, h))

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False
            results = mp_holistic.process(image)
            
            pose, lh, rh = extract_landmarks_from_results(results)
            n_pose, n_lh, n_rh = normalize_landmarks(pose, lh, rh)
            
            frames_pose.append(pose)
            frames_lh.append(lh)
            frames_rh.append(rh)
            
            frames_norm_pose.append(n_pose)
            frames_norm_lh.append(n_lh)
            frames_norm_rh.append(n_rh)
            
            if results.pose_landmarks: pose_detected += 1
            if results.left_hand_landmarks: lh_detected += 1
            if results.right_hand_landmarks: rh_detected += 1
            
            if draw and vis_writer:
                image.flags.writeable = True
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                if results.pose_landmarks:
                    mp_drawing.draw_landmarks(
                        image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                        landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style())
                if results.left_hand_landmarks:
                    mp_drawing.draw_landmarks(
                        image, results.left_hand_landmarks, mp_hands.HAND_CONNECTIONS)
                if results.right_hand_landmarks:
                    mp_drawing.draw_landmarks(
                        image, results.right_hand_landmarks, mp_hands.HAND_CONNECTIONS)
                vis_writer.write(image)
    finally:
        cap.release()
        if vis_writer:
            vis_writer.release()
            
    seq_len = len(frames_pose)
    if seq_len == 0:
        raise Exception("Zero frames processed.")
        
    raw_data = {
        "pose": np.array(frames_pose),
        "left_hand": np.array(frames_lh),
        "right_hand": np.array(frames_rh)
    }
    norm_data = {
        "pose": np.array(frames_norm_pose),
        "left_hand": np.array(frames_norm_lh),
        "right_hand": np.array(frames_norm_rh)
    }
    
    stats = {
        "fps": fps,
        "frame_count": frame_count,
        "sequence_length": seq_len,
        "pose_detected_frames": pose_detected,
        "left_hand_detected_frames": lh_detected,
        "right_hand_detected_frames": rh_detected
    }
    
    return raw_data, norm_data, stats

def main():
    parser = argparse.ArgumentParser(description="Extract MediaPipe Landmarks from INCLUDE optimized dataset")
    parser.add_argument("--test", action="store_true", help="Run in test mode (small sample)")
    parser.add_argument("--run", action="store_true", help="Run on full dataset")
    parser.add_argument("--resume", action="store_true", help="Skip already processed videos")
    parser.add_argument("--source", type=str, default=CONFIG["SOURCE_ROOT"])
    parser.add_argument("--output", type=str, default=CONFIG["OUTPUT_ROOT"])
    args = parser.parse_args()
    
    if not args.test and not args.run:
        print("Must specify --test or --run")
        sys.exit(1)
        
    print("==================================================")
    print("MediaPipe Landmark Extraction Pipeline")
    print("==================================================")
    
    source_dir = args.source
    output_dir = args.output
    
    dirs = setup_output_dirs(output_dir)
    
    # Try to load dataset metadata to get original category
    word_category_map = {}
    metadata_csv_path = os.path.join(source_dir, "dataset_metadata.csv")
    if os.path.exists(metadata_csv_path):
        try:
            with open(metadata_csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    word_category_map[row["word"]] = row.get("category", "unknown")
        except Exception as e:
            print(f"Warning: Could not read dataset metadata: {e}")
            
    # Find videos
    video_paths = []
    if os.path.exists(source_dir):
        for word_dir in sorted(os.listdir(source_dir)):
            wp = os.path.join(source_dir, word_dir)
            if not os.path.isdir(wp): continue
            for vf in sorted(os.listdir(wp)):
                if vf.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
                    video_paths.append((word_dir, vf, os.path.join(wp, vf)))
                
    if not video_paths:
        print(f"No videos found in {source_dir}")
        sys.exit(1)
        
    print(f"Total videos discovered in dataset: {len(video_paths)}")
    
    if args.test:
        print(f"TEST MODE: Selecting {CONFIG['TEST_SAMPLE_SIZE']} videos for processing.")
        video_paths = video_paths[:CONFIG["TEST_SAMPLE_SIZE"]]
        
    metadata_csv = os.path.join(dirs["meta"], "extraction_metadata.csv")
    file_exists = os.path.exists(metadata_csv)
    
    fieldnames = [
        "word", "original_category", "video_filename", "source_path", "fps", "frame_count", 
        "sequence_length", "pose_detected_frames", "left_hand_detected_frames",
        "right_hand_detected_frames", "extraction_status", "normalization_status",
        "raw_file", "norm_file"
    ]
    
    # Setup MediaPipe Holistic
    mp_holistic = mp.solutions.holistic.Holistic(
        static_image_mode=False,
        model_complexity=CONFIG["MODEL_COMPLEXITY"],
        enable_segmentation=False,
        refine_face_landmarks=False,
        min_detection_confidence=CONFIG["MIN_DETECTION_CONFIDENCE"],
        min_tracking_confidence=CONFIG["MIN_TRACKING_CONFIDENCE"]
    )
    
    success_count = 0
    fail_count = 0
    seq_lengths = []
    pose_dets = []
    lh_dets = []
    rh_dets = []
    
    try:
        with open(metadata_csv, "a", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
                
            for idx, (word, vf, vpath) in enumerate(video_paths):
                base_name = os.path.splitext(vf)[0]
                out_name = f"{word}_{base_name}.npz"
                raw_out_path = os.path.join(dirs["raw"], out_name)
                norm_out_path = os.path.join(dirs["norm"], out_name)
                
                if args.resume and os.path.exists(raw_out_path) and os.path.exists(norm_out_path):
                    print(f"[{idx+1}/{len(video_paths)}] SKIPPING (already exists): {word}/{vf}")
                    continue
                    
                print(f"[{idx+1}/{len(video_paths)}] PROCESSING: {word}/{vf}")
                
                vis_out_path = None
                if args.test:
                    vis_out_path = os.path.join(dirs["vis"], f"{word}_{base_name}_vis.mp4")
                    
                try:
                    # process_video performs extraction + sequential resource release
                    raw_data, norm_data, stats = process_video(vpath, mp_holistic, draw=args.test, vis_out_path=vis_out_path)
                    
                    np.savez_compressed(raw_out_path, **raw_data)
                    np.savez_compressed(norm_out_path, **norm_data)
                    
                    writer.writerow({
                        "word": word,
                        "original_category": word_category_map.get(word, "unknown"),
                        "video_filename": vf,
                        "source_path": vpath,
                        "fps": stats["fps"],
                        "frame_count": stats["frame_count"],
                        "sequence_length": stats["sequence_length"],
                        "pose_detected_frames": stats["pose_detected_frames"],
                        "left_hand_detected_frames": stats["left_hand_detected_frames"],
                        "right_hand_detected_frames": stats["right_hand_detected_frames"],
                        "extraction_status": "success",
                        "normalization_status": "success",
                        "raw_file": raw_out_path,
                        "norm_file": norm_out_path
                    })
                    csvfile.flush() # Save metadata incrementally
                    
                    success_count += 1
                    seq_lengths.append(stats["sequence_length"])
                    pose_dets.append(stats["pose_detected_frames"])
                    lh_dets.append(stats["left_hand_detected_frames"])
                    rh_dets.append(stats["right_hand_detected_frames"])
                    
                except Exception as e:
                    fail_count += 1
                    print(f"  ERROR processing {vf}: {e}")
                    traceback.print_exc()
                    writer.writerow({
                        "word": word,
                        "original_category": word_category_map.get(word, "unknown"),
                        "video_filename": vf,
                        "source_path": vpath,
                        "fps": "", "frame_count": "", "sequence_length": "",
                        "pose_detected_frames": "", "left_hand_detected_frames": "",
                        "right_hand_detected_frames": "",
                        "extraction_status": f"failed: {str(e)}",
                        "normalization_status": "failed",
                        "raw_file": "", "norm_file": ""
                    })
                    csvfile.flush()
    finally:
        mp_holistic.close()
        
    print("\n==================================================")
    print("EXTRACTION COMPLETE")
    print("==================================================")
    print(f"Videos processed : {success_count + fail_count}")
    print(f"Successful       : {success_count}")
    print(f"Failed           : {fail_count}")
    if success_count > 0:
        print(f"Avg sequence len : {sum(seq_lengths)/len(seq_lengths):.1f} frames")
        print(f"Avg pose det     : {sum(pose_dets)/len(pose_dets):.1f} frames")
        print(f"Avg left hand det: {sum(lh_dets)/len(lh_dets):.1f} frames")
        print(f"Avg right hand   : {sum(rh_dets)/len(rh_dets):.1f} frames")
    print(f"Output files in  : {output_dir}")

if __name__ == "__main__":
    main()
