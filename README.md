# RepoLens — Local Repository Analysis Agent

A read-only, local-first AI agent that investigates source code using Ollama tool calling. It records runs and tool metadata in SQLite and includes deterministic tests and a small heuristic evaluation. Designed as a learning and portfolio starter, not a production security sandbox.

## Architecture

```text
CLI → Orchestrator → Ollama model
        │              ↕ tool requests/results
        ├→ bounded list / search / read tools → repository
        └→ SQLite: run status, answers, tool metadata, eval checks
```

The agent loops over model responses, validates tool names and arguments, executes read-only tools, feeds results back, and stops at a tool-call limit. Project content is untrusted; tool access is bounded to a selected directory. Runs record `running`, `completed`, `stopped`, or `failed` status. No commands or edits are exposed to the model.

## Windows quick start

Install Python and [Ollama](https://ollama.com/), then in PowerShell from this project folder:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
ollama pull qwen3:8b
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m repo_agent ask ".\fixtures\sample_project" "Read login.py and explain the login conditions."
.\.venv\Scripts\python.exe -m repo_agent history
.\.venv\Scripts\python.exe -m repo_agent show 1
.\.venv\Scripts\python.exe -m repo_agent eval
```

The local Ollama application/service needs to be running. Change the model using `--model MODEL_NAME`; it must support tool calling. Use `--db PATH` before the subcommand to select a different SQLite database. Model downloads and inference have hardware, electricity, and network costs; no paid model API is required.

## Tests and evaluation

`unittest` runs offline using a fake model client and a temporary SQLite database. The evaluation calls the real local model, records checks in SQLite, and checks for keywords. Keyword checks do **not** establish correctness; manually review the explanation. The fixture deliberately contains hardcoded demo credentials, not production authentication.

## Privacy and limitations

- Runs store project paths, questions, answers and tool names in `data/agent.db`; answers can contain source code or secrets. This folder is ignored by Git. Delete it to clear history.
- The tool layer blocks path escapes, common excluded names, sensitive extensions, and symlinks, and bounds output. It is **not** a security sandbox: race conditions, unanticipated secret names, prompt injection, and malicious repositories remain risks. Use only trusted, non-sensitive projects. Do not expose this application publicly or connect production data.
- Search inspects at most the first 100 listed files; results can be incomplete. No semantic retrieval, edit support, authorization, distributed deployment, MLflow integration, or multi-agent delegation is implemented.
- Model responses are nondeterministic and can be inaccurate. No performance or accuracy claims are implied.

## Resume guidance

Use only after you build, test, and understand the work. Example: “Built a local-first repository analysis agent using Python, Ollama tool calling, and SQLite; implemented bounded read-only tools, run history, and automated safety and evaluation checks.” Add measured results only after conducting and documenting real experiments. This project alone does not establish years of experience.
