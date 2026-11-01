"""Explicit paid, synthetic live checks; never run as part of pytest or startup."""

import argparse
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from pydantic import ValidationError

from career_assistant.ai import AIError, AIResult, OpenAIClient
from career_assistant.ai_evaluation import Arithmetic, cases, evaluate_case
from career_assistant.config import Settings


def result_record(
    name: str, result: AIResult, checks: dict, requested_model: str
) -> dict:
    cost = result.usage.estimated_cost_usd(requested_model)
    return {
        "case": name,
        "model": result.model,
        "passed": all(checks.values()),
        "checks": checks,
        "elapsed_seconds": round(result.elapsed_seconds, 3),
        "usage": asdict(result.usage),
        "estimated_cost_usd": str(cost) if cost is not None else None,
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["smoke", "evaluate"])
    parser.add_argument("--report", type=Path, help="Write sanitized JSON results")
    args = parser.parse_args(argv)
    records = []
    client = None
    try:
        settings = Settings()
        client = OpenAIClient(settings)
        if args.command == "smoke":
            result = client.complete(
                instructions="Compute the arithmetic question as a structured answer.",
                data={"question": "2+2"},
                response_type=Arithmetic,
            )
            records.append(
                result_record(
                    "arithmetic",
                    result,
                    {"answer_is_4": result.value.answer == 4},
                    settings.ai_model,
                )
            )
        else:
            for case in cases():
                result, checks = evaluate_case(client, case)
                records.append(
                    result_record(case.name, result, checks, settings.ai_model)
                )
        report = {
            "checked_at": datetime.now(UTC).isoformat(),
            "requested_model": settings.ai_model,
            "reasoning_effort": settings.ai_reasoning_effort,
            "max_input_tokens": settings.ai_max_input_tokens,
            "max_output_tokens": settings.ai_max_output_tokens,
            "results": records,
        }
    except AIError as error:
        report = {
            "error": {"code": error.code, "message": str(error)},
            "results": records,
        }
        if error.usage is not None:
            report["error"]["usage"] = asdict(error.usage)
    except ValidationError:
        parser.exit(
            1, "Invalid backend AI settings. Check .env without sharing its contents.\n"
        )
    finally:
        if client is not None:
            client.close()
    output = json.dumps(report, indent=2)
    if args.report:
        args.report.write_text(output + "\n", encoding="utf-8")
    print(output)
    if "error" in report or not all(record["passed"] for record in records):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
