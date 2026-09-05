# Architecture

Factory repo (catalog + CLI) → `init` → generated app. The catalog is a build-time menu only. Asset Factory is a separate GitHub package (`uv sync --extra asset-factory`).

![66degrees Factory + Asset Factory architecture](../img/architecture.png)

HTTP hits `app/main.py`. `Platform` (`app/platform.py`) connects `agents/` to `factories/`. Shared types and logging live in `shared/`.
