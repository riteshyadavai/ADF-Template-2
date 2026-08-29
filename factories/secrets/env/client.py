"""Environment-variable secrets."""

from __future__ import annotations

import os

from factories.secrets.protocol import SecretsProvider


class EnvSecretsProvider(SecretsProvider):
    def get_secret(self, name: str) -> str | None:
        return os.getenv(name)
