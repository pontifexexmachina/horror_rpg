# Simulator Bootstrap

The simulator uses a normal Python project layout with `uv`, but this machine did not have Python or `uv` on `PATH` when the simulator was first scaffolded.

The repository does **not** track local toolchain binaries under `tools/`. Treat `tools/` as disposable local bootstrap infrastructure.

## Preferred Setup

If Python 3.12+ and `uv` are already installed on your machine:

```powershell
uv sync --extra dev
uv run pytest
uv run basedpyright
uv run ruff check src tests pyproject.toml
uv run ruff format --check src tests pyproject.toml
```

## Windows Bootstrap Without Global Python

If the machine has no usable Python installation, bootstrap a local runtime into `tools/` and keep it untracked.

### 1. Create `tools/`

```powershell
New-Item -ItemType Directory -Force -Path '.\tools' | Out-Null
```

### 2. Download embedded Python 3.12

```powershell
Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip' -OutFile '.\tools\python-embed.zip'
Expand-Archive -Path '.\tools\python-embed.zip' -DestinationPath '.\tools\python312' -Force
```

### 3. Download `uv`

```powershell
Invoke-WebRequest -Uri 'https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.zip' -OutFile '.\tools\uv.zip'
Expand-Archive -Path '.\tools\uv.zip' -DestinationPath '.\tools\uv' -Force
```

### 4. Use repo-local cache directories

This environment may block writes to the default user-level `uv` cache, so point `uv` at a repo-local cache.

```powershell
$env:UV_CACHE_DIR = "$PWD\.uv-cache"
```

### 5. Create the virtual environment and install dependencies

```powershell
& '.\tools\uv\uv.exe' sync --python '.\tools\python312\python.exe' --extra dev
```

### 6. Run checks through the local toolchain

```powershell
$env:UV_CACHE_DIR = "$PWD\.uv-cache"
$env:RUFF_CACHE_DIR = "$PWD\.ruff-cache-local"
& '.\tools\uv\uv.exe' run pytest
& '.\tools\uv\uv.exe' run basedpyright
& '.\tools\uv\uv.exe' run ruff check src tests pyproject.toml
& '.\tools\uv\uv.exe' run ruff format --check src tests pyproject.toml
```

## Notes

- `uv.lock` is tracked and should remain the dependency source of truth.
- `.venv/`, `.uv-cache/`, `tools/`, and Ruff/Pytest caches are local-only.
- Once a machine has a normal Python + `uv` installation, the repo-local `tools/` directory can be deleted.
