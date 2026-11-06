# Meeting Insights

A meeting ends, and you need to know what was decided and who agreed to do what without rereading the whole transcript. Meeting Insights takes an uploaded or pasted transcript and turns it into a brief with action items, decisions, open questions, and a summary. It’s a Streamlit prototype for reviewing transcripts after a meeting, not a live Zoom recorder.

Built with Python, Streamlit, and Gemini.

I interviewed five graduate students before building it. All five wanted to know who had agreed to do what, and several were uncomfortable leaving raw transcripts in shared channels. That shaped the workflow: load a transcript, review the version with identifying details removed, request a brief, and export it as JSON.

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

The app removes email addresses and phone numbers before sending text to Gemini. You can also replace speaker names with labels and compare the processed text with the original. This happens in Python—on the server for the hosted demo—and can miss identifying details.

Results stay in the session unless downloaded. The app reads the model’s JSON response but does not strictly validate every field. Participation estimates use transcript text, not measured speaking time.

## Checking it

No automated tests are committed. Use the sample transcript to inspect parsing, redaction, task ownership, and JSON export. Review generated claims against the source before sharing them. The app has no database or user authentication; live Zoom capture remains an integration sketch.

[Architecture](docs/architecture.md) · [Design decisions](docs/design_decisions.md) · [Full guide](GUIDE.md)
