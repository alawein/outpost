# Token budget

How to spend fewer tokens per unit of work, keep context lean, and cut hallucination. Agent API cost adds up. Most of it is avoidable with habits and settings, not a new tool. Findings first: the five moves that save the most, then the full table, then what this kit already does for you.

Each claim is tagged verified (a primary source confirms it) or proposed (a reasonable practice we have not benchmarked). Sources are at the end.

## The five that matter most

1. Prompt caching. Cached input tokens cost about 90% less to read. Keep the fixed parts stable across turns: system prompt, the doc you work against, or a schema. Pay full price once, and stay in one session because the cache has a 5-minute idle TTL. (verified)
2. Subagent offload. Push long reading into a subagent: logs, many files, or web research. It reads in its own context and returns a short summary, so the parent stays small. Do not over-dispatch, since each subagent carries its own cost. (verified)
3. Model routing. Match the model to the task: Haiku for mechanical work (classification, renames, summaries), Sonnet for analysis, Opus for hard reasoning. The price spread is large (verified against published pricing). That routing routine work down is the biggest saving after caching follows from the spread but is not benchmarked here. (proposed)
4. Clear context per task. Start a fresh session per unit of work, or `/compact` before switching modules. Old context stops riding along. `/context` shows what is loaded. (verified)
5. Ground, do not recall. For anything that must match a source, read and quote it rather than relying on memory. The small extra cost per query prevents the expensive rework from a hallucinated API or field name. (verified)

## The full table

| Practice | Basis | How it saves | How to adopt |
|---|---|---|---|
| Prompt caching | verified | About 90% off cached input reads; 5-minute TTL | Keep fixed context stable across turns; stay in one session |
| Context compaction | verified | `/compact` drops intermediate reasoning, keeps decisions and code | Compact before a new module or after a fix; `/clear` between unrelated tasks |
| Subagent offload | verified | Verbose reads happen in a child context, summary returns | Dispatch research, log scans, and parallel checks; avoid over-dispatch |
| Model routing | price spread verified; routing effect proposed | Large price spread across Haiku, Sonnet, Opus | Route mechanical work to Haiku, reasoning to Opus |
| MCP tool gating | proposed | An issue report puts each idle MCP tool schema near 1K tokens (an issue, not a primary source) | Disable MCP servers you are not using this session |
| Citation grounding | verified | Quoted spans are auditable and cut hallucination rework | Quote the source before processing a long document |
| Persistent memory | verified | Findings stored across sessions instead of re-read each time | Save decisions and schemas to memory; retrieve on demand |
| Terse output | proposed | Fewer output tokens, fewer follow-up turns | Use the `ledger-voice` output style (ships with the plugin) |
| Subset install | proposed | Fewer skills in context means less schema overhead | Install with `--only plan-change,write-tests` rather than the full pack |

## What this kit already does for you

- Skills load by description in Claude rather than by pasting prompt text into the chat. The agent
  pulls only what it needs; the full text stays on disk. (verified)
- `--only` and `--exclude` let you install a focused subset, and the installer records the choice
  so `--verify` tracks it (verified). Fewer installed skills should mean less context overhead per
  session, the same subset-install claim as the table. (proposed)
- The `nudge_context` hook prints a one-line reminder when a Read pulls a very large file with no `offset` or `limit`. It reinforces targeted reads and subagent offload. It is advisory and never blocks. (verified)
- The `ledger-voice` plugin output style keeps responses terse: findings first, claims tagged, no slop. It is a plugin output style, separate from the installer's `--terse` settings merge. (proposed until benchmarked)

## Anti-hallucination, specifically

Drift and wrong output cost tokens too, since they cause rework. The cheap controls:

- Read the file or run the command rather than guess. Already a convention in this kit.
- For a claim that must hold up, quote the source. Tag it verified, proposed, or unknown when the
  basis matters.
- Verify a field or contract name against the consuming system before coding to it; a name written
  from memory is a common, expensive miss.
- Use a verification step before calling work done. Here that is `python validate.py`.

## Sources

- Anthropic, Prompt caching: https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- Anthropic Cookbook, Automatic context compaction: https://platform.claude.com/cookbook/tool-use-automatic-context-compaction
- Claude Code, Subagents: https://code.claude.com/docs/en/sub-agents
- Anthropic, Pricing: https://platform.claude.com/docs/en/about-claude/pricing
- MCP tool-schema token overhead, issue 2808: https://github.com/modelcontextprotocol/modelcontextprotocol/issues/2808
- Anthropic, Reduce hallucinations: https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations
- Anthropic, Memory tool: https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool
