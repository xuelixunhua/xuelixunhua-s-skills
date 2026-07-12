#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multimodal formula recognition helpers for rule PDFs.

This module is intentionally provider-pluggable, but currently implements an
OpenAI-compatible multimodal chat-completions provider.

Design goals:
1. Render formula-sensitive clause pages to images
2. Call a multimodal model with clause context + page screenshots
3. Return clause Markdown with LaTeX embedded directly in the body
4. Cache intermediate responses under tmp/pdfs/ for reuse
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


DEFAULT_SYSTEM_PROMPT = """
你是“电力市场规则文档公式识别助手”。
你的任务是针对规则 PDF 页面中的公式、条件表达式和分摊计算式进行准确转写，
把条款正文重写为适合 Markdown 展示的内容，并将公式写成规范的 LaTeX。

要求：
1. 只依据当前图片和条款原文识别，不得补写图片中不存在的变量或公式。
2. 输出的是“条款正文 Markdown”，不是解释报告。
3. 数学公式必须使用 LaTeX，可使用 $$...$$ 包裹块级公式。
4. 中文变量名、中文下标或中文说明统一使用 \\text{} 包裹。
5. 保留求和范围、上下标、括号、条件项和比例关系。
6. 如果图片中公式不完整、模糊或无法确认，不得猜测补全；需要标记 review_required=true。
7. 不要重复条款编号和条款标题，只输出条款正文内容。
8. 不要输出 JSON 代码块之外的额外说明。
""".strip()

DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CodexRuleAgent/1.0"
CACHE_VERSION = "formula-mm-v3-footer-aware"
FOOTER_TEXT_COMPACT_RE = re.compile(r"^第\d+页[,，]?共\d+页$")
PHYSICAL_PAGE_COMPACT_RE = re.compile(r"^[-—]\d+[-—]$")


PAGE_REVIEW_SYSTEM_PROMPT = """
你是“电力市场规则文档页面 OCR 与公式转写助手”。
你的任务是根据规则 PDF 页面截图，输出适合人工复核和后续结构化处理的 Markdown 文本。

要求：
1. 只依据页面图片识别，不得脑补缺失内容。
2. 页面中的公式、求和式、条件表达式必须转写为规范的 LaTeX。
3. 页面中的普通正文、列表、表头说明保留为自然的中文 Markdown。
4. 如果无法可靠识别，必须标记 review_required=true，并把原因写入 issues。
5. 仅输出 JSON，不要输出额外解释。
""".strip()


def extract_json_text(content: str) -> str:
    text = str(content or "").strip()
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, flags=re.IGNORECASE)
    return fenced.group(1).strip() if fenced else text


def repair_json_backslashes(text: str) -> str:
    result: List[str] = []
    in_string = False
    escaped = False
    length = len(text)

    for index, ch in enumerate(text):
        if not in_string:
            result.append(ch)
            if ch == '"':
                in_string = True
            continue

        if escaped:
            result.append(ch)
            escaped = False
            continue

        if ch == "\\":
            next_char = text[index + 1] if index + 1 < length else ""
            if next_char and next_char in {'"', "\\", "/", "b", "f", "n", "r", "t", "u"}:
                result.append(ch)
                escaped = True
            else:
                result.append("\\\\")
            continue

        result.append(ch)
        if ch == '"':
            in_string = False

    return "".join(result)


def parse_model_json(content: str) -> Dict:
    raw = extract_json_text(content)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        repaired = repair_json_backslashes(raw)
        return json.loads(repaired)


def compact_text(text: str) -> str:
    cleaned = text or ""
    cleaned = cleaned.replace("\x00", " ")
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", cleaned)
    return cleaned.strip()


def sanitize_prompt_text(text: str, max_length: int = 4000) -> str:
    cleaned = str(text or "")
    cleaned = "".join(
        ch
        if (ch.isprintable() or ch in "\n\r\t") and not (0xE000 <= ord(ch) <= 0xF8FF)
        else " "
        for ch in cleaned
    )
    cleaned = compact_text(cleaned)
    if len(cleaned) > max_length:
        return cleaned[: max_length - 1].rstrip() + "…"
    return cleaned


