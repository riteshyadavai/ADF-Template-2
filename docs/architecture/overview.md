# Architecture

HTTP hits `app/main.py`. `Platform` (`app/platform.py`) connects `agents/` to `factories/`. Shared types and logging live in `shared/`.
