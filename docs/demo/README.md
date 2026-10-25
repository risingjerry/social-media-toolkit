# README demo GIF

`docs/demo.gif` is rendered from synthetic terminal frames; every URL, ID, title, and transcript line is fake. The command output shapes were checked against the real code (`PostBundle`, `write_timed_transcript_artifacts`) and abbreviated with `...`.

## Rebuild

Requires macOS Google Chrome, `ffmpeg`, and optionally `gifsicle`. (`vhs` is not used.)

```bash
python3 docs/demo/build_demo.py
```

Edit the scenes in `build_demo.py`; `engine.py` renders HTML frames, screenshots them with headless Chrome at 2x, and assembles the GIF with ffmpeg `palettegen`/`paletteuse`. Temporary frames are deleted afterwards.
