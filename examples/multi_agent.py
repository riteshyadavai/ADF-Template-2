"""List registered agents (none until you register a manifest)."""

from app.platform import Platform


def main() -> None:
    platform = Platform()
    print("agents:", platform.agents.list_agents() or "(none registered)")


if __name__ == "__main__":
    main()
