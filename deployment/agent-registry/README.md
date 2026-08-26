# Agent Registry templates

[Agent Registry](https://docs.cloud.google.com/agent-registry/overview) is a
central catalog for the pieces of an agentic system. Its data model has these
resource types: `McpServer`, `Agent`, `Endpoint`, `Skill` / `SkillRevision`,
and `Publisher`.

This folder is organized by category — one subfolder per resource type, each
with a small, editable template:

```
agent-registry/
  common.env                # shared PROJECT_ID / LOCATION
  register.sh               # generic registrar: ./register.sh <resource-dir>
  mcp-servers/              # McpServer resources
    salesforce/             #   -> spec.env + toolspec.json
  agents/                   # Agent resources (A2A agent card)
    example/                #   -> spec.env + agent-card.json
  endpoints/                # Endpoint resources (reachable URL, no spec)
    example/                #   -> spec.env
  skills/                   # Skill resources (separate API — see skills/README.md)
    example/                #   -> skill.json
```

## How it works

`McpServer`, `Agent`, and `Endpoint` are all registered through one API call
(`projects.locations.services.create`) with a different spec field:

| Category | Folder | `SPEC_KIND` | Spec field | Typical `SPEC_TYPE` |
|----------|--------|-------------|------------|---------------------|
| MCP server | `mcp-servers/` | `mcp` | `mcpServerSpec` | `TOOL_SPEC` |
| Agent | `agents/` | `agent` | `agentSpec` | `A2A_AGENT_CARD` |
| Endpoint | `endpoints/` | `endpoint` | `endpointSpec` | `NO_SPEC` |

`Skill` is a separate resource with its own API — see `skills/README.md`.

## Usage

1. Edit `common.env` (project + location).
2. Edit the resource's `spec.env` (and its content file, if any).
3. Register it:

   ```bash
   ./register.sh mcp-servers/salesforce
   ./register.sh agents/example
   ./register.sh endpoints/example
   ```

## Add a new resource

Create a new folder under the right category with a `spec.env` (copy an existing
one) plus any content file it references, then run `./register.sh <that-dir>`.

## Requirements

- `gcloud` authenticated with `roles/agentregistry.editor` (and permission to
  enable services) on the project.
- `LOCATION` must be a region or `global` (the `us`/`eu` multi-regions are not
  supported).

## Verify

```bash
curl -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  https://agentregistry.googleapis.com/v1/projects/PROJECT_ID/locations/LOCATION/services/SERVICE_ID
```
