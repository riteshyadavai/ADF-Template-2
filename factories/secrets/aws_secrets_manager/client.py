"""Planned AWS Secrets Manager backend."""

from factories.secrets.protocol import SecretsProvider


class AwsSecretsProvider(SecretsProvider):
    def get_secret(self, name: str) -> str | None:
        raise NotImplementedError(
            "AWS Secrets Manager is planned. Use SECURITY_SECRETS_BACKEND=env."
        )