def clean_markdown_response(markdown_text: str) -> str:
    text = str(markdown_text or "").strip()
    if not text:
        return ""
    fenced = re.search(r"```(?:markdown)?\s*([\s\S]*?)\s*```", text, flags=re.IGNORECASE)
    if fenced:
        text = fenced.group(1).strip()
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def compact_block_text(text: str) -> str:
    return re.sub(r"\s+", "", sanitize_prompt_text(text, max_length=200))


def is_footer_block_text(text: str) -> bool:
    compact = compact_block_text(text)
    if not compact:
        return False
    return bool(
        FOOTER_TEXT_COMPACT_RE.match(compact)
        or PHYSICAL_PAGE_COMPACT_RE.match(compact)
    )


def is_header_block_text(text: str) -> bool:
    compact = compact_block_text(text)
    if not compact or len(compact) > 80:
        return False
    return any(token in compact for token in ("内蒙古电力市场", "实施细则", "基本规则"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clause_input_hash(document: Dict, clause: Dict, image_paths: List[Path]) -> str:
    raw = json.dumps(
        {
            "cache_version": CACHE_VERSION,
            "document_title": document.get("title"),
            "rule_type": document.get("rule_type"),
            "version_label": document.get("version_label"),
            "id": clause.get("id"),
            "marker": clause.get("marker"),
            "label": clause.get("label"),
            "pages": clause.get("page_numbers"),
            "text": clause.get("text"),
            "image_digests": [sha256_file(path) for path in image_paths],
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def page_input_hash(page_number: int, document: Dict | None, image_path: Path) -> str:
    document = document or {}
    image_digest = sha256_file(image_path)
    raw = json.dumps(
        {
            "cache_version": CACHE_VERSION,
            "page": page_number,
            "title": document.get("title"),
            "rule_type": document.get("rule_type"),
            "version_label": document.get("version_label"),
            "image_digest": image_digest,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def image_to_data_url(path: Path) -> str:
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{data}"


@dataclass
class MultimodalConfig:
    provider: str
    api_key: str
    base_url: str
    model: str
    temperature: float
    max_tokens: int
    timeout_ms: int
    max_images_per_clause: int
    max_clauses_per_run: int
    enabled: bool


def load_config() -> MultimodalConfig:
    provider = os.environ.get("RULE_FORMULA_PROVIDER", "openai-compatible")

    if provider == "zhipu-openai":
        default_api_key = (
            os.environ.get("ZHIPUAI_API_KEY")
            or os.environ.get("BIGMODEL_API_KEY", "")
        )
        default_base_url = "https://open.bigmodel.cn/api/paas/v4"
        default_model = "glm-4.6v"
        default_temperature = "0.2"
    else:
        default_api_key = os.environ.get("SKYAPI_API_KEY", "")
        default_base_url = os.environ.get("SKYAPI_BASE_URL") or "https://api.skyapi.org"
        default_model = os.environ.get("SKYAPI_MODEL") or "gpt-5.4"
        default_temperature = os.environ.get("SKYAPI_TEMPERATURE") or "0"

    api_key = os.environ.get("RULE_FORMULA_API_KEY") or default_api_key
    base_url = (os.environ.get("RULE_FORMULA_BASE_URL") or default_base_url).rstrip("/")
    model = os.environ.get("RULE_FORMULA_MODEL") or default_model
    temperature = float(os.environ.get("RULE_FORMULA_TEMPERATURE", default_temperature))
    if provider == "zhipu-openai" and not (0 < temperature < 1):
        temperature = 0.2
    max_tokens = int(os.environ.get("RULE_FORMULA_MAX_TOKENS", "4000"))
    timeout_ms = int(os.environ.get("RULE_FORMULA_TIMEOUT_MS", "90000"))
    max_images_per_clause = int(os.environ.get("RULE_FORMULA_MAX_IMAGES", "4"))
    max_clauses_per_run = int(os.environ.get("RULE_FORMULA_MAX_CLAUSES", "0"))
    enabled_text = os.environ.get("RULE_FORMULA_ENABLED", "1").strip().lower()
    enabled = enabled_text not in {"0", "false", "off", "no"} and bool(api_key)
    return MultimodalConfig(
        provider=provider,
        api_key=api_key,
        base_url=base_url,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout_ms=timeout_ms,
        max_images_per_clause=max_images_per_clause,
        max_clauses_per_run=max_clauses_per_run,
        enabled=enabled,
    )


def ensure_review_images(
    pdf_path: Path,
    pages: Iterable[int],
    output_dir: Path,
    dpi: int = 220,
    ) -> Dict[int, Path]:
    try:
        import fitz
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("PyMuPDF (fitz) is required for formula page rendering.") from exc

    output_dir.mkdir(parents=True, exist_ok=True)
    resolved: Dict[int, Path] = {}
    page_list = sorted(set(page for page in pages if page))
    if not page_list:
        return resolved

    doc = fitz.open(str(pdf_path))
    try:
        for page_number in page_list:
            image_path = output_dir / f"page_{page_number:03d}_body_v2.png"
            if not image_path.exists():
                if page_number < 1 or page_number > len(doc):
                    continue
                page = doc.load_page(page_number - 1)
                rect = page.rect
                left = rect.x0 + rect.width * 0.03
                right = rect.x1 - rect.width * 0.03
                top = rect.y0 + rect.height * 0.03
                bottom = rect.y1 - rect.height * 0.05
                blocks = page.get_text("blocks")
                for block in blocks:
                    if len(block) < 5:
                        continue
                    x0, y0, x1, y1, text = block[:5]
                    block_type = block[6] if len(block) > 6 else 0
                    if block_type != 0:
                        continue
                    if is_footer_block_text(text):
                        bottom = min(bottom, y0 - 4)
                    elif y0 <= rect.y0 + rect.height * 0.08 and is_header_block_text(text):
                        top = max(top, y1 + 4)
                clip = fitz.Rect(left, top, right, bottom)
                if clip.width <= 0 or clip.height <= 0:
                    clip = rect
                matrix = fitz.Matrix(dpi / 72, dpi / 72)
                pix = page.get_pixmap(matrix=matrix, alpha=False, clip=clip)
                pix.save(str(image_path))
            resolved[page_number] = image_path
    finally:
        doc.close()

    return resolved


def build_user_prompt(document: Dict, clause: Dict) -> str:
    clause_label = clause.get("label") or clause.get("marker") or "未命名条款"
    clause_text = sanitize_prompt_text(clause.get("text") or "")
    return f"""
请识别下列规则条款中的公式，并输出“条款正文 Markdown”。

文档标题：{document.get("title") or ""}
规则类型：{document.get("rule_type") or ""}
版本：{document.get("version_label") or ""}
条款标识：{clause.get("marker") or ""}
条款标题：{clause_label}
物理页：{", ".join(map(str, clause.get("page_numbers") or []))}

条款原文（文本抽取结果，可能存在公式乱码，仅供辅助）：
{clause_text}

输出要求：
1. 仅输出 JSON。
2. JSON 格式必须为：
{{
  "content_markdown": "...",
  "review_required": false,
  "issues": []
}}
3. content_markdown 是“条款正文 Markdown”，不要再重复条款编号和标题。
4. 公式写成 LaTeX，并直接嵌入 Markdown。
5. 页面页眉、页脚、页码不属于正文，不要转写。
6. 如无法可靠识别，review_required 置为 true，并把问题写入 issues。
""".strip()


def build_page_review_prompt(page_number: int, document: Dict | None = None) -> str:
    document = document or {}
    return f"""
请识别下列规则文档页面，并输出页面级 Markdown。

文档标题：{document.get("title") or ""}
规则类型：{document.get("rule_type") or ""}
版本：{document.get("version_label") or ""}
物理页：{page_number}

输出要求：
1. 仅输出 JSON。
2. JSON 格式必须为：
{{
  "page_markdown": "...",
  "review_required": false,
  "issues": []
}}
3. page_markdown 需要尽量保留页面中的正文、列表和公式。
4. 公式必须使用 LaTeX，直接嵌入 Markdown。
5. 页面页眉、页脚、页码不属于正文，不要转写。
6. 若页面中存在无法确认的公式、表格或字符，请把问题写入 issues。
""".strip()


def build_openai_content(prompt_text: str, image_paths: List[Path], max_images: int) -> List[Dict]:
    content: List[Dict] = [{"type": "text", "text": prompt_text}]
    for image_path in image_paths[:max_images]:
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": image_to_data_url(image_path)},
            }
        )
    return content


def post_openai_compatible(
    config: MultimodalConfig,
    system_prompt: str,
    content: List[Dict],
) -> Dict:
    url = f"{config.base_url}/v1/chat/completions"
    payload = {
        "model": config.model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content},
        ],
    }
    if config.temperature is not None:
        payload["temperature"] = config.temperature
    if config.max_tokens > 0:
        payload["max_tokens"] = config.max_tokens
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.api_key}",
            "User-Agent": DEFAULT_USER_AGENT,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=config.timeout_ms / 1000) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:  # pragma: no cover
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"formula multimodal upstream error {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:  # pragma: no cover
        raise RuntimeError(f"formula multimodal request failed: {exc}") from exc

    return data


