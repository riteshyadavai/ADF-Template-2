"""Looker API smoke: init40 + me(). Set LOOKER_ENABLED and LOOKERSDK_* credentials."""

from __future__ import annotations

from factories.looker.factory import make_looker_client


def main() -> None:
    client = make_looker_client()
    if not client.enabled:
        raise SystemExit("Looker is disabled. Set LOOKER_ENABLED=true and LOOKERSDK_* credentials.")
    user = client.me()
    print(user.get("email") or user.get("first_name") or user)


if __name__ == "__main__":
    main()
