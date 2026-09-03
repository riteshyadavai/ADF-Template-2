"""BQML smoke: list models in BQML_DATASET. Uses ADC / GOOGLE_APPLICATION_CREDENTIALS."""

from __future__ import annotations

from factories.bqml.factory import make_bqml_client


def main() -> None:
    client = make_bqml_client()
    if not client.enabled:
        raise SystemExit("BQML is disabled. Set BQML_ENABLED=true and BQML_PROJECT / BQML_DATASET.")
    models = client.list_models()
    for row in models:
        print(f"{row.get('model_id')}\t{row.get('model_type')}")
    if not models:
        print("No models in BQML_DATASET")


if __name__ == "__main__":
    main()