def call_openai_compatible(
    config: MultimodalConfig,
    document: Dict,
    clause: Dict,
    image_paths: List[Path],
) -> Dict:
    content = build_openai_content(
        build_user_prompt(document, clause),
        image_paths,
        config.max_images_per_clause,
    )
    data = post_openai_compatible(config, DEFAULT_SYSTEM_PROMPT, content)
    raw_content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    parsed = parse_model_json(raw_content)
    return {
        "content_markdown": clean_markdown_response(parsed.get("content_markdown", "")),
        "review_required": bool(parsed.get("review_required")),
        "issues": [str(item).strip() for item in parsed.get("issues", []) if str(item).strip()],
        "raw_response": raw_content,
    }


def review_page_with_multimodal(
    image_path: Path,
    page_number: int,
    document: Dict | None = None,
) -> Dict:
    config = load_config()
    if not config.enabled:
        return {
            "page_markdown": "",
            "review_required": True,
            "issues": ["未配置多模态公式识别接口，页面 OCR 已跳过。"],
            "raw_response": "",
            "provider_status": "disabled",
        }

    return call_page_review_provider(config, image_path, page_number, document)


def call_page_review_provider(
    config: MultimodalConfig,
    image_path: Path,
    page_number: int,
    document: Dict | None = None,
) -> Dict:
    content = build_openai_content(
        build_page_review_prompt(page_number, document),
        [image_path],
        1,
    )
    data = post_openai_compatible(config, PAGE_REVIEW_SYSTEM_PROMPT, content)
    raw_content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    parsed = parse_model_json(raw_content)
    return {
        "page_markdown": clean_markdown_response(parsed.get("page_markdown", "")),
        "review_required": bool(parsed.get("review_required")),
        "issues": [str(item).strip() for item in parsed.get("issues", []) if str(item).strip()],
        "raw_response": raw_content,
        "provider_status": "ok",
    }


