# Excalidraw Element Types Guide

Detailed specifications for each Excalidraw element type with visual examples and use cases.

## Element Type Overview

| Type | Visual | Primary Use | Text Support |
|------|--------|-------------|--------------|
| `rectangle` | □ | Boxes, containers, process steps | ✅ Via bound text element |
| `ellipse` | ○ | Emphasis, terminals, states | ✅ Via bound text element |
| `diamond` | ◇ | Decision points, choices | ✅ Via bound text element |
| `arrow` | → | Directional flow, relationships | ❌ No (use separate text) |
| `line` | — | Connections, dividers | ❌ No |
| `text` | A | Labels, annotations, titles | ✅ (Its purpose) |

### How Text Inside Shapes Works

Text inside shapes requires **two elements**: the shape + a bound text element.

The shape lists the text in `boundElements`, and the text element has `containerId` pointing back:

```json
[
  {"id": "s1", "type": "rectangle", "boundElements": [{"id": "s1-text", "type": "text"}], "...": "..."},
  {"id": "s1-text", "type": "text", "containerId": "s1", "text": "Label", "originalText": "Label", "autoResize": true, "lineHeight": 1.25, "...": "..."}
]
```

See `excalidraw-schema.md` → "Text Inside Shapes" for full details and positioning formula.

---

## Rectangle

**Best for:** Process steps, entities, data stores, components

### Properties

```typescript
{
  type: "rectangle",
  roundness: { type: 3 },  // Rounded corners
  boundElements: [{ id: "textId", type: "text" }]  // Link to bound text
}
```

### Use Cases

| Scenario | Configuration |
|----------|---------------|
| **Process step** | Green background (`#b2f2bb`), centered text |
| **Entity/Object** | Blue background (`#a5d8ff`), medium size |
| **System component** | Light color, descriptive text |
| **Data store** | Gray/white, database-like label |

### Size Guidelines

| Content | Width | Height |
|---------|-------|--------|
| Single word | 120-150px | 60-80px |
| Short phrase (2-4 words) | 180-220px | 80-100px |
| Sentence | 250-300px | 100-120px |

### Example

```json
[
  {
    "id": "step1",
    "type": "rectangle",
    "x": 100,
    "y": 100,
    "width": 200,
    "height": 80,
    "backgroundColor": "#b2f2bb",
    "roundness": { "type": 3 },
    "boundElements": [{"id": "step1-text", "type": "text"}]
  },
  {
    "id": "step1-text",
    "type": "text",
    "x": 121,
    "y": 115,
    "width": 158,
    "height": 25,
    "text": "Validate Input",
    "fontSize": 20,
    "fontFamily": 5,
    "textAlign": "center",
    "verticalAlign": "middle",
    "containerId": "step1",
    "originalText": "Validate Input",
    "autoResize": true,
    "lineHeight": 1.25
  }
]
```

---

## Ellipse

**Best for:** Start/end points, states, emphasis circles

### Properties

```typescript
{
  type: "ellipse",
  boundElements: [{ id: "textId", type: "text" }]
}
```

### Use Cases

| Scenario | Configuration |
|----------|---------------|
| **Flow start** | Light green, "Start" text |
| **Flow end** | Light red, "End" text |
| **State** | Soft color, state name |
| **Highlight** | Bright color, emphasis text |

### Size Guidelines

For circular shapes, use `width === height`:

| Content | Diameter |
|---------|----------|
| Icon/Symbol | 60-80px |
| Short text | 100-120px |
| Longer text | 150-180px |

### Example

```json
[
  {
    "id": "start1",
    "type": "ellipse",
    "x": 100,
    "y": 100,
    "width": 120,
    "height": 120,
    "backgroundColor": "#d0f0c0",
    "boundElements": [{"id": "start1-text", "type": "text"}]
  },
  {
    "id": "start1-text",
    "type": "text",
    "x": 127,
    "y": 136,
    "width": 65,
    "height": 23,
    "text": "Start",
    "fontSize": 18,
    "fontFamily": 5,
    "textAlign": "center",
    "verticalAlign": "middle",
    "containerId": "start1",
    "originalText": "Start",
    "autoResize": true,
    "lineHeight": 1.25
  }
]
```

---

## Diamond

**Best for:** Decision points, conditional branches

### Properties

```typescript
{
  type: "diamond",
  boundElements: [{ id: "textId", type: "text" }]
}
```

### Use Cases

| Scenario | Text Example |
|----------|--------------|
| **Yes/No decision** | "Is Valid?", "Exists?" |
| **Multiple choice** | "Type?", "Status?" |
| **Conditional** | "Score > 50?" |

