# Design decisions

This document records the decisions that shaped the prototype, what drove
each one, and which were informed by user research vs. engineering
constraints.

## User research findings

Five graduate students were interviewed before the prototype was scoped.
The interview prompt focused on the gap between "what happened in this
meeting" and "what each person walked away thinking happened." Three
findings shaped the feature set:

1. **Participants wanted commitments, not transcripts.**
   When asked what they'd want delivered after a meeting, none of the
   five said "the transcript." All five wanted a list of who agreed to
   do what. This is why `action_items` is the primary tab and each item
   carries an explicit `owner` and `due` field.

2. **People were uncomfortable with raw transcripts in shared channels.**
   Several mentioned that sharing a full transcript in a group thread felt
   like exposing offhand comments that weren't meant for a permanent
   record. This pushed the design toward an *insights-only* output, with
   the original transcript staying on the user's machine.

3. **Names felt sensitive in different ways for different people.**
   One participant strongly preferred their name appearing on commitments
   ("if I said I'd do it, I want it credited"). Another preferred to be
   anonymized in any artifact that might be shared externally. This is
   why pseudonymization is a per-user *toggle*, not a default.

## Engineering decisions

### Redaction runs locally, before the API call

Emails and phone numbers are stripped with regex in the same Python
process that renders the UI. The redacted text is what gets sent to
Gemini. The user can verify this in the *Privacy preprocessing* expander,
which shows the original and the sent-to-API versions side by side.

The trade-off: regex is imperfect. A cleverly formatted phone number or a
non-standard email might slip through. We accept this for a prototype on
the basis that (a) the failure mode is visible (the user can see what was
caught and what wasn't), and (b) the alternative — sending raw text and
asking the model to redact — moves PII through a network boundary that
the user can't easily inspect.

### One structured Gemini call

The prompt asks for a single JSON object with a specific schema and uses
`response_mime_type="application/json"`. This avoids multi-step pipelines
where one step's failure cascades. If the JSON parser fails, a fallback
regex extracts the first `{...}` block; if both fail, the raw response is
surfaced to the user for debugging instead of silently breaking.

### Pseudonymization is opt-in

When enabled, names are replaced with `Speaker 1`, `Speaker 2`, etc.,
*before* the model sees the transcript. The model's output references
those pseudonyms. The user can choose to keep real names visible
internally and toggle pseudonymization on only when exporting.

### No backend key

The deployed Streamlit Cloud app does not ship with a shared Gemini API
key. Each user provides their own, stored only in their session. This
keeps the deployment cost at zero and removes a category of abuse where
one user's behavior could exhaust a shared quota.

## Decisions deferred to v2

- **Live SDK transcription.** Real-time capture from a Zoom Video SDK
  session is sketched in `zoom_capture.py` but not implemented. v1 demos
  on file uploads and cloud-recording transcripts.
- **Multi-meeting history.** No database; insights are downloaded as JSON
  per session. A future version would add a simple per-user store.
- **Cross-meeting trends.** Once history exists, useful follow-up
  features include "topics that repeat across meetings" and "commitments
  that didn't get done."
