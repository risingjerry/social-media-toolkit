---
name: social-media-toolkit
description: Extract public Douyin (抖音), Xiaohongshu (小红书 / RedNote), Bilibili (B站) and YouTube links into normalized JSON metadata, readable text, timed transcripts (MD/SRT/JSON), media downloads and public comment samples via the `socialkit` CLI or MCP server. Use when the user pastes a share link from these platforms and wants the title, caption, transcript, subtitles, video/cover/images, or comments; says "get the text of this video", "transcribe this YouTube video", "提取视频文案", "下载抖音视频", "抓取评论"; or wants an agent to read social posts without a browser or login.
---

# Social Media Toolkit

`socialkit` turns public social-media URLs into one normalized, provenance-bearing JSON result. Public reads need no browser, cookies, or login.

## First contact

```bash
socialkit doctor        # JSON: installed capabilities, missing optional setup (names only, never values)
```

If `socialkit` is missing (needs Node.js 18+):

```bash
npx -y github:risingjerry/social-media-toolkit
```

`doctor` may report `"status": "partial"`: the free public path works; the warnings list optional text/ASR pieces that are not configured. Do not treat `partial` as failure.

MCP alternative: run `social-media-toolkit-mcp` (stdio) and register it in the client as command `social-media-toolkit-mcp`. Tools: `social_inspect`, `social_get_text`, `social_get_comments`, `social_download`, `social_capture_bundle`, `social_doctor`. Same logic as the CLI.

## Mental model

- Every command prints one JSON object on stdout. Exit code is 1 when `status` is `error`/`failed`, otherwise 0.
- Supported: Douyin, Xiaohongshu, Bilibili, YouTube. Public URLs only.
- `inspect` is the safe default: no persistent files, no GetNote, no ASR.
- Results carry `provenance` and `warnings`; report the route used and any cost warning to the user.

## Safety rules

- Secrets come only from process environment or the client's secret store: `TIKHUB_API_KEY` (optional Douyin fallback), `VOLCENGINE_ASR_API_KEY`, `TOS_ACCESS_KEY`, `TOS_SECRET_KEY`. Never ask the user to paste a key into chat, never print one, never write a `.env` file.
- `text` (and `capture` unless `--no-text`) runs the configured text route: GetNote original content, then native subtitle/body, then Volcengine cloud ASR. These can cost money or save the URL to the user's GetNote account. Run it when the user asked for text, then tell them which route ran.
- Persistent files are written only to an explicit `--output` directory. Use a directory the user named or an obvious scratch directory.
- Comments are a bounded public sample (Douyin only), not a platform ranking.
- Publishing or posting to social accounts is out of scope.
- If a platform blocks or changes, report the error; do not switch to browser automation or cookies.

## Recipes

```bash
# 1. Metadata and media manifest (safe)
socialkit inspect "SHARE_URL"

# 2. Readable text of a post or video
socialkit text "SHARE_URL"

# 3. YouTube transcript with timecodes (needs --output)
socialkit text "YOUTUBE_URL" --timed --output ./transcripts --outputs md,srt,json

# 4. Ignore captions, run timed ASR with anonymous speaker labels
socialkit text "YOUTUBE_URL" --timed --force-asr --speaker-info --output ./transcripts

# 5. Douyin public comments, top 20 by likes (--limit 1-100, --sort likes|recent)
socialkit comments "DOUYIN_URL" --sort likes --limit 20

# 6. Download media (--include video,cover,images)
socialkit download "SHARE_URL" --include video,cover,images --output ./downloads

# 7. One bundle: metadata + text + comments + media
socialkit capture "SHARE_URL" --comments --comment-limit 20 --media video,cover --output ./capture
socialkit capture "SHARE_URL" --no-text      # skip the text route
```

Key fields to read: `source.platform`, `post.title`, `media.*`, `content`, `comments`, `provenance.routes`, `warnings`.

## Errors

- `status: error` with a message about a platform parse failure: the public page changed or blocked the request; retry once, then tell the user.
- Missing ASR/TOS configuration in `warnings` or the error: tell the user which secret *names* to set in their environment; do not guess values.
- `--timed` without `--output`, or `--speaker-info` without `--force-asr`: fix the flags.
- Media over 5 hours is rejected before download; there is no automatic chunking.

## More

Full reference: `README.md`, `docs/capabilities.md`, `docs/architecture.md` in https://github.com/risingjerry/social-media-toolkit.
