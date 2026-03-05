# excalidraw-export-skill

[中文文档](README.zh.md)

Generate Excalidraw diagrams from natural language and export to PNG/SVG images, end-to-end.

| Feature | Detail |
|---------|--------|
| Input | Natural language description |
| Output | PNG image, SVG image, .excalidraw source |
| Diagram types | Flowchart, architecture, mind map, sequence, ER, class, swimlane, DFD |
| Rendering | [kroki.io](https://kroki.io) (open-source) |
| PNG conversion | Chrome headless (recommended), resvg, rsvg-convert, or cairosvg |

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
- Google Chrome (recommended for PNG with perfect hand-drawn font rendering)
- Internet access (kroki.io for SVG rendering)
- Fallback PNG backends: `brew install resvg` or `brew install librsvg` or `pip install cairosvg`

Run the setup script to check:

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
  Chrome headless -> PNG (2x retina, perfect font rendering)
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
- Chrome headless required for perfect hand-drawn fonts (Excalifont + Xiaolai for CJK); fallback backends lose hand-drawn style
- Max ~20 elements per diagram for readability

## License

MIT
