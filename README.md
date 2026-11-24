# SE-Agentic-Finance

A source-grounded finance requirements engineering prototype with two cooperating
agents:

1. **Agent 1** retrieves evidence and returns traceable structured requirements.
2. **Agent 2** applies an explicit, normalized SDLC rubric and explains its ranking.

The implementation is intentionally conservative: it does not invent source
evidence and reports when the corpus has not been loaded.

## Current status

| Area | Status |
| --- | --- |
| PDF extraction and page preservation | Implemented |
| Corpus cleaning and stable IDs | Implemented |
| Training-data generation, validation, and split | Implemented |
| Embedding source-grounded retrieval | Implemented; Chroma index built at `chroma_db` |
| Lexical retrieval fallback | Implemented when embedding dependencies/index are unavailable |
| Agent 1 structured output | Implemented with offline fallback |
| Agent 2 transparent SDLC scoring | Implemented |
| Orchestration, session memory, follow-up SDLC requests | Implemented |
| Streamlit UI and execution trace | Implemented |
| Offline schema/grounding evaluation | Implemented |
| Genuine LoRA/QLoRA training | Complete: Qwen2.5-1.5B LoRA adapter trained and verified |
| Vector embeddings and Chroma index | Implemented in `app\rag_index.py`; lexical retrieval remains the safe fallback |
| Real source corpus | Implemented: 112-page IDRBT PDF processed into 1,682 fragments across 18 modules |
| Input masking, prompt-injection detection, source allowlisting, approval gates, audit log, traceability export | Implemented |
| Specialist classification, quality checks, compliance matrix, risk register, SRS bundle | Implemented |
| Base-vs-tuned comparison reporting | Complete on 169 held-out examples; see `reports\model_comparison.json` |
| RBAC/MFA, encryption, production deployment | Future work requiring infrastructure and security review |

This status is deliberate and avoids claiming that RAG or prompt engineering is
fine-tuning.

## Windows setup

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Download the IDRBT source PDF from the official publication link:
<http://www.idrbt.ac.in/assets/publications/Reports/CBS_Requirements_for_UCBs.pdf>
and save it as `data\raw\idrbt_cbs_ucb.pdf`.

Then run:

```powershell
python app\extract_pdf.py data\raw\idrbt_cbs_ucb.pdf
python app\build_corpus.py
python app\create_training_data.py
python app\validate_dataset.py data\training\train.jsonl data\training\validation.jsonl data\training\test.jsonl
python app\evaluate.py
python app\export_artifacts.py
streamlit run app\ui.py
```

Optional local embedding index:

```powershell
python -c "from app.rag_index import build_index; print(build_index())"
```

The current environment built the Chroma index successfully for all 1,682
requirements. Retrieval uses that index automatically and falls back to lexical
retrieval if the embedding runtime is unavailable.

Traceability export and approval gates are available through
`app\traceability.py` and `app\governance.py`. They require an authorised human
actor for regulated decisions; the application does not self-approve them.

The UI can answer greetings, retrieve requirements, show evidence, and score
SDLC models after requirements have been generated.

For a fast professor demonstration, leave **Use trained LoRA adapter** unchecked
in the sidebar. This uses the real Chroma evidence and deterministic structured
requirements. On this CPU-only machine, enabling the adapter can take several
minutes per request; use it only when demonstrating the fine-tuned path.

When a request names a recognized module, fast grounded mode returns the complete
module corpus rather than a top-k sample. For example, Loan Processing returns
all extracted Loan Processing requirements, including modules with hundreds of
items.

The current real-corpus run produced:

- 1,682 page-traceable fragments
- 18 functional modules
- Training split: 1,345 train / 168 validation / 169 test
- Schema validity: 100%
- Retrieval coverage: 100%
- Requirement evidence coverage: 100%

These are pipeline metrics, not claims of domain correctness; expert evaluation
is still required.

The completed held-out comparison recorded 100% schema validity and retrieval
coverage for both paths. The trained adapter was used for 78.7% of tuned
examples; the remaining cases used the conservative fallback because generated
model output did not meet the required JSON schema. This is reported honestly
and is not counted as tuned-model success.

## Optional ML phase

Install `requirements-ml.txt` only if you want to execute model fine-tuning. It
is not required to run the verified CPU-safe prototype. If installed, check the local CUDA/PyTorch and
bitsandbytes compatibility. The RTX 3050 4 GB target requires QLoRA, small
batches, gradient accumulation, and a reviewed sequence length:

```powershell
python -m pip install -r requirements-ml.txt
python app\train_agent1.py --train data\training\train.jsonl --validation data\training\validation.jsonl
```

No API keys or model weights belong in this repository.

## Verification

The dependency-light verification command is:

```powershell
python -m unittest discover -s tests -v
python -m compileall -q app tests
```

The current test suite covers stable corpus IDs, normalized SDLC scores, and
sensitive-input/prompt-injection handling. It does not substitute for
domain-expert evaluation on the real banking document.

## Scope mapping

The full problem statement describes 13 agents and production governance. This
implementation now provides a 13-role specialist registry plus explicit
safety, governance, traceability, and evaluation scaffolding. Regulatory/legal
interpretations, identity infrastructure, encryption, and production readiness
still require authorised human and infrastructure work.
