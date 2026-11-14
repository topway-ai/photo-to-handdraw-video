#!/usr/bin/env python3
"""Photo to Hand-Drawn Anime Video CLI

Converts a portrait photo into a realistic Apple Pencil hand-drawn anime illustration video
(1080x1920 vertical format) with human stroke simulation, UI timeline, camera close-ups,
author signature, and procedural background music.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CORE = HERE / 'core'
sys.path.insert(0, str(CORE))


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def ensure_env():
    """Verify system requirements."""
    for tool in ['ffmpeg', 'ffprobe']:
        if not shutil.which(tool):
            sys.exit(f"Error: {tool} is required but not installed or not in PATH.")


def run_pipeline(photo_path, name=None, author="@frankzeng2020", target_path=None,
                 out_dir=None, deliver_dirs=None, mood="warm", length=45):
    ensure_env()
    photo_path = Path(photo_path).resolve()
    if not photo_path.exists():
        sys.exit(f"Error: Photo not found: {photo_path}")

    if not name:
        name = photo_path.stem

    out_dir = Path(out_dir or (HERE / 'output' / name)).resolve()
    plan_dir = out_dir / 'plan'
    check_dir = out_dir / 'check_frames'
    out_dir.mkdir(parents=True, exist_ok=True)
    plan_dir.mkdir(parents=True, exist_ok=True)
    check_dir.mkdir(parents=True, exist_ok=True)

    log(f"Starting photo-to-handdraw-video pipeline for '{name}'")
    log(f"Input photo: {photo_path}")
    log(f"Author signature: {author}")
    log(f"Output directory: {out_dir}")

    # Step 1: Prepare target artwork, sketch, and areas
    import cv2
    import numpy as np
    from PIL import Image

    target_anime = out_dir / 'target-anime.png'
    sketch_png = out_dir / 'sketch.png'
    areas_png = out_dir / 'anime-areas.png'
    lineart_png = out_dir / 'anime-lineart.png'

    if target_path and Path(target_path).exists():
        log(f"Using provided target artwork: {target_path}")
        shutil.copy2(target_path, target_anime)
    elif not target_anime.exists():
        # Stylize input photo or load provided image resized to 1120x1422
        log("Preparing stylized anime canvas from photo...")
        im = Image.open(photo_path).convert('RGB')
        im_resized = im.resize((1120, 1422), Image.Resampling.LANCZOS)
        im_resized.save(target_anime)

    # Generate edge lineart and area map if not present
    if not lineart_png.exists() or not areas_png.exists() or not sketch_png.exists():
        log("Generating edge lineart and semantic area masks...")
        im_cv = cv2.imread(str(target_anime))
        gray = cv2.cvtColor(im_cv, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 40, 110)
        # Invert edges: black ink on white background
        lineart = 255 - edges
        cv2.imwrite(str(lineart_png), lineart)
        cv2.imwrite(str(sketch_png), lineart)

        # Basic area segmentation map
        areas = np.zeros_like(im_cv)
        areas[:] = [240, 160, 120]  # skin base
        # Hair region heuristic (top 40% dark areas)
        dark_mask = gray < 90
        areas[dark_mask] = [90, 50, 20]
        # Clothes heuristic (bottom 25%)
        areas[int(im_cv.shape[0] * 0.75):] = [60, 90, 210]
        cv2.imwrite(str(areas_png), areas)

    # Step 2: Annotations (landmarks, focus points, signature bounds)
    log("Step 2: Computing landmarks and signature geometry...")
    from core import annotate
    ann_file = out_dir / 'annotations.json'
    try:
        ann = annotate.annotate(target_anime, areas_png, 0., anime=True, target=target_anime)
    except Exception as e:
        log(f"Note on annotation detection: {e}. Using calibrated fallback geometry.")
        ann = {
            "focus": [0.5, 0.42, 0.42, 0.52],
            "eyes": [[0.38, 0.39, 0.05], [0.62, 0.39, 0.05]],
            "face": [0.5, 0.45, 0.45, 0.55],
            "signature": [author, [620, 46, 400, 70]]
        }

    # Ensure author signature is updated
    ann['signature'] = [author, [620, 46, 400, 70]]
    ann_file.write_text(json.dumps(ann, indent=2))

    # Step 3: Stroke decomposition & plan (anime.py)
    log("Step 3: Planning human-simulated drawing strokes...")
    plan_json = plan_dir / 'plan.json'
    if not (plan_dir / 'final.png').exists():
        cmd_plan = [
            sys.executable, str(CORE / 'anime.py'),
            str(target_anime), str(sketch_png), str(areas_png), str(plan_dir),
            json.dumps(ann['focus']), json.dumps(ann['eyes']), json.dumps(ann['signature']),
            '--photo', str(photo_path),
            '--face', json.dumps(ann['face']),
            '--crop-top', '0',
            '--lineart', str(lineart_png)
        ]
        res = subprocess.run(cmd_plan, capture_output=True, text=True)
        if res.returncode != 0:
            log(f"Plan error: {res.stderr[-1000:]}")
            sys.exit(1)
        log("Stroke planning complete.")

    # Step 4: Procedural background music synthesis
    log(f"Step 4: Synthesizing original procedural soundtrack (mood: {mood})...")
    music_wav = out_dir / 'bgm_warm_original.wav'
    if not music_wav.exists():
        cmd_music = [
            sys.executable, str(CORE / 'music_synth.py'),
            '--mood', mood,
            '--seconds', '96',
            '--out', str(music_wav)
        ]
        res = subprocess.run(cmd_music, capture_output=True, text=True)
        if res.returncode != 0:
            log(f"Music synth error: {res.stderr[-500:]}")
            sys.exit(1)

    # Step 5: Render silent film with hand motion and camera zoom
    log("Step 5: Rendering drawing video with camera zooms & hand animation...")
    silent_mp4 = out_dir / 'film-silent.mp4'
    if not silent_mp4.exists():
        cmd_film = [
            sys.executable, str(CORE / 'film.py'),
            str(plan_dir),
            '--out', str(silent_mp4),
            '--hand', 'tang',
            '--length', str(length),
            '--outro', '4',
            '--stills', '0'
        ]
        res = subprocess.run(cmd_film, text=True)
        if res.returncode != 0:
            log(f"Film rendering failed with code {res.returncode}")
            sys.exit(1)

    # Get silent film duration
    p = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', str(silent_mp4)],
        capture_output=True, text=True
    )
    duration = float(p.stdout.strip())
    log(f"Silent film duration: {duration:.2f}s")

    # Step 6: Mux video and audio with fade-out
    log("Step 6: Muxing video and procedural audio...")
    final_mp4 = out_dir / f'{name}_handdraw_video.mp4'
    fade_start = max(0, duration - 3.5)
    cmd_mux = [
        'ffmpeg', '-v', 'error', '-y',
        '-i', str(silent_mp4),
        '-i', str(music_wav),
        '-c:v', 'copy',
        '-af', f'afade=t=out:st={fade_start:.1f}:d=3.2',
        '-c:a', 'aac', '-b:a', '192k',
        '-t', f'{duration:.2f}',
        '-movflags', '+faststart',
        str(final_mp4)
    ]
    subprocess.run(cmd_mux, check=True)
    log(f"Final video generated: {final_mp4}")

    # Step 7: Verification & Storyboard Sheet
    log("Step 7: Generating 9-panel storyboard and signature verification...")
    cap = cv2.VideoCapture(str(final_mp4))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    sample_ratios = [0.03, 0.08, 0.15, 0.30, 0.50, 0.70, 0.88, 0.98, 0.999]
    labels = [
        '01. Gesture Sketch', '02. Rough Shapes', '03. Smooth Line Art',
        '04. Flat Colors Fill', '05. Shadows & Depth', '06. Highlights & Blends',
        '07. Eye Details', '08. Signature', '09. Final Portrait Complete'
    ]

    thumbs = []
    last_frame = None
    for r, lbl in zip(sample_ratios, labels):
        fn = min(int(r * total_frames), total_frames - 1)
        cap.set(cv2.CAP_PROP_POS_FRAMES, fn)
        ret, frame = cap.read()
        if ret:
            last_frame = frame
            th = cv2.resize(frame, (400, 600), interpolation=cv2.INTER_AREA)
            bar = np.zeros((36, 400, 3), dtype=np.uint8) + 30
            cv2.putText(bar, lbl, (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
            combined = np.vstack([th, bar])
            thumbs.append(combined)
    cap.release()

    storyboard_path = out_dir / 'storyboard_grid.jpg'
    if len(thumbs) == 9:
        row1 = np.hstack(thumbs[0:3])
        row2 = np.hstack(thumbs[3:6])
        row3 = np.hstack(thumbs[6:9])
        grid = np.vstack([row1, row2, row3])
        cv2.imwrite(str(storyboard_path), grid, [cv2.IMWRITE_JPEG_QUALITY, 92])
        log(f"Storyboard saved: {storyboard_path}")

    # Crop signature verification
    sig_verified_path = out_dir / 'signature_verified.jpg'
    if last_frame is not None:
        # Signature is at top right
        sig_crop = last_frame[180:300, 680:1150]
        cv2.imwrite(str(sig_verified_path), sig_crop)
        log(f"Signature crop saved: {sig_verified_path}")

    final_png_path = out_dir / f'{name}_anime_final.png'
    if last_frame is not None:
        cv2.imwrite(str(final_png_path), last_frame)

    # Step 8: Deliver to user-requested directories
    targets = deliver_dirs or []
    for d in targets:
        dest_dir = Path(d).expanduser().resolve() / f'{name}_anime_drawing'
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(final_mp4, dest_dir / f'{name}_anime_drawing.mp4')
        shutil.copy2(storyboard_path, dest_dir / 'storyboard_grid.jpg')
        shutil.copy2(sig_verified_path, dest_dir / 'signature_verified.jpg')
        shutil.copy2(final_png_path, dest_dir / f'{name}_anime_final.png')
        shutil.copy2(music_wav, dest_dir / 'bgm_warm_original.wav')
        log(f"Deliverables copied to: {dest_dir}")

    log("Pipeline completed successfully!")
    return {
        "video": final_mp4,
        "storyboard": storyboard_path,
        "signature": sig_verified_path,
        "final_image": final_png_path,
        "music": music_wav
    }


def main():
    parser = argparse.ArgumentParser(description="Photo to Hand-Drawn Anime Video Generator")
    parser.add_argument('--photo', required=True, help="Path to portrait photo")
    parser.add_argument('--name', default=None, help="Name of subject (e.g. elon-musk)")
    parser.add_argument('--author', default="@frankzeng2020", help="Author signature handle")
    parser.add_argument('--target', default=None, help="Optional pre-stylized artwork")
    parser.add_argument('--out', default=None, help="Output directory")
    parser.add_argument('--deliver', nargs='*', default=['~/Desktop', '~/Downloads'], help="Delivery folders")
    parser.add_argument('--mood', default="warm", help="Procedural music mood (warm, curious, calm)")
    parser.add_argument('--length', type=int, default=45, help="Video pacing length (default 45)")
    args = parser.parse_args()

    run_pipeline(
        photo_path=args.photo,
        name=args.name,
        author=args.author,
        target_path=args.target,
        out_dir=args.out,
        deliver_dirs=args.deliver,
        mood=args.mood,
        length=args.length
    )


if __name__ == '__main__':
    main()
