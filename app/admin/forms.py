"""Form definitions for the admin dashboard."""

from __future__ import annotations

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileRequired, FileField
from wtforms import HiddenField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional, Regexp


class UploadForm(FlaskForm):
    """Upload form restricted to approved snippet and asset types."""

    file = FileField(
        "Snippet File",
        validators=[
            FileRequired(),
            FileAllowed(
                {"html", "htm", "txt", "png", "jpg", "xlsx", "docx", "pdf"},
                "Allowed extensions: .html, .htm, .txt, .png, .jpg, .xlsx, .docx, .pdf",
            ),
        ],
    )
    submit = SubmitField("Upload File")


class ScenarioDuplicateForm(FlaskForm):
    """Duplicate an existing scenario into a new file."""

    source_filename = HiddenField(validators=[DataRequired()])
    new_filename = StringField(
        "New file name",
        validators=[
            DataRequired(),
            Length(max=120),
            Regexp(
                r"^[A-Za-z0-9_.\- ]+$",
                message=(
                    "Use only letters, numbers, spaces, dots, underscores, or hyphens "
                    "for file names."
                ),
            ),
        ],
    )
    submit = SubmitField("Duplicate")


class ScenarioDeleteForm(FlaskForm):
    """Delete a scenario file."""

    filename = HiddenField(validators=[DataRequired()])
    submit = SubmitField("Delete")


class ScenarioCreateForm(FlaskForm):
    """Create a new scenario from the template skeleton."""

    scenario_id = StringField(
        "Scenario ID",
        validators=[
            DataRequired(),
            Length(max=120),
            Regexp(
                r"^[A-Za-z0-9_.\-]+$",
                message=(
                    "Scenario IDs may include letters, numbers, dots, underscores, or hyphens."
                ),
            ),
        ],
    )
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    description = TextAreaField("Description", validators=[Optional(), Length(max=1000)])
    category = StringField(
        "Category",
        validators=[Optional(), Length(max=120)],
        default="General",
    )
    tags = StringField(
        "Tags",
        description="Comma-separated list of tags",
        validators=[Optional(), Length(max=200)],
    )
    submit = SubmitField("Create Scenario")


class ScenarioEditForm(FlaskForm):
    """Edit the JSON contents of a scenario file."""

    content = TextAreaField("Scenario JSON", validators=[DataRequired()])
    submit = SubmitField("Save Changes")


__all__ = [
    "ScenarioCreateForm",
    "ScenarioDeleteForm",
    "ScenarioDuplicateForm",
    "ScenarioEditForm",
    "UploadForm",
]
