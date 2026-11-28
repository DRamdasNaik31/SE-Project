# SE-Agentic-Finance

SE-Agentic-Finance is a source-grounded requirements engineering prototype for
Indian cooperative banking software. It uses a Streamlit chat interface and
multiple deterministic agents to retrieve banking requirements, produce
traceable software requirements, and compare SDLC models.

The project is designed to keep source provenance visible and require human
review of generated requirements, regulatory interpretations, and design
decisions.

## What the application does

- Extracts requirements from a page-preserving copy of the IDRBT CBS requirements PDF.
- Retrieves evidence by module or through lexical/embedding search.
- Ingests the Word problem statement as a traceable Agentic AI requirements module.
- Generates structured, page-traceable requirements.
- Classifies requirements and creates quality, compliance, risk, and traceability artifacts.
- Generates user stories, use cases, acceptance criteria, assumptions, and dependency records.
- Checks for duplicate or possible conflicting requirements.
- Recommends an SDLC model using a documented, normalized decision rubric.
- Masks sensitive input and blocks prompt-injection patterns.
- Exports an auditable report bundle and supports human approval gates.
- Supports reviewing, modifying, accepting, rejecting, and regenerating requirement baselines.

## Agent flow

```text
User request
    |
    v
Orchestrator
    |
    +--> Security/sanitization
    |
    +--> Retrieval (Chroma embeddings or lexical fallback)
    |
    +--> Agent 1: structured requirement generation
    |
    +--> Specialist checks: quality, compliance, risk, traceability
    |
    +--> Agent 2: transparent SDLC scoring
    |
    v
Streamlit UI + reviewable artifacts
```

The 13-role specialist registry covers orchestration, interaction, retrieval,
requirements engineering, classification, quality, compliance, security, risk,
traceability, SDLC factors, SDLC decisions, and governance.

## Repository layout

```text
app/
  ui.py                  Streamlit application
  orchestrator.py        Agent routing and session state
  rag.py                 Lexical retrieval and embedding fallback
  rag_index.py           Persistent Chroma/embedding index builder
  agent1.py              Requirement-generation agent
  agent2.py              Transparent SDLC scoring
  analysis_agents.py     Classification and artifact generation
  security.py            Sensitive-data masking and injection detection
  governance.py          Human approval gates and audit logging
  traceability.py        CSV and workflow exports
data/
  raw/                   Source PDF
  processed/             Extracted pages and stable requirement corpus
  training/              Train, validation, and test JSONL splits
models/                  Saved LoRA adapter, if trained
chroma_db/               Persistent local vector index
reports/                 Evaluation and generated review artifacts
tests/                   Dependency-light unit tests
```

## Requirements

- Windows 10/11
- Python 3.11 or 3.12 recommended
- An internet connection for initial package/model downloads
- Optional GPU for practical LoRA fine-tuning and adapter inference

The complete web demonstration only requires the packages in
`requirements.txt`.

## Installation

Clone or open the project directory in Visual Studio Code, then run:

