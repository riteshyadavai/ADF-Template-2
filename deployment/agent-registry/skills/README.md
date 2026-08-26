# Skills

Skills are a **separate resource** in Agent Registry (`Skill` / `SkillRevision`,
governed by a `Publisher`) and are registered through the skills API, not the
`services.create` call that `register.sh` uses for MCP servers, agents, and
endpoints.

See [Register skills](https://docs.cloud.google.com/agent-registry/register-skills).
`example/skill.json` is a placeholder for that payload.
