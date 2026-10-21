# HyperFrames skill for Claude Code (Android + FreeLLMAPI)

**Source:** https://github.com/heygen-com/hyperframes

**User-requested installation:** \`npx skills add heygen-com/hyperframes\`.

HyperFrames provides agent guidance for composing and rendering videos from HTML, animations, captions and media. Installing its skill does **not** create a video, activate a paid HeyGen subscription, or connect a HeyGen account.

## How installation is adapted to our free cloud runner

A GitHub Actions runner is temporary. One-time shell installations disappear when the job finishes. The reusable composite action at \`.github/actions/setup-hyperframes/action.yml\` provides an installation step that any FUTURE Claude Code video workflow can use:

\`\`\`yaml
- uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1
- uses: ./.github/actions/setup-hyperframes
\`\`\`

It uses Node.js 22, installs the free FFmpeg package on the temporary Ubuntu runner if missing, and installs the **HyperFrames router skill only**, non-interactively and only for Claude Code:

\`\`\`bash
npx --yes skills add heygen-com/hyperframes --skill hyperframes --agent claude-code --yes
\`\`\`

The interactive form supplied by the user starts a picker; \`--skill hyperframes\` avoids silently installing every published skill on a non-interactive server. To add the **recommended core set** later, in a separate approved video workflow use \`npx hyperframes skills update\` (the project maintainers' documented non-interactive method).

The verification workflow \`.github/workflows/hyperframes-skill-verify.yml\` checks that the installer actually puts a nonempty \`.claude/skills/hyperframes/SKILL.md\` into the checkout, verifies Node.js, the installed FFmpeg package and authentic Claude Code, and ensures it did not change tracked application source. No API keys, paid services or model queries are needed for this check. No PR merge or Render deploy is performed by the installer.

## Important limitation of the current Claude Code automation

Our audited FreeLLMAPI bridge currently uses \`claude --bare\` with **only Read/Edit** in one source file. Bare mode skips ordinary skill discovery and the bridge cannot create/render video assets. **Do not change that restricted agent into an unrestricted video renderer.**

When the user requests a video, the next approved stage is a NEW, independent opt-in video workflow that calls the setup action, enables ONLY the required skill discovery in a controlled directory, and installs the rendering dependencies (including FFmpeg/browser) in an isolated ephemeral runner. A first short clip must be generated and the resulting MP4 verified before claiming working video production.

## Privacy and expenses

- No desktop computer is needed; GitHub Actions supplies the temporary cloud environment.
- No HeyGen API key is configured. The skill/framework is open source, but some optional media-generation, text-to-speech or external services may require payment and must never be activated without explicit approval.
- Public GitHub Actions repositories and free Groq quotas have execution/resource limits. Zero cost and unlimited availability cannot be guaranteed forever.
- \`DISABLE_TELEMETRY=1\` and \`HYPERFRAMES_NO_TELEMETRY=1\` disable the installers' documented telemetry where supported.
- Skills are third-party instructions/code. Review their content before granting them more permissions; do not give them project credentials.
