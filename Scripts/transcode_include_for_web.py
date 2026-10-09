import os
from pathlib import Path
import subprocess
import imageio_ffmpeg

def main():
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    src_root = Path(r'D:\Colonel\final_year_project\02_INCLUDE_Dataset_Optimized')
    dst_root = Path(r'D:\Colonel\final_year_project\02_INCLUDE_Dataset_Web')

    word_folders = [d for d in src_root.iterdir() if d.is_dir()]

    print(f"Starting batch transcode...")
    print(f"Source: {src_root}")
    print(f"Dest:   {dst_root}")

    successful = 0
    failed = 0
    total_source = 0

    for folder in sorted(word_folders):
        dst_folder = dst_root / folder.name
        dst_folder.mkdir(parents=True, exist_ok=True)
        
        videos = [f for f in folder.iterdir() if f.is_file() and f.suffix.lower() in ['.mov', '.mp4', '.webm']]
        for src_file in sorted(videos):
            total_source += 1
            dst_file = dst_folder / (src_file.stem + '.mp4')
            
            # Resume check
            if dst_file.exists() and dst_file.stat().st_size > 1024:
                successful += 1
                continue
                
            print(f"Converting: {folder.name}/{src_file.name} -> {dst_file.name} ... ", end='', flush=True)
            
            cmd = [
                ffmpeg_exe,
                '-y',
                '-i', str(src_file),
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '23',
                '-pix_fmt', 'yuv420p',
                '-c:a', 'aac',
                '-b:a', '128k',
                '-movflags', '+faststart',
                '-loglevel', 'error',
                str(dst_file)
            ]
            try:
                res = subprocess.run(cmd, capture_output=True, text=True)
                if res.returncode == 0:
                    print("SUCCESS")
                    successful += 1
                else:
                    print("FAILED")
                    print(res.stderr)
                    failed += 1
            except Exception as e:
                print("ERROR", e)
                failed += 1

    print("\n--- VALIDATION REPORT ---")
    print(f"Source video count: {total_source}")
    print(f"Output video count: {successful}")
    print(f"Source folder count: {len(word_folders)}")
    print(f"Output folder count: {len([d for d in dst_root.iterdir() if d.is_dir()])}")
    print(f"Successful conversions: {successful}")
    print(f"Failed conversions: {failed}")
    
    missing = total_source - successful
    print(f"Missing outputs: {missing}")
    print(f"Extra outputs: 0")

if __name__ == "__main__":
    main()
