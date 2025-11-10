# Design Overview

This document captures the high-level guardrails that keep the Reflex Agent Demo aligned with its stakeholder storytelling goals.

## Product Requirements

- **Guided storytelling:** The experience should walk an executive audience through curated conversation beats, pairing each assistant response with a visual snippet or artifact.
- **Scenario modularity:** Product, support, or field enablement teams can author new demo flows by dropping JSON files into `data/scenarios/` without redeploying code.
- **Asset reusability:** HTML and Markdown snippets under `data/snippets/` are reusable across scenarios. The interface previews each asset so presenters know what will display before sharing their screen.
- **Secure moderation:** Only administrators can manage scenarios and uploads. Admin accounts are either seeded from environment variables or created through the CLI helper.

## Scenario Schema Expectations

Every scenario file is a JSON object with the following structure:

```json
{
  "id": "unique_scenario_id",
  "metadata": {
    "id": "unique_scenario_id",
    "title": "Human-readable name",
    "description": "Purpose of the walkthrough",
    "category": "Grouping label",
    "tags": ["keyword", "keyword"],
    "order": 1
  },
  "steps": [
    {
      "actor": "user" | "assistant",
      "speaker": "Display name",
      "message": "Spoken line in the transcript",
      "snippet": "optional/path/to/snippet.html",
      "typingDelay": 1200,
      "pause": 600
    }
  ]
}
```

- `actor` determines layout alignment in the chat transcript.
- `snippet` is optional; when present it references a file in `data/snippets/` using a relative path.
- `typingDelay` (milliseconds) simulates the agent thinking before responding.
- `pause` (milliseconds) adds a beat between turns to keep the pacing presenter-friendly.

## UX and Presentation Flow

- **Landing layout:** The mock in [`docs/ui_mock.png`](ui_mock.png) shows the primary framing—sidebar scenario picker, central conversation timeline, right-hand notes panel.
- **Snippet previews:** Admins should see a thumbnail or textual preview of the referenced snippet to avoid guessing what each step reveals.
- **Live narration cues:** Conversation steps highlight the current beat with a color accent so presenters can follow along without reading ahead.
- **Responsive-ready:** While the demo is desktop-first, cards and spacing should gracefully collapse for tablets when sales teams travel.

## Snippet Authoring Guidelines

Snippets live in nested folders under `data/snippets/`, mirroring topical categories:

- Use short, descriptive filenames (e.g., `pdp/personalization.html`).
- Prefer semantic HTML for mockups so screen readers or future automation tools can parse them.
- Include lightweight styling inside the snippet if required—global CSS should live in the main app to avoid duplication.

## Admin Workflow Reminders

- Upload new snippets and JSON scenarios from the `/admin` dashboard; files land in the `instance/uploads/` staging area before you promote them into `data/`.
- Version control curated scenarios. Treat uploads as drafts and merge final assets into the repository for long-term storage.
- Rotate admin credentials regularly and use the `create_admin.py --update` flag when revoking access.
