---
name: soul-inject
description: "Injects SOUL.md into system prompt to reinforce agent personality"
homepage: https://docs.openclaw.ai/hooks#soul-inject
metadata:
  {
    "openclaw":
      {
        "emoji": "🧠",
        "events": ["agent:bootstrap"],
        "requires": {},
        "install": [{ "id": "bundled", "kind": "bundled", "label": "Bundled with OpenClaw" }],
      },
  }
---

# Soul-Inject Hook

Ensures the agent's personality (defined in SOUL.md) is always reinforced in the system prompt.

## The Problem

OpenClaw's memory system has a limitation:

1. **Bootstrap happens once** - SOUL.md is loaded only when an agent run starts
2. **Context fills up** - As the conversation grows, LLM context windows fill with messages
3. **Personality fades** - The agent may "forget" its core personality traits

## What This Hook Does

This hook ensures SOUL.md is always present and reinforced:

### Current Implementation

On `agent:bootstrap`:
- Reads SOUL.md from the workspace
- Prepends it to bootstrap files
- Ensures it appears at the start of the system prompt

### Full Per-Message Support (Requires Core Modification)

To inject SOUL.md on **every message**, the OpenClaw core would need to:

1. Add a new event type like `agent:turn` or `message:start`
2. Trigger this event before each message is processed
3. Register this hook for that event type

Example core modification in `attempt.ts`:

```typescript
// Before processing each message, trigger a hook
const turnEvent = createHookEvent("agent", "turn", sessionKey, {
  workspaceDir,
  bootstrapFiles: contextFiles,
});
await triggerHook(turnEvent);
contextFiles = turnEvent.context.bootstrapFiles;
```

## Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `injectOnBootstrap` | boolean | `true` | Inject SOUL.md when run starts |

Example:

```json
{
  "hooks": {
    "internal": {
      "entries": {
        "soul-inject": {
          "enabled": true,
          "injectOnBootstrap": true
        }
      }
    }
  }
}
```

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│ Agent Run Starts                                    │
└────────────────┬──────────────────────────────────┘
                 ▼
┌─────────────────────────────────────────────────────────┐
│ agent:bootstrap Event Triggered                       │
└────────────────┬──────────────────────────────────┘
                 ▼
┌─────────────────────────────────────────────────────────┐
│ soul-inject Hook Reads SOUL.md                       │
│ - Loads from workspace/SOUL.md                      │
│ - Prepends to bootstrap files                      │
└────────────────┬──────────────────────────────────┘
                 ▼
┌─────────────────────────────────────────────────────────┐
│ System Prompt Built                                 │
│ [SOUL.md] + [Other bootstrap files] + [History]      │
└─────────────────────────────────────────────────────────┘
```

## Related Files

- `SOUL.md` - Agent personality definition (workspace root)
- `IDENTITY.md` - Agent identity (workspace root)
- `USER.md` - User preferences (workspace root)

## Disabling

To disable this hook:

```bash
openclaw hooks disable soul-inject
```

Or remove from config:

```json
{
  "hooks": {
    "internal": {
      "entries": {
        "soul-inject": { "enabled": false }
      }
    }
  }
}
```
