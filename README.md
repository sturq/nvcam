# NVCam

Android camera with a camcorder night-shot look. The live feed runs through a GLSL shader,
so the viewfinder, photos and videos all get the same look: almost monochrome, near-black
shadows with a faint purple, mint-white highlights that glow, soft detail, light grain and a
slight lens bulge.

Built from [CCDCam](https://github.com/sturq/ccdcam) (same camera and recording pipeline,
own shader, UI and icon).

## Features

- Live filtered preview
- Photo mode, JPEG saved to `Pictures/NVCam` (currently at preview resolution)
- Video mode, H.264 + AAC with the look baked in, saved to `Movies/NVCam`
- Pinch to zoom, front/back camera, 16:9 or 4:3
- Camcorder HUD: STBY/REC, timecode, battery, date

## Tweaking the look

All constants sit at the top of `app/src/main/assets/shaders/nv.frag`. `tools/nv_sim.py`
mirrors them in numpy, so a change can be checked on a JPEG before building:

```
python tools/nv_sim.py input.jpg output.jpg
python tools/test_nv_sim.py
```

Keep both files in sync by hand.

## Build

The repo has no Gradle wrapper script; use Gradle 8.7 or newer:

```
gradle assembleDebug
```

## Debug control

Debug builds accept commands while the app is open, and log results under the tag `NVCam`:

```
adb shell am start -n at.sturq.nvcam/.MainActivity --es action photo   # or video, flip
adb logcat -s NVCam
```

## License

[GPL-3.0-only](LICENSE)
