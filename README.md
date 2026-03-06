# excalidraw-export-skill

[中文文档](README.zh.md)

Generate Excalidraw diagrams from natural language and export to PNG/SVG images, end-to-end.

| Feature | Detail |
|---------|--------|
| Input | Natural language description |
| Output | PNG image, SVG image, .excalidraw source |
| Diagram types | Flowchart, architecture, mind map, sequence, ER, class, swimlane, DFD |
| Rendering | [kroki.io](https://kroki.io) (open-source) |
| PNG conversion | text-to-path + resvg (recommended), Chrome headless (fallback) |

## Installation

### Via skills.sh (recommended)

```bash
npx skills add psylch/excalidraw-export-skill -g -y
```

### Via Plugin Marketplace

```
/plugin marketplace add psylch/excalidraw-export-skill
/plugin install excalidraw-export@psylch-excalidraw-export-skill
```

### Manual Install

```bash
git clone https://github.com/psylch/excalidraw-export-skill.git
cp -r excalidraw-export-skill/skills/excalidraw-export ~/.claude/skills/
```

Restart Claude Code after installation.

## Prerequisites

- Python 3.8+
- `resvg` — fast SVG-to-PNG rasterizer (`brew install resvg`)
- `fonttools` + `brotli` — extracts embedded fonts, converts text to paths (`pip install fonttools brotli`)
- Internet access (kroki.io for SVG rendering)
- Google Chrome — optional fallback (not needed if resvg + fonttools installed)

Run the setup script to check and auto-install:

```bash
bash ~/.agents/skills/excalidraw-export/scripts/setup.sh
```

## Usage

Just ask Claude to create a diagram:

- "Create a flowchart for user registration"
- "Draw the system architecture of a microservice app"
- "Visualize the relationship between User, Post, and Comment"
- "Make a mind map about machine learning"
- "画一个登录流程图"
- "画架构图"

The skill will generate the diagram and automatically export it as a PNG image.

## How It Works

```
User description
       |
       v
  Generate .excalidraw JSON (Claude)
       |
       v
  kroki.io API -> SVG (with embedded Excalifont + Xiaolai woff2)
       |
       v
  fonttools extracts woff2 glyphs -> <text> converted to <path>
       |
       v
  resvg -> PNG (2x retina, hand-drawn fonts preserved)
       |
       v
  Delivered: .png + .excalidraw source
```

## File Structure

```
excalidraw-export-skill/
├── skills/
│   └── excalidraw-export/
│       ├── SKILL.md              # Skill definition
│       ├── scripts/
│       │   ├── export.py         # Export pipeline
│       │   └── setup.sh          # Dependency checker
│       └── references/
│           ├── excalidraw-schema.md
│           └── element-types.md
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json
├── README.md
├── README.zh.md
├── LICENSE
└── .gitignore
```

## Known Limitations

- Requires internet (kroki.io renders SVG server-side)
- Max ~20 elements per diagram for readability

## License

MIT
