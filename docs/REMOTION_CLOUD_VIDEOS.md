# Remotion Cloud Videos via ChatGPT / Claude Code

This is a bounded, free-tier-friendly video path that needs no continuously running PC.

## Submit from ChatGPT
A chat assistant with authorized GitHub repository access creates **one new JSON file**
under `.video-requests/video-YYYYMMDD-unique-slug.json` on the branch
`remotion-requests` with commit message beginning `remotion-video: `.

Example:

```json
{
  "title": "NUEVO VIDEO",
  "subtitle": "Movimiento real, cuadro por cuadro",
  "seconds": 6,
  "prompt": "Diseña tres escenas dinámicas sobre nuevas ideas y creatividad",
  "background": "#0b1020",
  "accent": "#76e8c7",
  "use_claude": true,
  "scenes": [
    {"heading": "IDEA", "caption": "Todo empieza con una idea"},
    {"heading": "MOVIMIENTO", "caption": "Damos vida a cada fotograma"},
    {"heading": "LISTO", "caption": "Tu MP4 para compartir"}
  ]
}
```

Only owner-authored requests are accepted. Each push may add exactly one JSON request file.
The workflow always runs reviewed code from `main`, parses the request as **data**, and
renders in GitHub Actions. The Claude Code CLI is installed with Remotion's official
plugin; when the free model gateway responds correctly, Claude creates scene text.
When unavailable or malformed, validated input scenes render deterministically.

## Get the video

Open GitHub Actions -> **Claude Code + Remotion - Cloud MP4 Videos** -> relevant run
-> **Artifacts** -> `remotion-mp4-RUN_ID` (a ZIP containing `video.mp4`).
Files are retained 7 days; no deployment or automatic social publishing occurs.
The assistant can find the run ID and give you its direct run page link in the chat.

## Limits and safety

- 720×1280 portrait video at 30 FPS; 3–15 seconds; H.264 MP4.
- Animated text and graphics only. No narration, imported images, audio, 3D Blender or
  editing of arbitrary external video. These require separately reviewed extensions.
- Output depends on GitHub Actions availability, repository free-tier minutes and
  available disk/CPU. No cost or timing guarantee. No paid Remotion cloud required.
- Untrusted requests cannot supply code, file paths, URLs, scripts or shell arguments.
- FreeLLMAPI credentials go only into the Claude step and never into render props or
  the downloadable artifact.
- Cloud runners are ephemeral; no PC and no permanent background service.
- The existing one-file ChatGPT-to-Claude PR bridge remains unchanged.
- A passing install smoke test does not prove every future render; verify each run.

## First-time setup
The authorized repo owner must have the workflow on `main`; create the
`remotion-requests` branch from that commit. Subsequent video requests are
GitHub file writes from chat (one file per commit); do not merge them into main.

Remotion license may require a commercial license above its free eligibility;
check official terms before scaling to team or large commercial usage.