def review_pdf_pages_with_multimodal(
    document: Dict | None,
    pdf_path: Path,
    pages: Iterable[int],
    review_dir: Path,
    cache_path: Path | None = None,
    dpi: int = 220,
) -> Tuple[Dict[int, Dict], Dict]:
    config = load_config()
    cache = load_cache(cache_path)
    cache_items = cache.setdefault("items", {})
    processed = 0
    provider_errors: List[str] = []
    needed_pages = sorted(set(page for page in pages if page))
    rendered = ensure_review_images(pdf_path, needed_pages, review_dir, dpi=dpi) if needed_pages else {}
    results: Dict[int, Dict] = {}

    cache_hits = 0
    cache_misses = 0
    for page_number in needed_pages:
        image_path = rendered.get(page_number)
        if not image_path:
            results[page_number] = {
                "page_markdown": "",
                "review_required": True,
                "issues": [f"未找到第{page_number}页截图，页面复核已跳过。"],
                "raw_response": "",
                "provider_status": "missing_image",
            }
            continue

        cache_key = page_input_hash(page_number, document, image_path)
        cached = cache_items.get(cache_key)
        if not cached:
            cached = find_cached_page_result(cache_items, page_number)
        if cached and "page_markdown" in cached:
            results[page_number] = normalize_page_result(cached, image_path)
            cache_hits += 1
            continue

        if not config.enabled:
            cache_misses += 1
            results[page_number] = {
                "page_markdown": "",
                "review_required": True,
                "issues": ["未命中页面识别缓存，且未配置多模态接口，页面复核已跳过。"],
                "raw_response": "",
                "provider_status": "disabled",
                "image_path": str(image_path),
            }
            continue

        try:
            result = call_page_review_provider(config, image_path, page_number, document)
            result["image_path"] = str(image_path)
            result["page"] = page_number
            cache_items[cache_key] = result
            results[page_number] = result
            processed += 1
            save_cache(cache_path, cache)
        except Exception as exc:  # pragma: no cover
            error_text = str(exc)
            provider_errors.append(error_text)
            results[page_number] = {
                "page_markdown": "",
                "review_required": True,
                "issues": [f"多模态页面识别失败：{error_text}"],
                "raw_response": "",
                "provider_status": "error",
                "image_path": str(image_path),
            }

    if not config.enabled and not provider_errors:
        cache["provider_status"] = "cache_only"
        cache["reason"] = "missing api key or RULE_FORMULA_ENABLED=0; applied cached page results where available"
    else:
        cache["provider_status"] = "ok" if not provider_errors else "error"
    cache["provider_errors"] = provider_errors
    cache["processed_count"] = processed
    cache["cache_hit_count"] = cache_hits
    cache["cache_miss_count"] = cache_misses
    save_cache(cache_path, cache)
    return results, cache


