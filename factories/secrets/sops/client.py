"""Planned SOPS secrets backend."""

from factories.secrets.protocol import SecretsProvider


class SopsSecretsProvider(SecretsProvider):
    def get_secret(self, name: str) -> str | None:
        raise NotImplementedError("SOPS is planned. Use SECURITY_SECRETS_BACKEND=env.")
