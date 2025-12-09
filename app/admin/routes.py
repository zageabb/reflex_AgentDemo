"""Administrative routes for managing uploads and scenarios."""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import (
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from .. import db
from ..models import AuditLog, User
from . import bp
from .forms import (
    ScenarioCreateForm,
    ScenarioDeleteForm,
    ScenarioDuplicateForm,
    ScenarioEditForm,
    UploadForm,
)


ALLOWED_UPLOAD_EXTENSIONS = {
    ".html",
    ".htm",
    ".txt",
    ".png",
    ".jpg",
    ".xlsx",
    ".docx",
    ".pdf",
}


def _require_admin() -> None:
    if not current_user.is_admin:
        abort(403)


def _log_action(action: str, details: str) -> None:
    entry = AuditLog(user_id=current_user.id, action=action, details=details)
    db.session.add(entry)
    db.session.commit()


def _iter_directory_files(directory: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    if not directory.exists():
        return entries

    for path in sorted(directory.rglob("*")):
        if not path.is_file():
            continue
        stat = path.stat()
        entries.append(
            {
                "name": path.relative_to(directory).as_posix(),
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime),
            }
        )
    return entries


def _scenario_file(directory: Path, name: str) -> Path:
    safe_name = secure_filename(name)
    if not safe_name:
        abort(404)
    if not safe_name.lower().endswith(".json"):
        safe_name = f"{safe_name}.json"
    candidate = directory / safe_name
    if not candidate.is_file():
        abort(404)
    return candidate


def _validate_scenario_payload(payload: Any) -> str:
    if not isinstance(payload, dict):
        raise ValueError("Scenario content must be a JSON object.")

    metadata = payload.get("metadata", {})
    if metadata and not isinstance(metadata, dict):
        raise ValueError("The 'metadata' field must be an object when provided.")

    scenario_id = str(payload.get("id") or metadata.get("id") or "").strip()
    if not scenario_id:
        raise ValueError("A scenario must define an 'id' or metadata.id value.")

    steps = payload.get("steps")
    if steps is None:
        raise ValueError("The scenario must include a 'steps' array.")
    if not isinstance(steps, list):
        raise ValueError("The 'steps' field must be an array of step definitions.")
    for index, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            raise ValueError(f"Step {index} must be a JSON object.")

    return scenario_id


@bp.get("/")
@login_required
def dashboard() -> str:
    _require_admin()

    upload_dir = Path(current_app.config["UPLOAD_DIR"])
    scenario_dir = Path(current_app.config["SCENARIO_DIR"])

    user_count = User.query.count()
    scenario_count = sum(1 for path in scenario_dir.rglob("*.json") if path.is_file())
    upload_count = sum(1 for path in upload_dir.rglob("*") if path.is_file())

    return render_template(
        "admin/dashboard.html",
        user_count=user_count,
        scenario_count=scenario_count,
        upload_count=upload_count,
    )


@bp.get("/uploads")
@login_required
def uploads() -> str:
    _require_admin()

    form = UploadForm()
    upload_dir = Path(current_app.config["UPLOAD_DIR"])
    uploads = _iter_directory_files(upload_dir)

    return render_template("admin/uploads.html", form=form, uploads=uploads)


@bp.post("/upload")
@login_required
def upload_file():
    _require_admin()

    form = UploadForm()
    if not form.validate_on_submit():
        for errors in form.errors.values():
            for error in errors:
                flash(error, "danger")
        return redirect(url_for("admin.uploads"))

    file_storage = form.file.data
    filename = secure_filename(file_storage.filename or "")
    if not filename:
        flash("Invalid file name.", "danger")
        return redirect(url_for("admin.uploads"))

    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_UPLOAD_EXTENSIONS:
        flash(
            "Unsupported file type. Upload .html, .htm, .txt, .png, .jpg, .xlsx, .docx, or .pdf files.",
            "danger",
        )
        return redirect(url_for("admin.uploads"))

    upload_dir = Path(current_app.config["UPLOAD_DIR"])
    upload_dir.mkdir(parents=True, exist_ok=True)
    destination = upload_dir / filename
    if destination.exists():
        flash("A file with that name already exists.", "warning")
        return redirect(url_for("admin.uploads"))

    file_storage.save(destination)
    _log_action("upload.create", f"Uploaded snippet {filename}")
    flash("File uploaded successfully.", "success")
    return redirect(url_for("admin.uploads"))


@bp.get("/scenarios")
@login_required
def scenarios() -> str:
    _require_admin()

    scenario_dir = Path(current_app.config["SCENARIO_DIR"])
    scenario_dir.mkdir(parents=True, exist_ok=True)
    scenarios = _iter_directory_files(scenario_dir)

    duplicate_form = ScenarioDuplicateForm()
    delete_form = ScenarioDeleteForm()

    return render_template(
        "admin/scenarios.html",
        scenarios=scenarios,
        duplicate_form=duplicate_form,
        delete_form=delete_form,
    )


@bp.post("/scenarios/duplicate")
@login_required
def duplicate_scenario():
    _require_admin()

    form = ScenarioDuplicateForm()
    if not form.validate_on_submit():
        for errors in form.errors.values():
            for error in errors:
                flash(error, "danger")
        return redirect(url_for("admin.scenarios"))

    scenario_dir = Path(current_app.config["SCENARIO_DIR"])
    scenario_dir.mkdir(parents=True, exist_ok=True)

    source_name = Path(form.source_filename.data).name
    source_file = _scenario_file(scenario_dir, source_name)

    new_name = secure_filename(form.new_filename.data.strip())
    if not new_name:
        flash("Provide a name for the duplicated scenario.", "danger")
        return redirect(url_for("admin.scenarios"))
    if not new_name.lower().endswith(".json"):
        new_name = f"{new_name}.json"

    destination = scenario_dir / new_name
    if destination.exists():
        flash("A scenario with that name already exists.", "warning")
        return redirect(url_for("admin.scenarios"))

    shutil.copy2(source_file, destination)
    _log_action(
        "scenario.duplicate",
        f"Duplicated {source_file.name} to {destination.name}",
    )
    flash("Scenario duplicated successfully.", "success")
    return redirect(url_for("admin.scenarios"))


@bp.post("/scenarios/delete")
@login_required
def delete_scenario():
    _require_admin()

    form = ScenarioDeleteForm()
    if not form.validate_on_submit():
        for errors in form.errors.values():
            for error in errors:
                flash(error, "danger")
        return redirect(url_for("admin.scenarios"))

    scenario_dir = Path(current_app.config["SCENARIO_DIR"])
    scenario_dir.mkdir(parents=True, exist_ok=True)

    filename = Path(form.filename.data).name
    target = _scenario_file(scenario_dir, filename)
    target.unlink()

    _log_action("scenario.delete", f"Deleted scenario {target.name}")
    flash("Scenario deleted.", "info")
    return redirect(url_for("admin.scenarios"))


@bp.route("/scenarios/<scenario_id>/edit", methods=["GET", "POST"])
@login_required
def edit_scenario(scenario_id: str):
    _require_admin()

    scenario_dir = Path(current_app.config["SCENARIO_DIR"])
    scenario_dir.mkdir(parents=True, exist_ok=True)
    scenario_file = _scenario_file(scenario_dir, f"{scenario_id}.json")

    form = ScenarioEditForm()

    if form.validate_on_submit():
        raw_content = form.content.data
        try:
            payload = json.loads(raw_content)
        except json.JSONDecodeError as exc:
            form.content.errors.append(f"Invalid JSON: {exc}")
            raw_content = None
        else:
            try:
                scenario_identifier = _validate_scenario_payload(payload)
            except ValueError as exc:
                form.content.errors.append(str(exc))
            else:
                formatted = json.dumps(payload, indent=2, ensure_ascii=False)
                scenario_file.write_text(f"{formatted}\n", encoding="utf-8")
                _log_action(
                    "scenario.update",
                    f"Updated scenario {scenario_file.name} (id={scenario_identifier})",
                )
                flash("Scenario saved successfully.", "success")
                return redirect(
                    url_for("admin.edit_scenario", scenario_id=scenario_file.stem)
                )

        if raw_content is None:
            # Reset the textarea value to the submitted content for display
            form.content.data = request.form.get("content", "")

    elif request.method == "GET":
        content = scenario_file.read_text(encoding="utf-8")
        try:
            payload = json.loads(content)
        except json.JSONDecodeError:
            form.content.data = content
        else:
            formatted = json.dumps(payload, indent=2, ensure_ascii=False)
            form.content.data = f"{formatted}\n"

    return render_template(
        "admin/editor.html",
        form=form,
        scenario_name=scenario_file.name,
        scenario_id=scenario_file.stem,
    )


@bp.route("/scenarios/new", methods=["GET", "POST"])
@login_required
def new_scenario():
    _require_admin()

    form = ScenarioCreateForm()
    if form.validate_on_submit():
        scenario_dir = Path(current_app.config["SCENARIO_DIR"])
        scenario_dir.mkdir(parents=True, exist_ok=True)

        scenario_id = form.scenario_id.data.strip()
        safe_id = secure_filename(scenario_id)
        if not safe_id:
            flash("Scenario ID contains no valid characters after sanitization.", "danger")
            return redirect(url_for("admin.new_scenario"))

        filename = f"{safe_id}.json"
        destination = scenario_dir / filename
        if destination.exists():
            flash("A scenario with that ID already exists.", "warning")
            return redirect(url_for("admin.new_scenario"))

        metadata = {
            "id": safe_id,
            "title": form.title.data.strip(),
            "description": (form.description.data or "").strip(),
            "category": (form.category.data or "General").strip() or "General",
            "tags": [
                tag.strip()
                for tag in (form.tags.data or "").split(",")
                if tag.strip()
            ],
        }

        payload = {
            "id": safe_id,
            "metadata": metadata,
            "steps": [],
        }

        formatted = json.dumps(payload, indent=2, ensure_ascii=False)
        destination.write_text(f"{formatted}\n", encoding="utf-8")

        _log_action(
            "scenario.create",
            f"Created scenario {destination.name} (id={safe_id})",
        )
        flash("Scenario created. You can now edit it.", "success")
        return redirect(url_for("admin.edit_scenario", scenario_id=safe_id))

    for errors in form.errors.values():
        for error in errors:
            flash(error, "danger")

    return render_template("admin/new_scenario.html", form=form)


__all__ = [
    "dashboard",
    "delete_scenario",
    "duplicate_scenario",
    "edit_scenario",
    "new_scenario",
    "scenarios",
    "upload_file",
    "uploads",
]