def call_provider(
    config: MultimodalConfig,
    document: Dict,
    clause: Dict,
    image_paths: List[Path],
) -> Dict:
    if config.provider not in {"openai-compatible", "zhipu-openai"}:
        raise RuntimeError(f"Unsupported formula provider: {config.provider}")
    return call_openai_compatible(config, document, clause, image_paths)


def load_cache(path: Path | None) -> Dict:
    if not path or not path.exists():
        return {"items": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"items": {}}


def save_cache(path: Path | None, payload: Dict) -> None:
    if not path:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def same_page_set(left: Iterable[int], right: Iterable[int]) -> bool:
    left_pages = {int(page) for page in left if page}
    right_pages = {int(page) for page in right if page}
    return bool(left_pages and right_pages and left_pages == right_pages)


def find_cached_clause_result(cache_items: Dict, clause: Dict) -> Dict | None:
    """Allow old but still valid multimodal cache entries to survive image-crop upgrades."""
    marker = str(clause.get("marker") or "").strip()
    label = str(clause.get("label") or "").strip()
    pages = clause.get("page_numbers") or []

    for cached in cache_items.values():
        if not isinstance(cached, dict) or not cached.get("content_markdown"):
            continue
        if marker and marker != str(cached.get("marker") or "").strip():
            continue
        if label and label != str(cached.get("label") or "").strip():
            continue
        cached_pages = cached.get("page_numbers") or []
        if pages and cached_pages and not same_page_set(pages, cached_pages):
            continue
        return cached
    return None


def find_cached_page_result(cache_items: Dict, page_number: int) -> Dict | None:
    for cached in cache_items.values():
        if not isinstance(cached, dict) or not cached.get("page_markdown"):
            continue
        if int(cached.get("page") or 0) == int(page_number):
            return cached
    return None


def normalize_clause_result(result: Dict, image_paths: List[Path] | None = None) -> Dict:
    payload = dict(result or {})
    payload["content_markdown"] = clean_markdown_response(payload.get("content_markdown", ""))
    payload["review_required"] = bool(payload.get("review_required"))
    payload["issues"] = [str(item).strip() for item in payload.get("issues", []) if str(item).strip()]
    if image_paths and not payload.get("image_paths"):
        payload["image_paths"] = [str(path) for path in image_paths]
    return payload


