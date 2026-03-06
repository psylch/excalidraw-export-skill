# excalidraw-export-skill

[English](README.md)

自然语言生成 Excalidraw 图表，端到端导出为 PNG/SVG 图片。

| 特性 | 说明 |
|------|------|
| 输入 | 自然语言描述 |
| 输出 | PNG 图片、SVG 图片、.excalidraw 源文件 |
| 图表类型 | 流程图、架构图、思维导图、时序图、ER 图、类图、泳道图、数据流图 |
| 渲染引擎 | [kroki.io](https://kroki.io)（开源） |
| PNG 转换 | text-to-path + resvg（推荐）、Chrome headless（备选） |

## 安装

### 通过 skills.sh（推荐）

```bash
npx skills add psylch/excalidraw-export-skill -g -y
```

### 通过 Plugin Marketplace

```
/plugin marketplace add psylch/excalidraw-export-skill
/plugin install excalidraw-export@psylch-excalidraw-export-skill
```

### 手动安装

```bash
git clone https://github.com/psylch/excalidraw-export-skill.git
cp -r excalidraw-export-skill/skills/excalidraw-export ~/.claude/skills/
```

安装后重启 Claude Code。

## 前置条件

- Python 3.8+
- `resvg` — 高性能 SVG 转 PNG 光栅化器（`brew install resvg`）
- `fonttools` + `brotli` — 提取内嵌字体，将文字转为路径（`pip install fonttools brotli`）
- 网络连接（kroki.io 用于 SVG 渲染）
- Google Chrome — 可选备选方案（安装了 resvg + fonttools 则不需要）

运行检查脚本（自动安装缺失依赖）：

```bash
bash ~/.agents/skills/excalidraw-export/scripts/setup.sh
```

## 使用方式

直接让 Claude 画图：

- "画一个用户注册流程图"
- "画微服务架构图"
- "画 User、Post、Comment 的关系图"
- "做一个机器学习的思维导图"
- "Create a flowchart for user login"
- "Draw system architecture diagram"

Skill 会自动生成图表并导出为 PNG 图片。

## 工作原理

```
用户描述
  |
  v
生成 .excalidraw JSON（Claude）
  |
  v
kroki.io API -> SVG（内嵌 Excalifont + Xiaolai woff2 字体）
  |
  v
fonttools 提取 woff2 字形 -> <text> 转换为 <path>
  |
  v
resvg -> PNG（2x 视网膜分辨率，手绘字体完美保留）
  |
  v
交付：.png + .excalidraw 源文件
```

## 已知限制

- 需要网络连接（kroki.io 在服务端渲染 SVG）
- 建议每张图不超过 20 个元素

## 许可证

MIT
