# Meeting Insights

A meeting ends, and you need to know what was decided and who agreed to do what without rereading the whole transcript. Meeting Insights takes an uploaded or pasted transcript and turns it into a brief with action items, decisions, open questions, and a summary. It’s a Streamlit prototype for reviewing transcripts after a meeting, not a live Zoom recorder.

Built with Python, Streamlit, and Gemini.

Before scoping it, I interviewed five graduate students. None wanted the transcript after a meeting; all five wanted a list of who agreed to do what, and several were uneasy about raw transcripts sitting in shared channels. So the workflow is deliberately small: load a transcript, review the redacted version, make one structured model request, and export the result as JSON.

## Run locally

From the repository root:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

On Windows, use `venv\Scripts\activate`. Supply a Gemini API key in the sidebar if the host has not configured one. Start with [`sample_transcript.vtt`](sample_transcript.vtt), or upload a WebVTT/text file or paste a transcript.

[Live demo](https://richithareddyy-zoom-meeting-insights-app-gr5imo.streamlit.app)

## What happens to the transcript

Email addresses and phone numbers are redacted before the Gemini request, with optional speaker-name pseudonymization. You can compare the original and processed text first. Redaction runs in the Python hosting process—on the server when using the hosted demo—and does not guarantee removal of every identifying detail.

Results remain in the session unless downloaded. The app parses the response as JSON but does not enforce a strict output schema. Speaker participation is estimated from text, not measured from audio timing.

## Checking it

No automated tests are committed. Use the sample transcript to inspect parsing, redaction, task ownership, and JSON export. Review generated claims against the source before sharing them. The app has no database or user authentication; live Zoom capture remains an integration sketch.

[Architecture](docs/architecture.md) · [Design decisions](docs/design_decisions.md) · [Full guide](GUIDE.md)