def normalize_page_result(result: Dict, image_path: Path | None = None) -> Dict:
    payload = dict(result or {})
    payload["page_markdown"] = clean_markdown_response(payload.get("page_markdown", ""))
    payload["review_required"] = bool(payload.get("review_required"))
    payload["issues"] = [str(item).strip() for item in payload.get("issues", []) if str(item).strip()]
    payload.setdefault("provider_status", "cache")
    if image_path and not payload.get("image_path"):
        payload["image_path"] = str(image_path)
    return payload


def apply_formula_markdown(
    document: Dict,
    clauses: List[Dict],
    pdf_path: Path,
    review_dir: Path,
    cache_path: Path | None = None,
    dpi: int = 220,
) -> Tuple[List[Dict], Dict]:
    config = load_config()
    cache = load_cache(cache_path)
    cache_items = cache.setdefault("items", {})
    processed = 0
    review_dir.mkdir(parents=True, exist_ok=True)

    formula_clauses = [clause for clause in clauses if clause.get("formula_sensitive")]
    formula_clauses.sort(
        key=lambda clause: (
            len(clause.get("formula_review_pages") or []),
            len(clause.get("page_numbers") or []),
        ),
        reverse=True,
    )
    if config.max_clauses_per_run > 0:
        formula_clauses = formula_clauses[: config.max_clauses_per_run]

    needed_pages = sorted(
        {
            page
            for clause in formula_clauses
            for page in (clause.get("formula_review_pages") or clause.get("page_numbers") or [])
        }
    )
    rendered = ensure_review_images(pdf_path, needed_pages, review_dir, dpi=dpi) if needed_pages else {}

    for clause in clauses:
        clause.setdefault("content_markdown", clause.get("default_markdown") or "")
        clause.setdefault("content_source", "raw_text")
        clause.setdefault("content_review_required", False)
        clause.setdefault("content_issues", [])

    provider_errors: List[str] = []
    cache_hits = 0
    cache_misses = 0
    for clause in formula_clauses:
        clause_pages = clause.get("formula_review_pages") or clause.get("page_numbers") or []
        image_paths = [rendered[page] for page in clause_pages if page in rendered]
        cache_key = clause_input_hash(document, clause, image_paths) if image_paths else None
        cached = cache_items.get(cache_key) if cache_key else None
        if not cached:
            cached = find_cached_clause_result(cache_items, clause)
        if not image_paths:
            clause["content_review_required"] = True
            clause["content_issues"] = ["未找到公式复核页截图，暂未调用多模态识别。"]
            continue

        if cached and cached.get("content_markdown"):
            result = normalize_clause_result(cached, image_paths)
            cache_hits += 1
        else:
            if not config.enabled:
                clause["content_review_required"] = True
                clause["content_issues"] = ["未命中公式识别缓存，且未配置多模态接口，暂保留原始文本。"]
                cache_misses += 1
                continue
            try:
                result = call_provider(config, document, clause, image_paths)
                result["image_paths"] = [str(path) for path in image_paths]
                result["marker"] = clause.get("marker")
                result["label"] = clause.get("label")
                result["page_numbers"] = clause.get("page_numbers")
                if cache_key:
                    cache_items[cache_key] = result
                processed += 1
                save_cache(cache_path, cache)
            except Exception as exc:  # pragma: no cover
                error_text = str(exc)
                clause["content_review_required"] = True
                clause["content_issues"] = [f"多模态公式识别失败：{error_text}"]
                provider_errors.append(error_text)
                continue

        if result.get("content_markdown"):
            clause["content_markdown"] = result["content_markdown"]
            clause["content_source"] = "multimodal_formula"
        clause["content_review_required"] = bool(result.get("review_required"))
        clause["content_issues"] = result.get("issues", [])

    if not config.enabled and not provider_errors:
        cache["provider_status"] = "cache_only"
        cache["reason"] = "missing api key or RULE_FORMULA_ENABLED=0; applied cached clause results where available"
    else:
        cache["provider_status"] = "ok" if not provider_errors else "error"
    cache["provider_errors"] = provider_errors
    cache["processed_count"] = processed
    cache["cache_hit_count"] = cache_hits
    cache["cache_miss_count"] = cache_misses
    save_cache(cache_path, cache)
    return clauses, cache