### Size Guidelines

Diamonds need more space than rectangles for the same text:

| Content | Width | Height |
|---------|-------|--------|
| Yes/No | 120-140px | 120-140px |
| Short question | 160-180px | 160-180px |
| Longer question | 200-220px | 200-220px |

### Example

```json
[
  {
    "id": "decision1",
    "type": "diamond",
    "x": 100,
    "y": 100,
    "width": 150,
    "height": 150,
    "backgroundColor": "#ffe4a3",
    "boundElements": [{"id": "decision1-text", "type": "text"}]
  },
  {
    "id": "decision1-text",
    "type": "text",
    "x": 127,
    "y": 152,
    "width": 65,
    "height": 23,
    "text": "Valid?",
    "fontSize": 18,
    "fontFamily": 5,
    "textAlign": "center",
    "verticalAlign": "middle",
    "containerId": "decision1",
    "originalText": "Valid?",
    "autoResize": true,
    "lineHeight": 1.25
  }
]
```

---

## Arrow

**Best for:** Flow direction, relationships, dependencies

### Properties

```typescript
{
  type: "arrow",
  points: [[0, 0], [endX, endY]],  // Relative coordinates
  roundness: { type: 2 },          // Curved
  startBinding: null,              // Or { elementId, focus, gap }
  endBinding: null
}
```

### Arrow Directions

#### Horizontal (Left to Right)

```json
{
  "x": 100,
  "y": 150,
  "width": 200,
  "height": 0,
  "points": [[0, 0], [200, 0]]
}
```

#### Vertical (Top to Bottom)

```json
{
  "x": 200,
  "y": 100,
  "width": 0,
  "height": 150,
  "points": [[0, 0], [0, 150]]
}
```

#### Diagonal

```json
{
  "x": 100,
  "y": 100,
  "width": 200,
  "height": 150,
  "points": [[0, 0], [200, 150]]
}
```

### Arrow Styles

| Style | `strokeStyle` | `strokeWidth` | Use Case |
|-------|---------------|---------------|----------|
| **Normal flow** | `"solid"` | 2 | Standard connections |
| **Optional/Weak** | `"dashed"` | 2 | Optional paths |
| **Important** | `"solid"` | 3-4 | Emphasized flow |
| **Dotted** | `"dotted"` | 2 | Indirect relationships |

### Adding Arrow Labels

Use separate text elements positioned near arrow midpoint:

```json
[
  {
    "type": "arrow",
    "id": "arrow1",
    "x": 100,
    "y": 150,
    "points": [[0, 0], [200, 0]]
  },
  {
    "type": "text",
    "x": 180,      // Near midpoint
    "y": 130,      // Above arrow
    "text": "sends",
    "fontSize": 14
  }
]
```

---

## Line

**Best for:** Non-directional connections, dividers, borders

### Properties

```typescript
{
  type: "line",
  points: [[0, 0], [x2, y2], [x3, y3], ...],
  roundness: null  // Or { type: 2 } for curved
}
```

### Use Cases

| Scenario | Configuration |
|----------|---------------|
| **Divider** | Horizontal, thin stroke |
| **Border** | Closed path (polygon) |
| **Connection** | Multi-point path |
| **Underline** | Short horizontal line |

### Multi-Point Line Example

```json
{
  "type": "line",
  "x": 100,
  "y": 100,
  "points": [
    [0, 0],
    [100, 50],
    [200, 0]
  ]
}
```

---

## Text

**Best for:** Labels, titles, annotations, standalone text

### Properties

```typescript
{
  type: "text",
  text: "Label text",
  fontSize: 20,
  fontFamily: 5,        // 5=Excalifont (default), 3=Cascadia (code)
  textAlign: "left",
  verticalAlign: "top"
}
```

### Font Sizes by Purpose

| Purpose | Font Size |
|---------|-----------|
| **Main title** | 28-36 |
| **Section header** | 24-28 |
| **Element label** | 18-22 |
| **Annotation** | 14-16 |
| **Small note** | 12-14 |

### Width/Height Calculation

```javascript
// Approximate width
const width = text.length * fontSize * 0.6;

// Approximate height (single line)
const height = fontSize * 1.2;

// Multi-line
const lines = text.split('\n').length;
const height = fontSize * 1.2 * lines;
```

### Text Positioning

| Position | textAlign | verticalAlign | Use Case |
|----------|-----------|---------------|----------|
| **Top-left** | `"left"` | `"top"` | Default labels |
| **Centered** | `"center"` | `"middle"` | Titles |
| **Bottom-right** | `"right"` | `"bottom"` | Footnotes |

