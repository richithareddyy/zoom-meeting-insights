# Architecture

Written for a non-developer reader. The goal is to explain how the prototype
is put together, what each piece is responsible for, and why the boundaries
are drawn where they are.

## What this prototype does, in one sentence

A user provides a Zoom meeting transcript. The app strips identifying
information on the user's own machine, asks Google Gemini to extract a
structured set of insights from the remaining text, and displays those
insights as a shared post-meeting brief.

## Three layers

```
┌─────────────────────────────────────────────────────────────┐
│  Capture layer                                              │
│  - Today: file upload / paste (.vtt or .txt)                │
│  - v2:    Zoom Video SDK cloud recording or live transcript │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Local preprocessing (browser process, never sent anywhere) │
│  - Strip VTT timestamps and cue numbers                     │
│  - Redact emails and phone numbers (regex)                  │
│  - Optionally replace speaker names with "Speaker 1/2/3..." │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Gemini call (single structured JSON response)              │
│  - One request, not a chain of prompts                      │
│  - response_mime_type = application/json forces structure   │
│  - Robust parser: extracts first {...} block if needed      │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Display layer (Streamlit)                                  │
│  - Summary, key topics                                      │
│  - Tabs: action items, decisions, open questions,           │
│    participants (with speaking-share chart), follow-ups     │
│  - Raw JSON download for export to other tools              │
└─────────────────────────────────────────────────────────────┘
```

## Why these boundaries

**Capture is decoupled from analysis.** The same `analyze_transcript()`
function runs whether the transcript came from a Zoom cloud recording, a
live SDK stream, or a pasted text file. Adding Zoom Video SDK in v2 is a
swap at the top of the pipeline, not a rewrite.

**Redaction is local.** Personally identifying information is removed before
the transcript leaves the user's machine. The model never sees it. This is
the privacy guarantee a meeting host can credibly make to participants.

**One Gemini call, not many.** Multi-step LLM pipelines compound failure
modes — each call is another chance for a parse error, a timeout, or
inconsistent state. A single structured-output call is cheaper, faster, and
easier to reason about.

## File map

| File | Role |
|------|------|
| `app.py` | Streamlit UI, redaction, Gemini call, results display |
| `zoom_capture.py` | Zoom Video SDK integration sketch (cloud recording + live) |
| `sample_transcript.vtt` | Reference transcript used for demos |
| `docs/design_decisions.md` | Why this is built the way it is, including the user-interview findings |
| `docs/zoom_video_sdk_integration.md` | How the SDK integration lands in v2 |

## What's intentionally *not* here

- A database. v1 is single-session. Transcripts and insights live in the
  Streamlit session and are downloaded as JSON if the user wants them
  persisted.
- An auth layer. The deployed app accepts the user's own Gemini API key in
  the sidebar. There is no shared backend key — each user pays for their
  own (free-tier) usage.
- A queue or background worker. Analysis takes a few seconds; the user
  waits on a spinner. A queue would be over-engineered for v1.