```powershell
cd "D:\OneDrive\Documents\SE Project"
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks virtual-environment activation, enable local scripts for
your terminal session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## Prepare the source corpus

Download the IDRBT CBS requirements PDF from the official publication page:

<http://www.idrbt.ac.in/assets/publications/Reports/CBS_Requirements_for_UCBs.pdf>

Save it as:

```text
data\raw\idrbt_cbs_ucb.pdf
```

Then build the processed corpus:

```powershell
python app\extract_pdf.py data\raw\idrbt_cbs_ucb.pdf
python app\build_corpus.py
python app\extract_problem_statement.py "C:\Users\dramd\Downloads\Problem Statement (2).docx"
python app\create_training_data.py
python app\validate_dataset.py data\training\train.jsonl data\training\validation.jsonl data\training\test.jsonl
python app\evaluate.py
python app\export_artifacts.py
```

The corpus builder assigns stable IDs in module-specific prefixes, for example
`LOAN-001`, `REG-001`, and `GL-001`, and preserves PDF page numbers.

## Optional vector retrieval

Install the ML dependencies and build the local Chroma index:

```powershell
python -m pip install -r requirements-ml.txt
python -c "from app.rag_index import build_index; print(build_index())"
```

The optional index uses `sentence-transformers/all-MiniLM-L6-v2`. If embedding
packages or the index are unavailable, the application automatically falls back
to dependency-light lexical retrieval.

## SDLC recommendation factors

The Streamlit sidebar allows users to set requirement stability, stakeholder
feedback, and delivery pressure before requesting an SDLC recommendation. The
decision engine ranks Waterfall, V-Shaped, Prototype, Iterative, and Spiral
models, plus Extreme Programming (XP), Scrum, and Dynamic Systems Development
Method (DSDM), with a normalized transparent score.

## Run the application

From the project directory:

```powershell
python -m streamlit run app\ui.py
```

Open the local URL printed by Streamlit, usually
<http://localhost:8501>.

### Example prompts

```text
Generate software requirements for loans
Generate requirements for Account Opening
Generate requirements for Regulatory Requirements
Which SDLC model fits this project?
Show the evidence for these requirements
```

If you ask for broad requirements such as "requirements for finance", the chat
will list the available sub-branches and ask you to choose one. Reply with a
branch such as "loan" or "Loan Processing" and the app generates requirements
for it without needing you to repeat the request. Results remain grouped by
branch in the current session, so generating another branch does not replace
the previous branch's requirements. Each branch returns up to 25 source-grounded
requirements, ranked by lexical relevance; branches with fewer source fragments
return fewer.

Use the two agents in sequence: first ask for requirements, then ask for an SDLC
recommendation. Both are available in the same Streamlit chat page, but the
orchestrator routes requirement requests to Agent 1 and routes a later SDLC
request to Agent 2. Agent 2 uses the requirements already generated in that
session. If asked for an SDLC recommendation before any requirements exist, the
application asks the user to generate requirements first.

The available module names include Account Opening, Customer Information,
Cheque Book Facility, Service Branches and Clearing, Cash Department at Branch,
Cash Credit and Overdraft, Loan Processing, Bills, Remittances, Interest and Fee
Calculation, Transaction Posting, Safe Custody Facility, Tax Calculation,
Lockers, General Ledger, Regulatory Requirements, Head Office, and Reports.

## Adapter mode

The sidebar has a **Use trained LoRA adapter** option. It is disabled by
default because CPU inference can take several minutes for a response.

- **Fast grounded mode:** uses real corpus evidence and deterministic structured requirements.
- **Adapter mode:** uses the saved LoRA adapter at `models\agent1_lora` when the
  environment can load the base model and adapter dependencies.
- **Safety fallback:** invalid or unparseable model output is replaced by the
  conservative source-grounded fallback.

No API keys or model weights need to be committed to the repository.

## Training a LoRA adapter

Install `requirements-ml.txt` and run:

```powershell
python app\train_agent1.py ^
  --train data\training\train.jsonl ^
  --validation data\training\validation.jsonl ^
  --output models\agent1_lora
```

The training entry point uses the Qwen2.5-1.5B-Instruct base model and PEFT LoRA.
It enables 4-bit NF4 quantization when CUDA and compatible libraries are
available. Review the base-model license and local hardware compatibility before
training.

The command uses a 768-token maximum sequence length, LoRA rank 8, batch size 1,
gradient accumulation 8, and one training epoch by default.

## Evaluation

Run the offline test suite:

```powershell
python -m unittest discover -s tests -v
python -m compileall -q app tests
```

Evaluate the held-out test set:

```powershell
python app\evaluate.py
python app\evaluate_models.py
```

Outputs are written to `reports\evaluation.json` and
`reports\model_comparison.json`.

The generated project artifacts can be refreshed with:

```powershell
python app\export_artifacts.py
```

This creates or updates files such as:

- `reports\srs.json`
- `reports\quality_findings.json`
- `reports\compliance_control_matrix.json`
- `reports\risk_register.json`
- `reports\traceability.json`
- `reports\open_issues.json`
- `reports\sdlc.json`
- `reports\conflict_findings.json`
- `reports\user_stories.json`
- `reports\use_cases.json`
- `reports\assumptions_and_dependencies.json`

## Current project metrics

The processed real-corpus run contains:

- 112 source PDF pages
- 1,682 page-traceable fragments
- 85 problem-statement fragments
- 1,767 combined fragments
- 18 functional modules
- 1,345 training examples
- 168 validation examples
- 169 test examples

The offline evaluation reports 100% schema validity, retrieval coverage, and
requirement evidence coverage on the test set. These are implementation metrics,
not domain-expert validation and not proof of legal or regulatory correctness.

The completed base-versus-fine-tuned comparison reports 100% schema validity
and 100% retrieval coverage for both paths. The tuned adapter was actually used
for 78.7% of held-out examples; 21.3% used the conservative fallback because
the generated output did not meet the required JSON schema.

## Governance and human review

AI output is advisory in this project. Requirements and SDLC selections are
marked `pending_human_review`. Approval gates cover requirement baselines,
regulatory interpretation, high-risk security decisions, stakeholder conflicts,
architecture-critical choices, SDLC selection, requirement changes, and
production readiness.

The governance module requires an authorised human actor and records events in
`reports\audit_log.jsonl`. It does not provide self-approval.

## Limitations

- The source PDF is required and is not embedded in the repository.
- PDF text quality and heading extraction can affect corpus completeness.
- Regulatory mappings are review prompts, not legal advice or a compliance
  certification.
- No authentication, MFA, RBAC, encryption-at-rest, or production infrastructure
  is implemented.
- Model inference is local and may require substantial memory or CPU time.
- Expert banking, compliance, security, and acceptance testing are still required.

## License and responsibility

Use the IDRBT source material according to its publication terms. Review all
generated requirements, risks, compliance mappings, and SDLC recommendations
with qualified project, security, legal, and compliance stakeholders before use
in a production banking system.
