"""Secrets factory."""

from __future__ import annotations

from config.settings import Settings, get_settings
from factories.secrets.env.client import EnvSecretsProvider
from factories.secrets.protocol import SecretsProvider


def make_secrets_provider(settings: Settings | None = None) -> SecretsProvider:
    settings = settings or get_settings()
    backend = settings.security.secrets_backend
    if backend == "env":
        return EnvSecretsProvider()
    if backend == "vault":
        from factories.secrets.vault.client import VaultSecretsProvider

        return VaultSecretsProvider()
    if backend == "aws_secrets_manager":
        from factories.secrets.aws_secrets_manager.client import AwsSecretsProvider

        return AwsSecretsProvider()
    if backend == "sops":
        from factories.secrets.sops.client import SopsSecretsProvider

        return SopsSecretsProvider()
    return EnvSecretsProvider()
