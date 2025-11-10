from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from flask import (
    abort,
    current_app,
    jsonify,
    render_template,
    request,
    send_from_directory,
)
from werkzeug.utils import secure_filename

from . import bp


def _load_scenario_metadata(scenario_dir: Path) -> list[dict[str, Any]]:
    """Return structured metadata for all JSON scenarios in ``scenario_dir``."""

    scenarios: list[dict[str, Any]] = []
    if not scenario_dir.exists():
        return scenarios

    for scenario_file in sorted(scenario_dir.rglob("*.json")):
        if not scenario_file.is_file():
            continue

        try:
            with scenario_file.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError):
            current_app.logger.warning(
                "Failed to parse scenario file %s", scenario_file
            )
            continue

        metadata = payload.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}

        scenario_id = metadata.get("id") or payload.get("id") or scenario_file.stem
        title = (
            metadata.get("title")
            or payload.get("title")
            or metadata.get("name")
            or scenario_id
        )
        description = (
            metadata.get("description")
            or metadata.get("summary")
            or payload.get("description")
            or ""
        )
        category = metadata.get("category") or "Uncategorized"

        tags = metadata.get("tags", [])
        if not isinstance(tags, Iterable) or isinstance(tags, (str, bytes)):
            tags = []
        else:
            tags = [str(tag) for tag in tags]

        order = metadata.get("order")
        scenarios.append(
            {
                "id": str(scenario_id),
                "title": str(title),
                "description": str(description),
                "category": str(category),
                "tags": tags,
                "order": order,
                "filename": scenario_file.name,
            }
        )

    return scenarios


def _group_scenarios(scenarios: Iterable[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for scenario in scenarios:
        grouped[scenario["category"]].append(scenario)

    ordered: dict[str, list[dict[str, Any]]] = {}
    for category, items in sorted(grouped.items(), key=lambda item: item[0].lower()):
        items.sort(key=_scenario_sort_key)
        ordered[category] = items

    return ordered


def _scenario_sort_key(item: dict[str, Any]) -> tuple[Any, Any, str]:
    order = item.get("order")
    title = item["title"].lower()
    if isinstance(order, (int, float)):
        return (0, float(order), title)
    if isinstance(order, str):
        return (0, order.lower(), title)
    return (1, "", title)


def _sanitize_path_components(path_value: str) -> Path | None:
    candidate = Path(path_value)
    parts: list[str] = []
    for part in candidate.parts:
        if part in {"", ".", ".."}:
            continue
        safe_part = secure_filename(part)
        if not safe_part:
            continue
        parts.append(safe_part)

    if not parts:
        return None

    return Path(*parts)


@bp.get("/")
def index() -> str:
    scenario_dir = Path(current_app.config["SCENARIO_DIR"])
    scenarios = _load_scenario_metadata(scenario_dir)
    grouped_scenarios = _group_scenarios(scenarios)

    selected_scenario = request.args.get("scenario") or None
    search_term = request.args.get("search") or ""

    return render_template(
        "main/index.html",
        scenario_groups=grouped_scenarios,
        scenarios=scenarios,
        selected_scenario_id=selected_scenario,
        search_term=search_term,
    )


@bp.get("/scenario/<scenario_id>")
def scenario_details(scenario_id: str):
    safe_identifier = secure_filename(scenario_id)
    if not safe_identifier:
        abort(404)

    scenario_dir = Path(current_app.config["SCENARIO_DIR"])
    scenario_file = scenario_dir / f"{safe_identifier}.json"
    if not scenario_file.is_file():
        abort(404)

    try:
        with scenario_file.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except json.JSONDecodeError as exc:  # pragma: no cover - indicates corrupt data
        abort(400, description=f"Invalid scenario file: {exc}")

    return jsonify(payload)


@bp.get("/snippet/<path:snippet_path>")
def serve_snippet(snippet_path: str):
    sanitized = _sanitize_path_components(snippet_path)
    if sanitized is None:
        abort(404)

    relative_path = sanitized.as_posix()

    upload_dir = Path(current_app.config["UPLOAD_DIR"])
    upload_candidate = upload_dir / sanitized
    if upload_candidate.is_file():
        return send_from_directory(upload_dir, relative_path)

    data_snippet_dir = Path(current_app.root_path).parent / "data" / "snippets"
    data_candidate = data_snippet_dir / sanitized
    if data_candidate.is_file():
        return send_from_directory(data_snippet_dir, relative_path)

    abort(404)
