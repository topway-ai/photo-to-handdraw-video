---
name: photo-to-handdraw-video
description: Converts any human portrait photo into a realistic Apple Pencil hand-drawn anime illustration process video (1080x1920 vertical format) with human stroke simulation, UI timeline, camera close-ups, cursive author signature, and original procedural background music.
---

# Photo to Hand-Drawn Anime Video

This skill automates the creation of high-retention, digital hand-drawing demonstration videos from any human portrait photo. It simulates a professional digital artist working on an iPad/tablet using an Apple Pencil, complete with realistic hand movement, stage transitions, progressive coloring, camera zooms, and original procedural audio.

## Key Capabilities & Guardrails
- **Humanized Stroke Simulation**: Eliminates robotic coordinate crosshairs and rigid mathematical ellipses; uses natural wrist arcs for head cranial domes, dual jaw gestures, and 1D Gaussian streamline smoothing ($\sigma = 1.8$) for continuous, non-jagged line art.
- **Noise & Stub Suppression**: Filters out fragmented edge noise (< 55px), preventing choppy debris along cheeks and jawlines.
- **Camera Zoom Close-ups Without Ghosting**: Applies an opaque header mask to prevent double-header artifacts during camera close-ups on facial features.
- **Full Signature Verification**: Dynamically places and renders cursive author watermarks (e.g. `@frankzeng2020`) with expanded canvas bounding boxes to prevent character clipping.
- **100% Original Procedural Soundtrack**: Synthesizes custom Lo-Fi piano music in F major (74 BPM) with smooth fade-outs, avoiding copyright claims.
- **Self-Inspection**: Automatically outputs a 9-panel storyboard contact sheet (`storyboard_grid.jpg`) and a signature verification crop (`signature_verified.jpg`).

---

## Prerequisites & Installation

### 1. System Requirements
- Python 3.9+
- `ffmpeg` & `ffprobe` (for video encoding and audio muxing)

### 2. Python Dependencies
```bash
pip install -r requirements.txt
```

---

## One-Command Quickstart

Run the unified CLI from the repository root:

```bash
python cli.py \
  --photo path/to/portrait.jpg \
  --name "person-name" \
  --author "@frankzeng2020" \
  --deliver ~/Desktop ~/Downloads
```

### CLI Arguments
| Argument | Description | Default |
| :--- | :--- | :--- |
| `--photo` | **Required.** Path to the source portrait photo. | None |
| `--name` | Identifier slug for the subject (e.g. `elon-musk`). | Photo stem |
| `--author` | Watermark & handwritten canvas signature handle. | `@frankzeng2020` |
| `--target` | Optional pre-stylized anime/comic artwork. | Auto-generated |
| `--out` | Output directory for interim files & final renders. | `./output/<name>` |
| `--deliver` | Destination folders to copy completed packages. | `['~/Desktop', '~/Downloads']` |
| `--mood` | Procedural music mood (`warm`, `curious`, `calm`). | `warm` |
| `--length` | Pacing length factor (seconds). | `45` |

---

## Pipeline Execution Stages

When executing this skill, follow these sequential stages:

### Stage 1: Artwork & Canvas Preparation
1. Load or resize the reference photo to portrait aspect ratio (1120×1422 canvas).
2. Generate semantic layer masks (`anime-areas.png`) and clean edge line art (`anime-lineart.png`).

### Stage 2: Landmark & Signature Annotation (`core/annotate.py`)
1. Detect facial landmarks (eyes, nose, mouth, face contour) via MediaPipe or fallback geometry.
2. Calculate focus points for camera close-ups.
3. Compute signature coordinates with width $\ge 400\text{px}$ to guarantee no character clipping.

### Stage 3: Stroke Decomposition & Planning (`core/anime.py`)
1. Deconstruct the illustration into 10 natural passes:
   - `rough`: Loose wrist arcs for cranial dome and jawline (no crosshairs).
   - `lines`: Continuous, smoothed ink outlines with Gaussian streamline filter ($\sigma = 1.8$, threshold $55\text{px}$).
   - `flat`: Base color fill.
   - `shadow`: Cel-shading depth.
   - `light`: Soft highlights.
   - `gradient`: Tonal gradations.
   - `polish`: Structural micro-details.
   - `dianjing`: Eye pupils, iris reflections, and specular highlights.
   - `adjust`: Global color grading.
   - `sign`: Handwritten cursive signature.

### Stage 4: Original Music Synthesis (`core/music_synth.py`)
1. Generate an original diatonic Lo-Fi soundtrack (~90–96s) using detuned band-limited wavetables, soft FM electric piano, and sine bass.
2. Normalize loudness to $-16\text{ LUFS}$.

### Stage 5: Video Render & Camera Zoom (`core/film.py`)
1. Animate the white stylus hand overlay (`tang`).
2. Trigger dynamic camera zoom close-ups on eyes and face.
3. Apply solid opacity mask to header rows to ensure zero double-text ghosting.

### Stage 6: Muxing & Keyframe Self-Inspection
1. Mux silent video with the synthesized music track using `ffmpeg`, adding a 3.2s audio fade-out.
2. Extract keyframes across all 9 drawing stages and compile `storyboard_grid.jpg`.
3. Crop the signature box and save `signature_verified.jpg` for automated visual verification.

---

## Verification Checklist

Before reporting completion to the user:
- [ ] **No Crosshairs**: Inspect early frames (0–5s); ensure no ruler-straight center crosshairs or mathematical ellipses appear.
- [ ] **Smooth Contours**: Check line art frames (10–20s); verify lines are fluid without jagged 1px staircases or disconnected debris stubs.
- [ ] **Header Stability**: Verify zoom frames (around 15s); ensure the top header text remains crisp with no double-ghosting.
- [ ] **Complete Signature**: Check `signature_verified.jpg`; confirm all glyphs of the author handle (e.g. `@frankzeng2020`) are visible with right-side padding.
- [ ] **Deliverables Deployed**: Confirm files exist in target folders (`~/Desktop` and `~/Downloads`).
