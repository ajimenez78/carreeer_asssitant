"""Validate synthetic mock payloads against the existing backend, without HTTP or DB."""

import json
from pathlib import Path

from career_assistant.api import schemas
from career_assistant import workflow

samples = json.loads(Path("frontend/test-results/mock-contract.json").read_text())
for sample in samples:
    model = getattr(schemas, sample["schema"], None) or getattr(workflow, sample["schema"])
    model.model_validate(sample["value"])
print(f"Validated {len(samples)} synthetic mock payloads against Part 7 Pydantic schemas.")
