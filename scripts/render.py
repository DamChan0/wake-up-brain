#!/usr/bin/env python3
"""Render a self-contained Korean code-walkthrough HTML document."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path
from typing import Any

SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
MODES = ("learn", "explain")


class ValidationError(ValueError):
    pass


def fail(message: str) -> None:
    raise ValidationError(message)


def text(value: Any, name: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        fail(f"{name} must be a {'string' if allow_empty else 'non-empty string'}")
    return value


def string_list(value: Any, name: str) -> list[str]:
    if not isinstance(value, list):
        fail(f"{name} must be an array of strings")
    return [text(item, f"{name}[{index}]", allow_empty=True) for index, item in enumerate(value)]


def valid_diagram(value: Any) -> str:
    diagram = text(value, "diagram")
    if (
        "%" in diagram
        or "\\" in diagram
        or any(character.isspace() or ord(character) < 32 for character in diagram)
        or not diagram.endswith(".html")
        or diagram.startswith(("/", "\\"))
        or ":" in diagram
        or "#" in diagram
        or "?" in diagram
        or any(part in {"", ".", ".."} for part in diagram.replace("\\", "/").split("/"))
    ):
        fail("diagram must be a relative, fragment-free .html path without traversal")
    return diagram


def validate_step(raw: Any, index: int, mode: str) -> dict[str, Any]:
    name = f"steps[{index}]"
    if not isinstance(raw, dict):
        fail(f"{name} must be an object")
    step_id = text(raw.get("id"), f"{name}.id")
    if not SLUG.fullmatch(step_id):
        fail(f"{name}.id must be a lowercase slug")
    step: dict[str, Any] = {
        "id": step_id,
        "title": text(raw.get("title"), f"{name}.title"),
        "code": text(raw.get("code"), f"{name}.code", allow_empty=True),
        "language": text(raw.get("language", "text"), f"{name}.language"),
        "explanation": string_list(raw.get("explanation"), f"{name}.explanation"),
        "inputs": string_list(raw.get("inputs"), f"{name}.inputs"),
        "outputs": string_list(raw.get("outputs"), f"{name}.outputs"),
    }
    if not step["explanation"]:
        fail(f"{name}.explanation must not be empty")
    if "before" in raw:
        step["before"] = text(raw["before"], f"{name}.before", allow_empty=True)
    if "source" in raw:
        source = raw["source"]
        if not isinstance(source, dict):
            fail(f"{name}.source must be an object")
        path = text(source.get("path"), f"{name}.source.path")
        line = source.get("line")
        end_line = source.get("end_line")
        if isinstance(line, bool) or not isinstance(line, int) or line < 1:
            fail(f"{name}.source.line must be a positive integer")
        if end_line is not None and (isinstance(end_line, bool) or not isinstance(end_line, int) or end_line < line):
            fail(f"{name}.source.end_line must be an integer no smaller than line")
        step["source"] = {"path": path, "line": line, "end_line": end_line}
    question = raw.get("question")
    if question is None:
        if mode == "learn":
            fail(f"{name}.question is required in learn mode")
    else:
        if not isinstance(question, dict):
            fail(f"{name}.question must be an object")
        step["question"] = {key: text(question.get(key), f"{name}.question.{key}") for key in ("prompt", "hint", "answer", "transfer")}
    return step


def validate_document(raw: Any, mode: str) -> dict[str, Any]:
    if not isinstance(raw, dict):
        fail("JSON root must be an object")
    steps = raw.get("steps")
    if not isinstance(steps, list) or not steps:
        fail("steps must be a non-empty array")
    document: dict[str, Any] = {
        "title": text(raw.get("title"), "title"),
        "summary": text(raw.get("summary"), "summary"),
        "steps": [validate_step(step, index, mode) for index, step in enumerate(steps)],
    }
    if "provenance" in raw:
        document["provenance"] = text(raw["provenance"], "provenance")
    if "diagram" in raw:
        document["diagram"] = valid_diagram(raw["diagram"])
    ids = [step["id"] for step in document["steps"]]
    generated_ids = [identifier for step_id in ids for identifier in (step_id, f"{step_id}-title")]
    reserved = {"content", "current-step", "current-mode", "overview-title"}
    if len(generated_ids) != len(set(generated_ids)) or reserved.intersection(generated_ids):
        fail("step ids and generated heading ids must be unique and not reserved")
    return document


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def source_label(source: dict[str, Any]) -> str:
    end = source["end_line"]
    location = str(source["line"]) if end is None or end == source["line"] else f"{source['line']}–{end}"
    return f"출처 위치: {source['path']}:{location}"


def list_markup(items: list[str]) -> str:
    return "<ul>" + "".join(f"<li>{esc(item)}</li>" for item in items) + "</ul>"


def literal(label: str, code: str, language: str) -> str:
    return f'<section class="literal" aria-label="{esc(label)}"><div class="literal-title"><span>{esc(label)}</span><span>{esc(language)}</span></div><pre><code>{esc(code)}</code></pre></section>'


def question_markup(question: dict[str, str] | None, visible: bool) -> str:
    if question is None:
        return ""
    hidden = "" if visible else " hidden"
    return (
        f'<section class="learn"{hidden} aria-label="학습 질문">'
        f"<h3>먼저 예측해 보세요</h3><p>{esc(question['prompt'])}</p>"
        f"<details><summary>힌트 보기</summary><p>{esc(question['hint'])}</p></details>"
        '<label>내 답 적기<textarea rows="5" placeholder="여기에 생각을 적어 보세요. 이 내용은 저장되지 않습니다."></textarea></label>'
        '</section>'
    )


def render_step(step: dict[str, Any], number: int, total: int, learn_visible: bool) -> str:
    source = f"<p class=\"source\">{esc(source_label(step['source']))}</p>" if "source" in step else ""
    before = literal("변경 전 코드 · 확인한 기준 버전", step["before"], step["language"]) if "before" in step else ""
    explanations = "".join(f"<p>{esc(paragraph)}</p>" for paragraph in step["explanation"])
    previous = " disabled" if number == 1 else ""
    following = " disabled" if number == total else ""
    question = step.get("question")
    feedback = (
        f'<div class="learn"{"" if learn_visible else " hidden"}><p><strong>예측 해설:</strong> {esc(question["answer"])}</p><p><strong>다른 곳에 적용:</strong> {esc(question["transfer"])}</p></div>'
        if question else ""
    )
    solution_open = "" if learn_visible else " open"
    return (
        f"<article class=\"step\" id=\"{esc(step['id'])}\" aria-labelledby=\"{esc(step['id'])}-title\">"
        f"<header class=\"step-head\"><div class=\"step-number\" aria-hidden=\"true\">{number:02}</div><div><div class=\"step-kind\">생성 순서 {number} / {total}</div><h2 id=\"{esc(step['id'])}-title\" tabindex=\"-1\">{esc(step['title'])}</h2>{source}</div></header>"
        f"{before}{literal('현재 코드', step['code'], step['language'])}"
        f'<div class="io"><section><h3>입력</h3>{list_markup(step["inputs"])}</section></div>'
        f"{question_markup(question, learn_visible)}"
        f'<details class="solution"{solution_open}><summary>해설과 출력 확인</summary>'
        f'<section class="explanation"><h3 class="section-title">왜 이렇게 되는가</h3>{explanations}</section>'
        f'<section class="outputs"><h3>출력</h3>{list_markup(step["outputs"])}</section>{feedback}</details>'
        f'<nav class="nav" aria-label="단계 이동"><button type="button" data-prev{previous}>이전 단계</button><button type="button" data-next{following}>다음 단계</button></nav>'
        '</article>'
    )


def render(document: dict[str, Any], mode: str) -> str:
    root = Path(__file__).resolve().parent.parent
    template = (root / "assets" / "guide.html").read_text(encoding="utf-8")
    steps = document["steps"]
    toc = "".join(
        f"<li><a href=\"#{esc(step['id'])}\"><span class=\"toc-number\">{index:02}</span>{esc(step['title'])}</a></li>"
        for index, step in enumerate(steps, 1)
    )
    provenance = f"<p class=\"provenance\">자료: {esc(document['provenance'])}</p>" if "provenance" in document else ""
    diagram = f"<a class=\"diagram\" href=\"{esc(document['diagram'])}\">흐름도 열기</a>" if "diagram" in document else ""
    replacements = {
        "TITLE": esc(document["title"]), "HEADING": esc(document["title"]), "SUMMARY": esc(document["summary"]),
        "PROVENANCE": provenance, "DIAGRAM": diagram, "TOC": toc,
        "STEPS": "".join(render_step(step, index, len(steps), mode == "learn") for index, step in enumerate(steps, 1)),
        "INITIAL_MODE": mode, "MODE_LABEL": "학습 모드" if mode == "learn" else "설명 모드",
        "TOTAL_STEPS": str(len(steps)), "LEARN_PRESSED": str(mode == "learn").lower(),
        "EXPLAIN_PRESSED": str(mode == "explain").lower(),
        "LEARN_DISABLED": "" if all("question" in step for step in steps) else 'disabled title="학습 질문이 없는 자료입니다"',
    }
    return re.sub(r"\{\{([A-Z_]+)\}\}", lambda match: replacements[match[1]], template)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render a standalone wake-up-brain HTML guide.")
    parser.add_argument("input", type=Path, help="session JSON input")
    parser.add_argument("output", type=Path, help="HTML output")
    parser.add_argument("--mode", choices=MODES, default="learn", help="initial display mode (default: learn)")
    args = parser.parse_args(argv)
    try:
        if args.input.resolve() == args.output.resolve() or (args.output.exists() and args.input.samefile(args.output)):
            fail("input and output must be different files")
        raw = json.loads(args.input.read_text(encoding="utf-8"))
        result = render(validate_document(raw, args.mode), args.mode)
        args.output.write_text(result, encoding="utf-8")
    except (OSError, UnicodeError, json.JSONDecodeError, ValidationError) as error:
        print(f"render.py: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
