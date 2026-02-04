# QUADAS-2 Assessment Agent

Prototype agent for structured, evidence-anchored QUADAS-2 risk of bias assessment in diagnostic accuracy studies.

## Features

- **Hallucination-proof architecture**: LLM returns line IDs only, not generated quotes
- **Domain 2 (Index Test)**: Assesses blinding and threshold pre-specification
- **Two-step process**: Extract evidence → Make judgement
- **Structured JSON output**: Schema-validated results with evidence quotes
- **Local LLM**: Runs on Ollama (no API costs)

## Architecture

The agent uses a line-ID based extraction system that **architecturally prevents hallucinations**:

1. **Extractor**: Identifies line numbers containing relevant evidence
2. **Verifier**: Python extracts verbatim quotes from source text using line IDs
3. **Judge**: Makes QUADAS-2 judgements based on verified evidence only

## Prerequisites

- Python 3.12+ (tested with 3.14)
- [Ollama](https://ollama.com/download) installed
- macOS (or Linux/Windows with minor path adjustments)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/JohnsonLy78/quadas_agent.git
cd quadas_agent
```

2. Create and activate virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install requests jsonschema python-dotenv
```

4. Install and start Ollama:
```bash
# Install Ollama from https://ollama.com/download
# Or via Homebrew:
brew install ollama

# Start Ollama (keep running in background)
ollama serve &

# Pull the model (7B recommended for better accuracy)
ollama pull qwen2.5:7b
```

## Usage

Run the agent on the sample study:

```bash
# Make sure Ollama is running
# Make sure virtual environment is activated
source .venv/bin/activate

# Run the assessment
python main.py
```

The agent will:
1. Read `sample_input/smith_2022.txt`
2. Extract evidence using line IDs (no hallucination possible)
3. Make QUADAS-2 Domain 2 judgements
4. Validate against JSON schema
5. Save results to `outputs/smith_2022_index_test.json`

## Project Structure

```
quadas_agent/
├── main.py                          # Main agent script
├── prompts/
│   └── index_test/
│       ├── extract.txt              # Line-ID extractor prompt
│       └── judge.txt                # QUADAS-2 judge prompt
├── schema/
│   └── index_test_result.json       # JSON schema for validation
├── sample_input/
│   └── smith_2022.txt               # Sample study text
├── outputs/                         # Generated assessments
│   └── smith_2022_index_test.json
└── README.md
```

## Configuration

Optional: Create a `.env` file to customize settings:

```bash
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
```

## Model Recommendations

- **qwen2.5:7b** (recommended): Best balance of accuracy and speed
- **qwen2.5:3b**: Faster but may miss evidence
- **llama3.2:3b**: Alternative 3B model

## Example Output

```json
{
  "study_id": "smith_2022",
  "domain": "index_test",
  "risk_of_bias": "Unclear",
  "applicability_concern": "Low",
  "signalling_answers": {
    "blinded_to_reference_standard": {
      "judgement": "Unclear",
      "rationale": "Blinding of index test interpretation was not reported."
    },
    "threshold_pre_specified": {
      "judgement": "Low",
      "rationale": "The positivity threshold specified by the manufacturer was applied."
    }
  },
  "evidence_quotes": [
    {
      "quote": "The positivity threshold specified by the manufacturer was applied.",
      "location": "Line 17"
    }
  ],
  "missing_evidence": [
    "Blinding of index test interpretation not reported."
  ]
}
```

## Key Design Decisions

### Why Line IDs?

LLMs frequently hallucinate evidence quotes. By having the LLM return only line numbers and letting Python extract the actual text, hallucination becomes **architecturally impossible**.

### Why Two Steps?

Separating extraction from judgement allows the extractor to be conservative (reducing false positives) while the judge focuses on applying QUADAS-2 rules to verified evidence.

### Why Local LLM?

- **Zero API costs**: Run unlimited assessments for free
- **Privacy**: Study data never leaves your machine
- **Reproducibility**: Fixed model versions for consistent results

## Limitations

- Currently supports Domain 2 (Index Test) only
- Requires manual review of assessments
- Model may miss evidence if phrasing is unusual
- English-language studies only

## Future Work

- Add remaining QUADAS-2 domains (Patient Selection, Reference Standard, Flow & Timing)
- Support for PDF input with OCR
- Batch processing mode
- Web interface
- Multi-language support

## License

MIT

## Citation

If you use this agent in your research, please cite:
```
[Citation details TBD]
```

## Contact

[Your contact information]
