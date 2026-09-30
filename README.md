# Meeting Insights

Turn a meeting transcript into a shared brief: action items, decisions, open questions, a summary, and a view of speaker participation. This Streamlit prototype works with uploaded WebVTT transcripts.

**Python · Streamlit · Gemini**

[Live demo](https://richithareddyy-zoom-meeting-insights-app-gr5imo.streamlit.app) · [Run locally](#run-locally) · [How it works](#how-it-works) · [Limitations](#limitations)

## What it does

- Extracts action items with owners and due dates, along with decisions and open questions.
- Summarizes the discussion and shows speaker participation.
- Redacts email addresses and phone numbers, with optional speaker-name pseudonymization.
- Shows the original and redacted transcript for review.
- Exports insights as JSON.

## Run locally

```sh
git clone https://github.com/richithareddyy/zoom-meeting-insights.git
cd zoom-meeting-insights
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

On Windows, activate the environment with `venv\Scripts\activate`.

Use a [Gemini API key](https://aistudio.google.com/apikey). The sidebar accepts a key when one has not been configured by the host. The hosted demo uses Streamlit secrets. Try the included [`sample_transcript.vtt`](sample_transcript.vtt) before uploading your own transcript.

## How it works

1. Upload a `.vtt` transcript, such as one exported from a Zoom cloud recording with audio transcription.
2. Review the redacted text and choose whether to pseudonymize speaker names.
3. The application sends the processed transcript to Gemini and receives a structured JSON response.
4. Browse the results in the interface and download the JSON report.

Redaction runs in the Python process hosting the app. When running locally, that process is on your computer; on the hosted demo, uploaded transcripts are processed on the server. Redaction is a best-effort step and does not guarantee that every identifying detail is removed.

## Design notes

The project’s design notes describe interviews with five graduate students. Their feedback shaped the emphasis on action items, explicit ownership, and a visible redaction step. A single analysis call keeps the transcript-to-brief workflow straightforward.

- [Architecture](docs/architecture.md)
- [Design decisions](docs/design_decisions.md)
- [Zoom Video SDK integration plan](docs/zoom_video_sdk_integration.md)

## Project structure

| File | Purpose |
| --- | --- |
| `app.py` | Streamlit interface and transcript analysis |
| `zoom_capture.py` | Sketch of a future Zoom SDK capture integration |
| `sample_transcript.vtt` | Sample input for trying the workflow |
| `docs/` | Architecture, design notes, and integration plan |

## Limitations

- Live Zoom capture is not connected to the demo; input is a transcript file.
- Insights remain in the Streamlit session unless downloaded. There is no database or user authentication.
- Summaries and extracted tasks may be incomplete or incorrect; review them against the transcript before sharing.
- Gemini analysis requires an API key and is subject to the account’s quota.
