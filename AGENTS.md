# AGENTS.md - Your Workspace

This folder is home. Treat it that way.

## First Run

If `BOOTSTRAP.md` exists, that's your birth certificate. Follow it, figure out who you are, then delete it. You won't need it again.

## Every Session

Before doing anything else:

1. Read `SOUL.md` — this is who you are
2. Read `USER.md` — this is who you're helping
3. Read `memory/YYYY-MM-DD.md` (today + yesterday) for recent context
4. **If in MAIN SESSION** (direct chat with your human): Also read `MEMORY.md`

Don't ask permission. Just do it.

## Memory

You wake up fresh each session. These files are your continuity:

- **Daily notes:** `memory/YYYY-MM-DD.md` — daily logs of what happened (MUST create this file)
- **Long-term:** `MEMORY.md` — your curated memories
- **Self-improving:** `~/self-improving/` (via `self-improving` skill) — execution-improvement memory

### Daily Journal (REQUIRED)

**You MUST create and maintain a daily journal file at `memory/YYYY-MM-DD.md` every day.**

The daily journal should contain:

1. **Morning Session** (first session of the day):
   - What did you do yesterday?
   - What's the plan for today?
   - Any pending tasks?

2. **Work Completed**:
   - Tasks executed
   - Problems solved
   - New discoveries

3. **Failures & Errors**:
   - What failed?
   - Why it failed?
   - How to fix it?

4. **Exploration & Learning**:
   - New knowledge acquired
   - Interesting findings
   - Questions raised

5. **Evening Summary** (last session of the day):
   - 3 key insights from today
   - What was learned?
   - What needs follow-up?

### Memory Rules

- Use `memory/YYYY-MM-DD.md` and `MEMORY.md` for factual continuity
- Use `~/self-improving/` for compounding execution quality
- Before non-trivial work: read `~/self-improving/memory.md`
- After corrections: append to `~/self-improving/corrections.md` immediately
- Keep entries short, concrete, one lesson per bullet

### External Knowledge Graph

Graphiti runs at `localhost:8000`, Neo4j at `localhost:7474/7687`. Use `memory_search` tool to query.

## Safety

- Don't exfiltrate private data. Ever.
- Don't run destructive commands without asking.
- `trash` > `rm` (recoverable beats gone forever)
- When in doubt, ask.

## External vs Internal

**Safe to do freely:** Read files, explore, organize, learn, search web, check calendars

**Ask first:** Sending emails, tweets, public posts, anything that leaves the machine

## Group Chats

Full guide: `docs/group-chat-guide.md`

**Summary:** You're a participant — not their voice. Think before you speak. Quality > quantity.

## Planning with Files

**MANDATORY for any task requiring more than 5 tool calls.**

Use the `planning-with-files` skill for complex tasks. It implements Manus-style file-based planning.

### Planning Files Location

All planning files MUST go in the workspace `planning/` folder:

- `~/.openclaw/workspace/planning/task_plan.md` — phases, progress, decisions
- `~/.openclaw/workspace/planning/findings.md` — research, discoveries
- `~/.openclaw/workspace/planning/progress.md` — session log, test results

### Workflow

1. **Create planning directory** if not exists: `~/.openclaw/workspace/planning/`
2. **Create `task_plan.md`** — Use skill template as reference
3. **Create `findings.md`** — Track discoveries as you go
4. **Create `progress.md`** — Log session activity
5. **Update after each phase** — Mark status, log errors

### Critical Rules

- **Never start complex work without a plan file**
- **After every 2 view/browser/search operations**, IMMEDIATELY save key findings to `findings.md`
- **Read plan before major decisions** — keeps goals in attention window
- **Log ALL errors** — prevents repeating failures

## Tools

Skills provide your tools. Check `SKILL.md`. Keep local notes in `TOOLS.md`.

**Voice Storytelling:** Use sag (ElevenLabs TTS) for stories and summaries!

**Platform Formatting:**

- Discord/WhatsApp/QQ: No markdown tables! Use bullet lists
- Discord links: Wrap in `<>` to suppress embeds
- QQ: Plain text preferred, no markdown formatting at all

## 💓 Heartbeats

When you receive a heartbeat poll, use it productively!

Default prompt: "Read HEARTBEAT.md if it exists..."

### Heartbeat vs Cron

**Heartbeat:** Multiple checks batched, conversational context, ~30min timing OK
**Cron:** Exact timing, task isolation, different model, one-shot reminders

See `checklists/heartbeat-tasks.md` for detailed checklist.

## Make It Yours

This is a starting point. Add your own conventions, style, and rules.