### Example: Title

```json
{
  "type": "text",
  "x": 100,
  "y": 50,
  "width": 400,
  "height": 40,
  "text": "System Architecture",
  "fontSize": 32,
  "fontFamily": 2,
  "textAlign": "center",
  "verticalAlign": "top"
}
```

### Example: Annotation

```json
{
  "type": "text",
  "x": 150,
  "y": 200,
  "width": 100,
  "height": 20,
  "text": "User input",
  "fontSize": 14,
  "fontFamily": 5,
  "textAlign": "left",
  "verticalAlign": "top"
}
```

---

## Combining Elements

### Pattern: Labeled Box

```json
[
  {
    "id": "box1",
    "type": "rectangle",
    "x": 100, "y": 100, "width": 200, "height": 100,
    "boundElements": [{"id": "box1-text", "type": "text"}]
  },
  {
    "id": "box1-text",
    "type": "text",
    "x": 130, "y": 125, "width": 140, "height": 25,
    "text": "Component",
    "fontSize": 20, "fontFamily": 5,
    "textAlign": "center", "verticalAlign": "middle",
    "containerId": "box1", "originalText": "Component",
    "autoResize": true, "lineHeight": 1.25
  }
]
```

### Pattern: Connected Boxes

```json
[
  {
    "id": "box1",
    "type": "rectangle",
    "x": 100, "y": 100, "width": 150, "height": 80,
    "boundElements": [{"id": "box1-text", "type": "text"}]
  },
  {
    "id": "box1-text",
    "type": "text",
    "x": 130, "y": 115, "width": 90, "height": 25,
    "text": "Step 1",
    "fontSize": 20, "fontFamily": 5,
    "textAlign": "center", "verticalAlign": "middle",
    "containerId": "box1", "originalText": "Step 1",
    "autoResize": true, "lineHeight": 1.25
  },
  {
    "id": "arrow1",
    "type": "arrow",
    "x": 250, "y": 140,
    "points": [[0, 0], [100, 0]]
  },
  {
    "id": "box2",
    "type": "rectangle",
    "x": 350, "y": 100, "width": 150, "height": 80,
    "boundElements": [{"id": "box2-text", "type": "text"}]
  },
  {
    "id": "box2-text",
    "type": "text",
    "x": 380, "y": 115, "width": 90, "height": 25,
    "text": "Step 2",
    "fontSize": 20, "fontFamily": 5,
    "textAlign": "center", "verticalAlign": "middle",
    "containerId": "box2", "originalText": "Step 2",
    "autoResize": true, "lineHeight": 1.25
  }
]
```

### Pattern: Decision Tree

```json
[
  {
    "id": "decision",
    "type": "diamond",
    "x": 100, "y": 100, "width": 140, "height": 140,
    "boundElements": [{"id": "decision-text", "type": "text"}]
  },
  {
    "id": "decision-text",
    "type": "text",
    "x": 131, "y": 148, "width": 78, "height": 23,
    "text": "Valid?",
    "fontSize": 18, "fontFamily": 5,
    "textAlign": "center", "verticalAlign": "middle",
    "containerId": "decision", "originalText": "Valid?",
    "autoResize": true, "lineHeight": 1.25
  },
  {
    "id": "yes-arrow",
    "type": "arrow",
    "x": 240, "y": 170,
    "points": [[0, 0], [60, 0]]
  },
  {
    "id": "yes-label",
    "type": "text",
    "x": 250, "y": 150,
    "text": "Yes",
    "fontSize": 14, "fontFamily": 5
  },
  {
    "id": "yes-box",
    "type": "rectangle",
    "x": 300, "y": 140, "width": 120, "height": 60,
    "boundElements": [{"id": "yes-box-text", "type": "text"}]
  },
  {
    "id": "yes-box-text",
    "type": "text",
    "x": 321, "y": 145, "width": 78, "height": 25,
    "text": "Process",
    "fontSize": 20, "fontFamily": 5,
    "textAlign": "center", "verticalAlign": "middle",
    "containerId": "yes-box", "originalText": "Process",
    "autoResize": true, "lineHeight": 1.25
  }
]
```

---

## Summary

| When you need... | Use this element |
|------------------|------------------|
| Process box | `rectangle` + bound `text` element |
| Decision point | `diamond` + bound `text` element |
| Flow direction | `arrow` |
| Start/End | `ellipse` |
| Title/Header | `text` (large font) |
| Annotation | `text` (small font) |
| Non-directional link | `line` |
| Divider | `line` (horizontal) |
