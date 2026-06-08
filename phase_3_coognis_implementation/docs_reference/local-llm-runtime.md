# Local LLM Runtime

SYNEXIS now supports a shared local LLM backend for both `ULM` and `PAGE`.

## Backends

- `LOCAL_LLM_BACKEND=mock`
  - safe default
  - keeps current placeholder behavior
  - no GGUF model required

- `LOCAL_LLM_BACKEND=llama_cpp`
  - uses `llama-cpp-python`
  - requires a local GGUF model file
  - used by both `ULM` and `PAGE`

## Required backend env

Add these in `backend/.env`:

```env
LOCAL_LLM_BACKEND=llama_cpp
LOCAL_LLM_MODEL_PATH=./models/llama/model.gguf
LOCAL_LLM_CONTEXT_WINDOW=4096
LLM_MAX_TOKENS=512
LLM_TEMPERATURE=0.2
LOCAL_LLM_THREADS=4
```

## Model file

Place a GGUF model file at the configured path, for example:

```text
backend/models/llama/model.gguf
```

The backend validates this path at startup.

## Dependency

Install backend dependencies again after updating `requirements.txt`:

```bash
cd backend
. .venv/bin/activate
pip install -r requirements.txt
```

## Startup behavior

On startup, the backend now validates the local LLM runtime:

- `mock` mode starts normally
- `llama_cpp` mode fails fast if:
  - `llama_cpp` is not installed
  - `LOCAL_LLM_MODEL_PATH` does not exist
  - the backend name is unsupported

This validation happens before serving requests so PAGE and ULM do not fail later at request time.
