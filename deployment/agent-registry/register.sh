#!/usr/bin/env bash
# Register any Agent Registry "service" (mcp-server | agent | endpoint).
#
# Usage:
#   ./register.sh <resource-dir>
#   e.g. ./register.sh mcp-servers/salesforce
#        ./register.sh agents/example
#        ./register.sh endpoints/example
#
# Skills use a different API resource — see skills/README-note in the README.
set -euo pipefail
cd "$(dirname "$0")"

DIR="${1:?Usage: ./register.sh <resource-dir> (e.g. mcp-servers/salesforce)}"
[[ -f "${DIR}/spec.env" ]] || { echo "No spec.env in ${DIR}" >&2; exit 1; }

# Clear optional vars so a value from the caller's env can't leak into a
# resource that doesn't set it (e.g. an A2A agent must have no interfaces).
unset SPEC_TYPE CONTENT_FILE SERVER_URL PROTOCOL_BINDING DESCRIPTION

set -a; source ./common.env; source "./${DIR}/spec.env"; set +a

BASE="https://agentregistry.googleapis.com/v1"
PARENT="projects/${PROJECT_ID}/locations/${LOCATION}"
TOKEN="$(gcloud auth print-access-token)"

gcloud services enable agentregistry.googleapis.com --project="${PROJECT_ID}"

BODY="$(RES_DIR="${DIR}" python3 <<'PY'
import json, os

kind = os.environ["SPEC_KIND"]  # mcp | agent | endpoint
spec_field = {"mcp": "mcpServerSpec", "agent": "agentSpec", "endpoint": "endpointSpec"}[kind]

spec = {"type": os.environ.get("SPEC_TYPE", "NO_SPEC")}
content_file = os.environ.get("CONTENT_FILE", "")
if content_file:
    with open(os.path.join(os.environ["RES_DIR"], content_file)) as f:
        spec["content"] = json.load(f)

body = {
    "displayName": os.environ["DISPLAY_NAME"],
    "description": os.environ.get("DESCRIPTION", ""),
    spec_field: spec,
}

url = os.environ.get("SERVER_URL", "")
if url:
    body["interfaces"] = [
        {"url": url, "protocolBinding": os.environ.get("PROTOCOL_BINDING", "JSONRPC")}
    ]

print(json.dumps(body))
PY
)"

echo ">> Registering ${SERVICE_ID} (${SPEC_KIND}) in ${PARENT}"
curl -sS -w "\nHTTP %{http_code}\n" -X POST \
  -H "Authorization: Bearer ${TOKEN}" -H "Content-Type: application/json" \
  -d "${BODY}" \
  "${BASE}/${PARENT}/services?serviceId=${SERVICE_ID}"
