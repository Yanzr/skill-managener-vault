#!/usr/bin/env python3
"""Extract readable text from common document formats."""

from __future__ import annotations

import argparse
import html
import os
import shutil
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
import tempfile
import zipfile
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET


SUPPORTED = {".pdf", ".docx", ".doc", ".rtf", ".odt", ".txt", ".md", ".markdown"}


def run(cmd: list[str], timeout: int = 120) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    return subprocess.run(
        cmd,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        env=env,
    )


def read_text_file(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "gb18030", "gbk", "big5", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_bytes().decode("utf-8", errors="replace")


def extract_pdf(path: Path) -> tuple[str, str]:
    pdftotext = shutil.which("pdftotext")
    if pdftotext:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
            tmp_path = Path(tmp.name)
        try:
            result = run([pdftotext, "-layout", "-enc", "UTF-8", str(path), str(tmp_path)])
            if result.returncode == 0 and tmp_path.exists():
                text = read_text_file(tmp_path).strip()
                if text:
                    return text, "pdftotext"
            if result.stderr.strip():
                last_error = result.stderr.strip()
            else:
                last_error = "pdftotext returned no text"
        finally:
            try:
                tmp_path.unlink(missing_ok=True)
            except TypeError:
                if tmp_path.exists():
                    tmp_path.unlink()
    else:
        last_error = "pdftotext not found"

    for module_name in ("pypdf", "PyPDF2"):
        try:
            module = __import__(module_name)
            reader_cls = getattr(module, "PdfReader")
            reader = reader_cls(str(path))
            pages = []
            for page in reader.pages:
                pages.append(page.extract_text() or "")
            text = "\n\n".join(pages).strip()
            if text:
                return text, module_name
            last_error = f"{module_name} extracted no text"
        except Exception as exc:
            last_error = f"{module_name} failed: {exc}"

    raise RuntimeError(
        "无法读取 PDF 文本。最后错误："
        + last_error
        + "\n建议安装 Poppler：winget install oschwartz10612.Poppler；如果是扫描版 PDF，需要 OCR。"
    )


def extract_docx_via_zip(path: Path) -> tuple[str, str]:
    names = [
        "word/document.xml",
        "word/footnotes.xml",
        "word/endnotes.xml",
        "word/header1.xml",
        "word/header2.xml",
        "word/header3.xml",
        "word/footer1.xml",
        "word/footer2.xml",
        "word/footer3.xml",
    ]
    chunks: list[str] = []
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

    with zipfile.ZipFile(path) as zf:
        available = set(zf.namelist())
        for name in names:
            if name not in available:
                continue
            root = ET.fromstring(zf.read(name))
            for paragraph in root.findall(".//w:p", ns):
                parts: list[str] = []
                for node in paragraph.iter():
                    if node.tag == "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t" and node.text:
                        parts.append(node.text)
                    elif node.tag == "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tab":
                        parts.append("\t")
                    elif node.tag == "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}br":
                        parts.append("\n")
                line = "".join(parts).strip()
                if line:
                    chunks.append(line)

    text = "\n\n".join(chunks).strip()
    if not text:
        raise RuntimeError("DOCX XML 中未提取到文本，可能是图片/扫描内容或特殊结构。")
    return html.unescape(text), "docx-zip"


def extract_with_pandoc(path: Path, to_format: str = "markdown") -> tuple[str, str]:
    pandoc = shutil.which("pandoc")
    if not pandoc:
        raise RuntimeError("pandoc not found")
    result = run([pandoc, str(path), "-t", to_format, "--wrap=none"], timeout=180)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "pandoc failed")
    text = result.stdout.strip()
    if not text:
        raise RuntimeError("pandoc returned no text")
    return text, "pandoc"


def extract_with_libreoffice(path: Path) -> tuple[str, str]:
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        raise RuntimeError("LibreOffice soffice not found")
    with tempfile.TemporaryDirectory() as tmpdir:
        result = run([
            soffice,
            "--headless",
            "--convert-to",
            "txt:Text",
            "--outdir",
            tmpdir,
            str(path),
        ], timeout=180)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "LibreOffice conversion failed")
        candidates = sorted(Path(tmpdir).glob("*.txt"))
        if not candidates:
            raise RuntimeError("LibreOffice produced no txt file")
        text = read_text_file(candidates[0]).strip()
        if not text:
            raise RuntimeError("LibreOffice returned no text")
        return text, "libreoffice"


def extract(path: Path) -> tuple[str, str]:
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED:
        raise RuntimeError(f"不支持的文件类型：{suffix}。支持：{', '.join(sorted(SUPPORTED))}")
    if suffix in {".txt", ".md", ".markdown"}:
        return read_text_file(path), "plain-text"
    if suffix == ".pdf":
        return extract_pdf(path)
    if suffix == ".docx":
        try:
            return extract_with_pandoc(path)
        except Exception as pandoc_error:
            try:
                return extract_docx_via_zip(path)
            except Exception as zip_error:
                raise RuntimeError(
                    f"无法读取 DOCX。pandoc 错误：{pandoc_error}；内置 DOCX 解析错误：{zip_error}。"
                )
    if suffix in {".doc", ".rtf", ".odt"}:
        errors: list[str] = []
        for extractor in (extract_with_pandoc, extract_with_libreoffice):
            try:
                return extractor(path)
            except Exception as exc:
                errors.append(f"{extractor.__name__}: {exc}")
        raise RuntimeError(
            "无法读取该文档。" + "；".join(errors) + "。建议安装 Pandoc/LibreOffice，或转成 DOCX/PDF。"
        )
    raise RuntimeError(f"未处理的文件类型：{suffix}")


def truncate(text: str, max_chars: int | None) -> str:
    if max_chars is None or max_chars <= 0 or len(text) <= max_chars:
        return text
    return text[:max_chars] + f"\n\n[已截断：原文 {len(text)} 字符，仅输出前 {max_chars} 字符。可使用 --output 保存完整文本。]"


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract text from PDF/Word/common document files.")
    parser.add_argument("file", help="Document path")
    parser.add_argument("--output", "-o", help="Output text/markdown path")
    parser.add_argument("--max-chars", type=int, default=120000, help="Max chars printed to stdout; use 0 for no limit")
    parser.add_argument("--quiet", action="store_true", help="Do not print metadata header")
    args = parser.parse_args(list(argv) if argv is not None else None)

    path = Path(args.file).expanduser().resolve()
    if not path.exists():
        print(f"错误：文件不存在：{path}", file=sys.stderr)
        return 2
    if not path.is_file():
        print(f"错误：路径不是文件：{path}", file=sys.stderr)
        return 2

    try:
        text, method = extract(path)
    except Exception as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1

    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if args.output:
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(normalized + "\n", encoding="utf-8")
        print(f"已提取：{path}")
        print(f"方法：{method}")
        print(f"字符数：{len(normalized)}")
        print(f"输出：{output}")
        return 0

    if not args.quiet:
        print(f"[document-reader] file={path}")
        print(f"[document-reader] method={method}")
        print(f"[document-reader] chars={len(normalized)}")
        print("---")
    print(truncate(normalized, args.max_chars))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
