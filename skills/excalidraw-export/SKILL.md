---
name: excalidraw-export
description: "Generate Excalidraw diagrams and export to PNG/SVG images. Use when asked to 'create a diagram', 'draw a flowchart', 'visualize architecture', 'make a mind map', 'generate excalidraw', 'export diagram to png', 'diagram to image'. Supports flowcharts, relationship diagrams, mind maps, architecture diagrams, sequence diagrams, ER diagrams, and more. End-to-end: natural language -> .excalidraw JSON -> PNG/SVG image. Trigger: 'excalidraw', 'diagram', 'flowchart', 'visualize', 'architecture diagram', '画图', '流程图', '架构图', '思维导图', '导出图片'."
---

# Excalidraw Export

Generate Excalidraw diagrams from natural language and export them as PNG/SVG images, end-to-end.

## Language

**Match user's language**: Respond in the same language the user uses.

## End-to-End Workflow

Progress:
- [ ] Step 1: Understand the request
- [ ] Step 2: Generate .excalidraw JSON
- [ ] Step 3: Export to PNG/SVG
- [ ] Step 4: Deliver result

## Prerequisites

On first use, run the setup script to check dependencies:

```bash
bash <SKILL_DIR>/scripts/setup.sh
```

Required:
- Python 3.8+
- Google Chrome (for PNG with perfect hand-drawn font rendering)
- Internet access (uses kroki.io for rendering)

Fallback PNG backends (if Chrome unavailable):
- `resvg` (`brew install resvg`) — loses hand-drawn fonts, uses system fonts
- `rsvg-convert` (`brew install librsvg`)
- `cairosvg` (`pip install cairosvg`) — may show CJK as boxes

If only SVG output is needed, no extra tools are required.

Run preflight to verify all dependencies programmatically:

```bash
python3 <SKILL_DIR>/scripts/export.py --preflight
```

### Step 1: Understand the Request

Determine:
1. **Diagram type**: flowchart, relationship, mind map, architecture, sequence, ER, class, swimlane, data flow
2. **Key elements**: entities, steps, concepts
3. **Relationships**: flow direction, connections, hierarchy

### Step 2: Generate .excalidraw JSON

Create a valid `.excalidraw` file following the schema. Read the reference docs for details:

- Read `<SKILL_DIR>/references/excalidraw-schema.md` for the JSON schema
- Read `<SKILL_DIR>/references/element-types.md` for element specifications

**Critical rules:**
- All text elements MUST use `fontFamily: 5` (Excalifont) for the hand-drawn style. This is excalidraw's current default font. kroki.io will auto-embed Excalifont (hand-drawn Latin) + Xiaolai (hand-drawn CJK) as woff2. Chrome headless renders both perfectly.
- `fontFamily: 1` (Virgil) is **deprecated** — kroki will NOT embed Xiaolai for it, causing CJK to fall back to system fonts
- Only use `fontFamily: 3` (Cascadia) for code identifiers / monospace text
- All IDs must be unique
- Keep element count under 20 for clarity
- Use consistent spacing: 200-300px horizontal, 100-150px vertical

**Color palette:**
| Role | Color |
|------|-------|
| Primary entities | `#a5d8ff` (light blue) |
| Process steps | `#b2f2bb` (light green) |
| Important/central | `#ffd43b` (yellow) |
| Warnings/errors | `#ffc9c9` (light red) |
| Default stroke | `#1e1e1e` |

**File structure:**
```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "https://excalidraw.com",
  "elements": [],
  "appState": {
    "viewBackgroundColor": "#ffffff",
    "gridSize": 20
  },
  "files": {}
}
```

Save the file as `<descriptive-name>.excalidraw`.

### Step 3: Export to PNG/SVG

Run the export script to convert the .excalidraw file to an image:

```bash
# Export to PNG (default, 2x resolution for retina)
python3 <SKILL_DIR>/scripts/export.py <file>.excalidraw

# Export to SVG
python3 <SKILL_DIR>/scripts/export.py <file>.excalidraw -f svg

# Export both PNG and SVG
python3 <SKILL_DIR>/scripts/export.py <file>.excalidraw -f png -f svg

# Custom output path
python3 <SKILL_DIR>/scripts/export.py <file>.excalidraw -o output.png

# Higher resolution (3x)
python3 <SKILL_DIR>/scripts/export.py <file>.excalidraw --scale 3

# Dark theme
python3 <SKILL_DIR>/scripts/export.py <file>.excalidraw --dark
```

### Step 4: Deliver Result

Always provide:
1. The exported image file (PNG or SVG)
2. The source `.excalidraw` file (for future editing)
3. Brief summary of what was created

**Example delivery:**
```
Created: system-architecture.png (86 KB)
Source:  system-architecture.excalidraw
Type:    Architecture diagram
Elements: 8 rectangles, 7 arrows, 1 title

The .excalidraw file can be edited at https://excalidraw.com or with the VS Code Excalidraw extension.
```

## Diagram Type Guide

| User Intent | Type | Keywords |
|-------------|------|----------|
| Sequential process | Flowchart | "workflow", "process", "steps" |
| Entity connections | Relationship | "relationship", "dependencies" |
| Concept hierarchy | Mind Map | "mind map", "concepts", "ideas" |
| System components | Architecture | "architecture", "system", "modules" |
| Data movement | Data Flow (DFD) | "data flow", "data processing" |
| Cross-functional | Swimlane | "business process", "actors" |
| OOP design | Class Diagram | "class", "inheritance", "OOP" |
| Message flow | Sequence | "sequence", "interaction", "timeline" |
| Database design | ER Diagram | "database", "entity", "data model" |

## Error Handling

| Issue | Solution |
|-------|----------|
| kroki.io unreachable | Check internet; output .excalidraw only, inform user to export manually |
| cairosvg not installed | Fall back to SVG output; suggest `pip install cairosvg` |
| CJK text shows as boxes | Ensure Chrome headless is used (not cairosvg); use `fontFamily: 5` so kroki embeds Xiaolai |
| Elements overlap | Increase spacing; use 200-300px horizontal gap |
| Too many elements | Break into multiple diagrams; suggest high-level + detail views |

## PNG Backend Degradation

| Backend | Hand-drawn English | Hand-drawn CJK | Notes |
|---------|---|---|---|
| Chrome headless | ✅ Excalifont | ✅ Xiaolai | Perfect woff2 rendering |
| resvg | ❌ System font | ❌ System font | Ignores @font-face |
| rsvg-convert | ❌ System font | ❌ System font | Ignores @font-face |
| cairosvg | ❌ System font | ❌ Boxes | Cannot render woff2 |

If Chrome is unavailable, inform the user that hand-drawn fonts will be lost and offer SVG-only output as an alternative.

## Limitations

- Requires internet access (kroki.io for SVG rendering)
- CJK requires Chrome headless for perfect rendering (resvg/cairosvg may have font issues)
- Maximum recommended: 20 elements per diagram
- No embedded image support in auto-generation
- Hand-drawn roughness uses default settings
