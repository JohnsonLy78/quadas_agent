# QUADAS-2 Assessment Agent

Hallucination-proof QUADAS-2 risk of bias assessment agent for diagnostic accuracy studies.

## Scope

- **Domain 2 (Index Test)** only
- Assesses blinding and threshold pre-specification
- Returns structured JSON output with evidence quotes
- Runs locally with Ollama (no API costs)

## How to Run

1. **Install Ollama** from https://ollama.com/download

2. **Start Ollama and pull model:**
```bash
ollama serve &
ollama pull qwen2.5:7b
```

3. **Set up Python environment:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install requests jsonschema python-dotenv
```

4. **Run the agent:**
```bash
python main.py
```

Results saved to `outputs/smith_2022_index_test.json`


