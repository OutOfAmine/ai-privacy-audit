# ai-privacy-audit

Claude Code skill that audits a codebase for personal-data risks around AI:

- personal data (PII) sent to LLM APIs (OpenAI, Anthropic, Mistral, Gemini, Bedrock, Ollama…)
- prompt injection, weighted by what the model can actually do (tools, SQL, HTML rendering)
- RAG / vector search without per-user or per-tenant access control
- prompts and responses written to logs, observability tools or long-lived storage
- AI API keys hardcoded, committed or exposed to the browser

It traces each prompt back to where its data comes from, reports verified `file:line` findings with severity, scenario and fix, never copies secret values and never modifies code. Reports are written in the user's language.

**Live demo:** https://outofamine.github.io/ai-privacy-audit/

## Install

```bash
git clone https://github.com/OutOfAmine/ai-privacy-audit
cp -r ai-privacy-audit/skills/ai-privacy-audit ~/.claude/skills/
```

Then in Claude Code: *"audit my project for personal data leaking to AI"*, or `/ai-privacy-audit`.

## Example

[`examples/fixture-app`](examples/fixture-app) is a small app with 8 deliberate flaws. [`examples/fixture-app-report.md`](examples/fixture-app-report.md) is the unedited report the skill produced on it: 8/8 found, the safe file not flagged, no secret reproduced.

The key in the fixture is a placeholder, not a real key.

## License

MIT
