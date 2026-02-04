import json
import os
from pathlib import Path
import requests

from dotenv import load_dotenv
load_dotenv()

import jsonschema

# --------- Config ---------
STUDY_ID = "smith_2022"
STUDY_TEXT_PATH = Path("sample_input/smith_2022.txt")

EXTRACT_PROMPT_PATH = Path("prompts/index_test/extract.txt")
JUDGE_PROMPT_PATH = Path("prompts/index_test/judge.txt")

SCHEMA_PATH = Path("schema/index_test_result.json")

# Ollama config
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")  # more capable for complex tasks


# --------- Helpers ---------
def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def number_lines(text: str) -> tuple[str, dict]:
    """
    Number each line in the text and return:
    - numbered_text: Text with [LINE_N] prefix on each line
    - line_map: Dict mapping line_id -> original text
    """
    lines = text.split("\n")
    numbered_lines = []
    line_map = {}
    
    for i, line in enumerate(lines, start=1):
        numbered_lines.append(f"[LINE_{i}] {line}")
        line_map[i] = line.strip()
    
    return "\n".join(numbered_lines), line_map


def extract_evidence_from_line_ids(line_ids: list, line_map: dict, topic: str) -> list:
    """
    Convert line IDs to evidence quote objects.
    Filters out invalid line IDs safely.
    """
    evidence = []
    for line_id in line_ids:
        if line_id in line_map and line_map[line_id]:
            evidence.append({
                "quote": line_map[line_id],
                "location": f"Line {line_id}",
                "topic": topic
            })
    return evidence


def call_llm(system_prompt: str, user_payload: str) -> str:
    """
    Calls Ollama locally via HTTP and returns raw text. We expect JSON text.
    """
    url = f"{OLLAMA_URL}/api/chat"
    
    # Add explicit JSON-only instruction
    enhanced_system = f"""{system_prompt}

CRITICAL: You MUST respond with ONLY valid JSON. Do not include any explanations, markdown formatting, or text outside the JSON object. Start your response with {{ and end with }}. Follow the exact output format specified in the prompt."""
    
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": enhanced_system},
            {"role": "user", "content": user_payload},
        ],
        "stream": False,
        # Don't force JSON mode - let model follow prompt structure
        "options": {
            "temperature": 0,  # deterministic
        }
    }
    
    resp = requests.post(url, json=payload)
    resp.raise_for_status()
    return resp.json()["message"]["content"].strip()


def must_json(text: str) -> dict:
    """
    Strict JSON parsing. If the model returns extra text, this will fail.
    """
    # Try to extract JSON if wrapped in markdown code blocks
    text = text.strip()
    if text.startswith("```"):
        # Remove markdown code fences
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        text = text.strip()
        if text.startswith("json"):
            text = text[4:].strip()
    
    # Try to find JSON object boundaries
    if "{" in text:
        start = text.find("{")
        # Find matching closing brace
        count = 0
        end = start
        for i in range(start, len(text)):
            if text[i] == "{":
                count += 1
            elif text[i] == "}":
                count -= 1
                if count == 0:
                    end = i + 1
                    break
        if end > start:
            text = text[start:end]
    
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"\n❌ Failed to parse JSON. Raw response:\n{text}\n")
        raise


def validate_schema(obj: dict, schema: dict) -> None:
    jsonschema.validate(instance=obj, schema=schema)


# --------- Main ---------
def main():
    # Basic file sanity checks
    for p in [STUDY_TEXT_PATH, EXTRACT_PROMPT_PATH, JUDGE_PROMPT_PATH, SCHEMA_PATH]:
        if not p.exists():
            raise FileNotFoundError(f"Missing file: {p}")

    study_text = read_text(STUDY_TEXT_PATH)
    extract_prompt = read_text(EXTRACT_PROMPT_PATH)
    judge_prompt = read_text(JUDGE_PROMPT_PATH)
    schema = json.loads(read_text(SCHEMA_PATH))

    # ---- Step 1: Extract evidence using line IDs (no hallucination possible) ----
    numbered_text, line_map = number_lines(study_text)
    
    extract_user_payload = (
        f"study_id: {STUDY_ID}\n\n"
        f"NUMBERED STUDY TEXT:\n{numbered_text}\n\n"
        "Return JSON with line IDs only."
    )

    extract_raw = call_llm(extract_prompt, extract_user_payload)
    line_ids_result = must_json(extract_raw)
    print(f"\n📋 EXTRACTED LINE IDs:\n{json.dumps(line_ids_result, indent=2)}\n")
    
    # Convert line IDs to actual evidence quotes (hallucination-proof)
    evidence_quotes = []
    evidence_quotes.extend(
        extract_evidence_from_line_ids(
            line_ids_result.get("index_test_blinding_line_ids", []),
            line_map,
            "index_test_blinding"
        )
    )
    evidence_quotes.extend(
        extract_evidence_from_line_ids(
            line_ids_result.get("threshold_line_ids", []),
            line_map,
            "threshold"
        )
    )
    
    extracted = {
        "study_id": STUDY_ID,
        "evidence_quotes": evidence_quotes,
        "not_found": line_ids_result.get("not_found", [])
    }
    print(f"\n✅ VERIFIED EVIDENCE (from actual text):\n{json.dumps(extracted, indent=2, ensure_ascii=False)}\n")

    # ---- Step 2: Judge using extracted evidence ----
    judge_user_payload = json.dumps(
        {"study_id": STUDY_ID, "extracted": extracted},
        ensure_ascii=False,
        indent=2,
    )

    judge_raw = call_llm(judge_prompt, judge_user_payload)
    print(f"\n📊 JUDGE RAW:\n{judge_raw[:500]}...\n")
    result = must_json(judge_raw)

    # ---- Validate schema ----
    validate_schema(result, schema)

    # ---- Print + Save ----
    print("\n✅ FINAL RESULT (schema-valid):\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    out_dir = Path("outputs")
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"{STUDY_ID}_index_test.json"
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved to: {out_path}\n")


if __name__ == "__main__":
    main()
