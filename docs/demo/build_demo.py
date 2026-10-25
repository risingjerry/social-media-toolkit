#!/usr/bin/env python3
"""Scenes for docs/demo.gif (synthetic data only). Rebuild: python3 docs/demo/build_demo.py"""
from engine import main

J = "json"
URL = "https://youtu.be/demoVid0001"

SCENES = [
    {
        "caption": "<b>1</b> &nbsp;Paste a public share link, get normalized JSON",
        "steps": [
            ("cmd", [f'socialkit inspect "{URL}"'], 0.5),
            ("out", [(l, J) for l in [
                "{",
                '  "source": {',
                '    "platform": "youtube",',
                '    "content_type": "video",',
                f'    "original_url": "{URL}",',
                '    "post_id": "demoVid0001", ...',
                "  },",
                '  "post": {',
                '    "title": "Example Talk: Building Agent Tools",',
                '    "duration_sec": 754, ...',
                "  },",
                '  "author": { "id": "UCexample", "name": "Example Channel", ... },',
                '  "media": { "covers": [ { "type": "cover", "primary": true, ... } ], ... },',
                '  "metrics": { "views": 1200, "likes": 88 },',
                '  "provenance": {',
                '    "quality": "metadata_only",',
                '    "routes": ["platform:youtube"],',
                '    "warnings": []',
                "  },",
                '  "schema_version": "1.0"',
                "}",
            ]], 3.6),
        ],
    },
    {
        "caption": "<b>2</b> &nbsp;Timed transcript with source timecodes (md + srt)",
        "steps": [
            ("cmd", [f'socialkit text "{URL}" \\', '  --timed --output ./transcripts --outputs md,srt'], 0.5),
            ("out", [(l, J) for l in [
                "{",
                '  "status": "success",',
                '  "provider": "platform_subtitle",',
                '  "duration_ms": 754000,',
                '  "timing_precision": "caption_cue",',
                '  "segment_count": 214,',
                '  "artifacts": [',
                '    { "kind": "md",  "path": ".../youtube-demoVid0001-transcript.md",  ... },',
                '    { "kind": "srt", "path": ".../youtube-demoVid0001-transcript.srt", ... }',
                "  ],",
                '  "temporary_media": "not_created",',
                "  ...",
                "}",
            ]], 2.2),
            ("cmd", ["head -n 7 transcripts/youtube-demoVid0001-transcript.srt"], 0.4),
            ("out", [(l, "c") for l in [
                "1",
                "00:00:00,000 --> 00:00:04,200",
                "Welcome. Today we build a small agent tool.",
                "",
                "2",
                "00:00:04,200 --> 00:00:09,100",
                "First, one command turns a link into JSON.",
            ]], 4.2),
        ],
    },
]

if __name__ == "__main__":
    main(SCENES)
