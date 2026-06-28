---
name: document-reader
description: "Use this skill whenever the user asks to read, parse, extract text from, summarize, analyze, compare, quote, translate, or inspect PDF/Word documents. Trigger when the user provides or mentions local files with extensions .pdf, .docx, .doc, .rtf, .odt, .txt, .md, or says PDF, Word, DOCX, 文档, 论文, 报告, 方案, 合同, 简历, 手册, 说明书, 提取文字, 读取文件, 总结文档, 分析文档, 对比文档. Also use when the built-in Read tool fails on PDF/DOCX or reports missing pdftoppm/pdftotext/binary file errors."
---

# Document Reader Skill

## 触发条件

必须使用本 skill 的情况：

- 用户给出或提到本地文档路径，扩展名包括：`.pdf`、`.docx`、`.doc`、`.rtf`、`.odt`、`.txt`、`.md`。
- 用户要求读取、解析、提取、总结、翻译、审阅、对比、引用、检查文档内容。
- 用户使用这些关键词：PDF、Word、DOCX、DOC、文档、论文、报告、方案、合同、简历、手册、说明书、提取文字、读取文件、总结文档、分析文档、对比文档。
- Claude 内置 `Read` 工具读取 PDF/DOCX 失败，尤其是出现：
  - `pdftoppm failed`
  - `pdftotext not found`
  - `Command 'pdftoppm' not found`
  - `cannot read binary files`
  - `binary .docx file`

不必使用本 skill 的情况：

- 用户只是讨论文档格式概念，没有给文件、也没有要求读取具体内容。
- `.pptx` 文件应优先使用 `pptx` skill。
- 图片截图 OCR 不属于本 skill，除非图片已嵌在 DOCX/PDF 中且用户只要求可提取文本。

## 核心脚本

| 脚本 | 用途 |
|------|------|
| `scripts/read_document.py` | 将 PDF/DOCX/DOC/RTF/ODT/TXT/MD 提取为纯文本或 Markdown |

## 推荐用法

始终用绝对路径，并用双引号包裹路径。

```bash
python "C:/Users/lenovo/.claude/skills/document-reader/scripts/read_document.py" "C:/path/to/file.pdf"
```

指定输出到文本文件：

```bash
python "C:/Users/lenovo/.claude/skills/document-reader/scripts/read_document.py" "C:/path/to/file.docx" --output "C:/path/to/file.extracted.md"
```

限制最大输出字符数，避免超长文档刷屏：

```bash
python "C:/Users/lenovo/.claude/skills/document-reader/scripts/read_document.py" "C:/path/to/file.pdf" --max-chars 60000
```

## 读取策略

### PDF

脚本按顺序尝试：

1. `pdftotext`，来自 Poppler，推荐全局安装。
2. Python 库 `pypdf`。
3. Python 库 `PyPDF2`。
4. 若都不可用，输出明确安装建议。

推荐全局安装：

```bash
winget install oschwartz10612.Poppler
```

安装后新终端应能运行：

```bash
pdftotext -v
pdftoppm -v
```

### DOCX

脚本按顺序尝试：

1. `pandoc` 转 Markdown。
2. Python 标准库直接解包 `.docx`，读取 `word/document.xml`、页眉、页脚、脚注、尾注中的文本。

推荐全局安装：

```bash
winget install JohnMacFarlane.Pandoc
```

### DOC/RTF/ODT

脚本按顺序尝试：

1. `pandoc`。
2. LibreOffice `soffice` 无界面转换。
3. 若都不可用，提示安装依赖或让用户转成 `.docx`/`.pdf`。

推荐全局安装 LibreOffice 作为复杂 Word 文件兜底：

```bash
winget install TheDocumentFoundation.LibreOffice
```

## 工作流程

1. 如果用户只问“能不能读取”，先用本脚本快速验证，不要长篇解释。
2. 如果用户要求分析内容，先提取到临时 `.txt`/`.md` 文件，再用 `Read` 分段读取。
3. 对大型 PDF/DOCX，优先使用 `--output` 保存提取结果，再按需读取部分内容。
4. 遇到扫描版 PDF 时，说明当前脚本只能提取文本层；需要 OCR 才能读取图片文字。

## 示例

```bash
python "C:/Users/lenovo/.claude/skills/document-reader/scripts/read_document.py" "C:/Users/lenovo/Desktop/水下重力匹配方案6.15/张锦柏 等 - 2025 - 一种粗精匹配结合的重力辅助惯性导航算法.pdf" --output "C:/Users/lenovo/Desktop/水下重力匹配方案6.15/paper.extracted.txt"
```

```bash
python "C:/Users/lenovo/.claude/skills/document-reader/scripts/read_document.py" "C:/Users/lenovo/Desktop/水下重力匹配方案6.15/重力匹配惯导组合导航研究方案第四版.docx" --output "C:/Users/lenovo/Desktop/水下重力匹配方案6.15/proposal.extracted.md"
```
