# Sophion

A personal knowledge engine that compiles research into a structured wiki and challenges you to actually understand it. Plugs into any MCP-capable agent — [Claude Code](https://claude.com/claude-code), [Hermes Agent](https://github.com/NousResearch/hermes-agent), Codex, Cursor — or runs standalone as a CLI/TUI.

Inspired by [Andrej Karpathy's LLM Knowledge Bases](https://x.com/karpathy/status/1911070200111272246) concept, with an added learning layer: a challenger agent that surfaces gaps in your understanding, tests your knowledge through Socratic questioning, and tracks what you've verified vs. what you've just accepted.

## How It Works

```
Raw sources (papers, articles, URLs)
    → Ingest into raw/
    → LLM compiles into wiki/ (structured markdown with backlinks)
    → Query, study, and explore via your agent or the CLI
    → Explorations get filed back into the wiki (compounding loop)
```

The knowledge base is Obsidian-compatible — open `~/.sophion/knowledge/` as a vault to browse articles and follow wikilinks.

## Quick Start

### Installation

```bash
git clone https://github.com/alperiox/sophion.git
cd sophion
uv sync
```

### Standalone CLI Usage

```bash
# Initialize the knowledge base
sophion init

# Ingest a web article
sophion ingest "https://lilianweng.github.io/posts/2021-07-11-diffusion-models/"

# Ingest a local file
sophion ingest path/to/notes.md

# Compile raw documents into wiki articles
sophion compile

# Ask questions against your knowledge base
sophion query "What is the forward process in diffusion models?"

# Launch the interactive TUI
sophion tui
```

### Agent Integration (Recommended)

Sophion ships a standard MCP server over stdio, so it works with any MCP-capable
agent. Running it inside an agent is what unlocks the conversational interface and
the self-improving learning loop.

There are **two** pieces to wire up, and they're independent:

1. **The MCP server** (`sophion-mcp`) — exposes the [17 tools](#mcp-tools-reference).
   Configured the same way everywhere.
2. **The study skill** (`skills/sophion-study/`) — teaches the agent the challenger
   behaviour behind `/sophion-study`. Skill loading is *not* part of MCP, so this
   step differs per harness.

Replace `/path/to/sophion` below with the actual path to your clone.

#### Claude Code

```bash
# 1. Register the MCP server
claude mcp add sophion -- uv --directory /path/to/sophion run sophion-mcp

# 2. Install the study skill
ln -s /path/to/sophion/skills/sophion-study ~/.claude/skills/sophion-study
```

#### Hermes Agent

Install Hermes, then add both pieces to `~/.hermes/config.yaml` (see
`hermes-config.example.yaml`):

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

```yaml
mcp_servers:
  sophion:
    command: "uv"
    args: ["--directory", "/path/to/sophion", "run", "sophion-mcp"]

skills:
  external_dirs:
    - /path/to/sophion/skills
```

Hermes additionally gives you multi-platform access (Telegram, Discord, etc.).

#### Any other MCP client

Most clients accept the standard `mcpServers` JSON block (see
`mcp-config.example.json`):

```json
{
  "mcpServers": {
    "sophion": {
      "command": "uv",
      "args": ["--directory", "/path/to/sophion", "run", "sophion-mcp"]
    }
  }
}
```

If your harness has no skill mechanism, paste the contents of
`skills/sophion-study/SKILL.md` into your system prompt instead — it's plain
markdown instructions, nothing harness-specific.

#### A note on the LLM backend

The MCP tools are harness-agnostic, but the *compilation* step is not: `compile`,
`query`, and the `compile_knowledge` tool shell out to the Claude Code CLI
(`claude -p`). You need the `claude` binary on your PATH for those, whichever
harness hosts the MCP server. Reading, searching, linting, gap tracking, and
study mode have no such dependency.

#### Using it

Once the server is registered, Sophion's 17 tools are available. Just talk naturally:

```
You: ingest this article https://arxiv.org/abs/2006.11239
You: compile my knowledge base
You: what do I know about diffusion models?
You: /sophion-study
```

## Study Mode

Study mode activates the **challenger agent** — it stops being a helpful assistant and starts testing your understanding.

```
You: /sophion-study

Agent: Study mode activated. 2 open gaps to revisit:
       - [a3f2b1c0] (diffusion) Why does noise prediction = ELBO?
       Want to revisit, or start a new topic?

You: let's study the forward process

Agent: Before I show you the article — what do you think
       q(x_t | x_0) looks like?

You: something with alpha bar... a Gaussian?

Agent: Good instinct. Can you write the exact expression?

You: q(x_t | x_0) = N(x_t; sqrt(alpha_bar_t) * x_0, (1 - alpha_bar_t) * I)

Agent: Correct: q(xₜ | x₀) = 𝒩(xₜ; √ᾱₜ · x₀, (1−ᾱₜ)I).
       Now — why does √ᾱₜ appear as the coefficient? What would
       happen if it were just ᾱₜ without the square root?

... the challenger keeps pushing until you truly understand ...

You: I'm done studying

Agent: Study session ended.
       Gaps surfaced (1):
         - (diffusion) Reverse process posterior derivation
       Gaps resolved (1):
         - (diffusion) Why does noise prediction = ELBO?
```

### What the Challenger Does

- **Gap surfacing**: When you accept a claim without questioning, it challenges you to explain *why* it's true
- **Socratic questioning**: Asks what you think the answer is *before* showing you
- **Spaced reinforcement**: Periodically revisits previously discussed topics
- **Gap tracking**: Maintains a persistent record of what you've verified vs. accepted
- **Session summaries**: Shows what you learned (and what's still open) when you stop

## Multiple Knowledge Bases

Create separate bases for different research topics:

```
You: create a knowledge base called diffusion
You: switch to diffusion
You: ingest https://arxiv.org/abs/2006.11239

You: create a knowledge base called attention
You: switch to attention
You: ingest https://arxiv.org/abs/1706.03762

You: list my knowledge bases
```

Each base has its own wiki, gap tracker, and conversation history.

## MCP Tools Reference

Sophion exposes 17 tools via the Model Context Protocol:

| Tool | Description |
|------|-------------|
| `list_articles` | List all wiki articles with titles |
| `read_article` | Read an article (LaTeX auto-rendered to Unicode) |
| `search_articles` | Full-text search across the wiki |
| `ingest_url` | Fetch and ingest a web page |
| `ingest_file` | Ingest a local markdown file |
| `compile_knowledge` | Compile raw documents into wiki articles |
| `update_article` | Create or update a wiki article |
| `lint_knowledge` | Health checks (broken links, thin articles, orphans) |
| `render_math` | Convert LaTeX to Unicode |
| `list_gaps` | List open learning gaps |
| `add_gap` | Record a new learning gap |
| `resolve_gap` | Mark a gap as understood |
| `toggle_study_mode` | Activate/deactivate the challenger agent |
| `study_status` | Check if study mode is active |
| `list_bases` | List available knowledge bases |
| `create_base` | Create a new knowledge base |
| `switch_base` | Switch to a different knowledge base |

## LaTeX Rendering

LaTeX in wiki articles is automatically converted to Unicode when read through the MCP tools:

- `$\alpha + \beta$` → `α + β`
- `$\mathcal{N}(0, I)$` → `𝒩(0, I)`
- `$\sqrt{\bar{\alpha}_t}$` → `√ᾱₜ`
- `$\nabla_x \log p(x)$` → `∇ₓ log p(x)`

## Storage Layout

```
~/.sophion/
├── knowledge/
│   ├── raw/              # Ingested source material
│   ├── wiki/             # LLM-compiled articles with backlinks
│   └── gaps/             # (reserved)
├── conversations/        # Chat history (JSON)
├── learner_state/        # Gap tracker + study session state
├── config.toml           # Configuration
└── bases/                # Named knowledge bases
    ├── diffusion/        # Each base has the same structure
    ├── attention/
    └── ...
```

The wiki is Obsidian-compatible — open `~/.sophion/knowledge/` (or any base directory) as an Obsidian vault.

## Development

```bash
git clone https://github.com/alperiox/sophion.git
cd sophion
uv sync
uv run pytest -v        # 150 tests
uv run sophion --help    # CLI commands
```

## License

MIT
