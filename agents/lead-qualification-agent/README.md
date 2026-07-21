# Lead Qualification Agent — V1

Single-shot pipeline: raw lead context → structured signal extraction (Groq LLM) → deterministic scoring → letter grade + next action.

## Architecture

```
LeadContext (intake)
       │
       ▼
SignalExtractionAgent  ← Groq API / tool_use (OpenAI-compatible)
       │
       ├── BudgetScorer
       ├── TimelineScorer
       └── IntentScorer
              │
              ▼
        GradingEngine  ← deterministic weighted rubric
              │
              ▼
    QualificationResult (grade A–D + recommended action)
```

## Stack
- Python 3.11+
- `groq` SDK       (signal extraction — OpenAI-compatible)
- `pydantic` v2    (schemas + validation)
- `pytest`         (tests)

## Supported Groq models
| Model | Notes |
|---|---|
| `llama-3.3-70b-versatile` | Default — best tool-use reliability |
| `llama-3.1-70b-versatile` | Good alternative |
| `mixtral-8x7b-32768` | Faster, slightly less accurate on edge cases |

## Quickstart

```bash
pip install -r requirements.txt
cp .env.example .env          # add GROQ_API_KEY
python scripts/run_example.py
```

## Run tests

```bash
pytest tests/ -v
```

## Config

Scoring weights live in `config/rubric.yaml` — edit them without touching code.