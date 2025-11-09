# Search Agent — Workflow

This repository implements a small state-graph driven agent that routes user requests to three main flows: database lookup, mail composition/send, and (optionally) Wikipedia-style knowledge lookup. The diagram below (workflow.png) shows the runtime nodes, key state fields, and tool integrations used by the agent.

![Workflow diagram](workflow.png)

Figure: workflow.png — high-level explanation

- classify: Accepts the user's message and sets `state["message_type"]` to one of `database`, `mail`, or `wikipedia`.
- router1: Normalizes `message_type` and ensures a canonical value is present in the state. The graph uses this to select the primary branch.
- database (google_sheets_node): Extracts column/value from the user message, calls the `read_records` tool (reads the canonical Google Sheet), filters rows with `fetch_selected_records`, and returns `final_answer` and `selected_google_sheet_responses`.
- mail flow: mail_extract -> mail_lookup -> mail_draft -> router2 -> (wikipedia_info | no_wikipedia_info) -> mail_send

  - mail_extract: extracts recipient (email or name) and message intent from the user's message.
  - mail_lookup: if recipient email is missing, uses `read_records` + `fetch_selected_records` to find the email address from the sheet.
  - mail_draft: uses the LLM to draft an email in the strict format `subject:` / `body:` and stores `draft_subject` and `draft_body`.
  - router2: decides whether additional Wikipedia-style info is needed (sets `state["need_wikipedia"]` true/false). This is a boolean-based branch mapped to `wikipedia_info` or `no_wikipedia_info`.
  - wikipedia_info / no_wikipedia_info: either fetches/summarizes external knowledge or no-ops, then continues to `mail_send`.
  - mail_send: calls `send_email` to actually send the drafted message (reads SMTP creds from environment variables). This step is only executed when the user explicitly requests sending.

- wikipedia node: when selected, extracts a topic from the user message, calls an external `retrieve` tool to collect resource pages, asks the LLM to summarize, and returns `final_answer`.

Tools and safety notes

- `read_records` — reads the canonical Google Sheet `Contact Details` worksheet and returns a list of row dictionaries. The tool takes no inputs and MUST be treated as the single source of truth for contact data.
- `fetch_selected_records(records, name, column)` — exact, case-insensitive match filter for the sheet records. Returns an empty list when no matches are found (do not fabricate results).
- `send_email(to, subject, body)` — sends email via Gmail SMTP using `EMAIL_ADDRESS` and `EMAIL_APP_PASSWORD` environment variables. Only use when the user explicitly asks to send an email.
- `retrieve(query)` — external retriever used by the wikipedia node to collect pages/resources for summarization.

Design guarantees to reduce hallucination

- Tools include precise descriptions and strict input/output shapes. The agent only answers from `selected_google_sheet_responses` or LLM text outputs that are explicitly formatted (e.g., the mail draft format).
- Conditional routing is driven by canonical state fields (`message_type`, `need_wikipedia`) to avoid mismatches between router returns and the graph's expected keys.
- Tool outputs are never invented by the agent; fetch functions return empty lists when nothing matches.

How to update the diagram

Place an updated `workflow.png` in the repository root (same folder as this README). The README references `workflow.png` by relative path.

If you'd like a different caption or more detail for any node, tell me which node(s) and I'll update the README accordingly.
