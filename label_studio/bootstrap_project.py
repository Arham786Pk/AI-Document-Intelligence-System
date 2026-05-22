"""Create the Milestone 2 annotation project in a running Label Studio instance.

Prerequisites:
    1. Label Studio installed:  pip install label-studio
    2. Server running:          label-studio start   (default http://localhost:8080)
    3. Log in once in the browser, then copy your Access Token from
       Account & Settings > Access Token.

Run:
    set LABEL_STUDIO_URL=http://localhost:8080
    set LABEL_STUDIO_TOKEN=<your-token>
    python label_studio/bootstrap_project.py

Creates the project "FR Invoice M2 — 12 Entities" with the 12-label NER config
and imports label_studio/test_task.json so you can immediately test labeling.
"""

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONFIG = (HERE / "label_config.xml").read_text(encoding="utf-8")
TEST_TASK = HERE / "test_task.json"

URL = os.environ.get("LABEL_STUDIO_URL", "http://localhost:8080")
TOKEN = os.environ.get("LABEL_STUDIO_TOKEN")


def main():
    if not TOKEN:
        sys.exit("Set LABEL_STUDIO_TOKEN (Account & Settings > Access Token).")

    try:
        from label_studio_sdk.client import LabelStudio
    except ImportError:
        sys.exit("label-studio-sdk not found. Run: pip install label-studio-sdk")

    client = LabelStudio(base_url=URL, api_key=TOKEN)

    project = client.projects.create(
        title="FR Invoice M2 — 12 Entities",
        description="Milestone 2 annotation: 12 entities incl. CONSUMER_NAME.",
        label_config=CONFIG,
    )
    print(f"Created project id={project.id}: {project.title}")

    if TEST_TASK.exists():
        import json
        tasks = json.loads(TEST_TASK.read_text(encoding="utf-8"))
        client.projects.import_tasks(id=project.id, request=tasks)
        print(f"Imported {len(tasks)} test task(s).")

    print(f"Open: {URL}/projects/{project.id}/")


if __name__ == "__main__":
    main()
