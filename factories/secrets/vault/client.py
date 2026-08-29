"""Planned Vault secrets backend."""

from factories.secrets.protocol import SecretsProvider


class VaultSecretsProvider(SecretsProvider):
    def get_secret(self, name: str) -> str | None:
        raise NotImplementedError("Vault secrets are planned. Use SECURITY_SECRETS_BACKEND=env.")
