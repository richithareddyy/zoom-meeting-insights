# Meeting Insights

Turns a Zoom meeting transcript into a shared post-session brief: summary,
action items, decisions, open questions, and a participant breakdown.

Built as a prototype to explore where AI can be genuinely useful for
meeting follow-up, where the privacy trade-offs sit, and how the same
analysis pipeline plugs into Zoom Video SDK as a capture source.

## What it does

- Accepts a Zoom `.vtt` transcript (uploaded or pasted)
- Redacts emails, phone numbers, and optionally speaker names — locally,
  before any API call
- Sends the redacted transcript to Google Gemini in a single structured
  JSON call
- Surfaces the results in a Streamlit dashboard:
  - Executive summary and key topics
  - Action items with owner and due date
  - Decisions and open questions
  - Participant speaking share (with chart)
  - Suggested follow-ups
- Lets users download insights as JSON

## Stack

- Python 3.9+, Streamlit
- Google Gemini via the `google-genai` SDK (structured JSON output)
- Local regex redaction (no PII leaves the user's machine without their
  having seen the redacted version first)

## Run locally

```bash
git clone <this-repo-url>
cd zoom-insights
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

The app opens at `http://localhost:8501`. Paste your Gemini API key into
the sidebar (free at <https://aistudio.google.com/apikey>) and click
**Use sample transcript** → **Analyze meeting**.

## Documentation

- [docs/architecture.md](docs/architecture.md) — system layout, the three
  pipeline layers, and why the boundaries are drawn where they are
- [docs/design_decisions.md](docs/design_decisions.md) — user-research
  findings from five grad-student interviews and how they shaped the
  feature set
- [docs/zoom_video_sdk_integration.md](docs/zoom_video_sdk_integration.md)
  — how the Zoom Video SDK plugs in as a capture source, and why v1
  demos on file uploads

## Repo layout

```
app.py                            Streamlit app
zoom_capture.py                   Zoom Video SDK integration sketch
sample_transcript.vtt             Demo input
requirements.txt                  Python dependencies
docs/
  architecture.md
  design_decisions.md
  zoom_video_sdk_integration.md
```

## Privacy

Redaction happens in the same Python process that renders the page,
before the transcript is handed to the Gemini SDK. The *Privacy
preprocessing* expander shows both the original transcript (local only)
and the redacted version (sent to the API) side by side, so the user
can verify what left their machine.

## Status

v1 prototype. v1.5 (Zoom cloud-recording transcripts) and v2 (live SDK
transcription) are documented in
[docs/zoom_video_sdk_integration.md](docs/zoom_video_sdk_integration.md)
but not yet implemented.
