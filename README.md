# Meeting Insights

A small prototype I built to play with the post-meeting problem: everyone walks
out of a Zoom call with a slightly different memory of what got decided. This
takes a transcript and turns it into one shared brief — a summary, the action
items with owners, the decisions, the open questions, and a quick view of who
spoke how much.

**Live demo:** https://richithareddyy-zoom-meeting-insights-app-gr5imo.streamlit.app

## Running it locally

```bash
git clone https://github.com/richithareddyy/zoom-meeting-insights
cd zoom-meeting-insights
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

You'll need a Gemini API key. Free one at https://aistudio.google.com/apikey,
takes about a minute. Paste it into the sidebar. There's a sample transcript
in the repo so you can try it without recording anything.

## How it actually works

Three steps:

1. You upload a `.vtt` transcript. Zoom produces these when you turn on cloud
   recording with audio transcription enabled.
2. The app strips emails, phone numbers, and optionally speaker names. This
   happens locally, in the same Python process that's rendering the page,
   before anything is sent to Gemini. There's an expander in the UI that
   shows both the original transcript and the redacted version side by side,
   so you can verify what actually leaves your machine.
3. One Gemini call returns the whole insight payload as structured JSON. The
   UI breaks that JSON into tabs.

I tried to keep the LLM part small on purpose. Multi-step prompt chains are
fragile, every hop is another chance to fail, and they cost more for not much
benefit on a task that's basically "read this and tell me what happened."

## Why these particular choices

I interviewed five grad students before scoping this. What surprised me:
none of them wanted the transcript. They wanted a shorter "who agreed to do
what" artifact, and a few wanted the raw transcript to stay on their laptop.
That's why action items are the first tab, each one has an owner and a due
date, and the redaction step has its own UI panel where you can check what's
being sent before you send it.

The other thing that came up: name sensitivity is uneven. One person wanted
credit for everything she committed to. Another preferred to be anonymized in
anything that might get shared. So pseudonymization is a per-user toggle
instead of a default.

More on this in [docs/design_decisions.md](docs/design_decisions.md).

## The Zoom Video SDK part

Live capture from the Video SDK is sketched in `zoom_capture.py` but isn't
wired into the demo. I ran out of runway to build the streaming client
reliably enough to demo on, so the prototype runs on file upload instead.
The downstream pipeline (redact, analyze, render) doesn't care where the
transcript came from, so adding cloud-recording fetch or live capture later
is a swap at the top of the file, not a rewrite.

The integration plan and the auth model are in
[docs/zoom_video_sdk_integration.md](docs/zoom_video_sdk_integration.md).

## What's in this repo

- `app.py` — the Streamlit app
- `zoom_capture.py` — Zoom SDK integration sketch
- `sample_transcript.vtt` — the demo transcript
- `docs/architecture.md` — how the pieces fit together
- `docs/design_decisions.md` — what the user interviews changed
- `docs/zoom_video_sdk_integration.md` — what v1.5 and v2 look like

## Things I haven't done

There's no database — insights live in the Streamlit session and you can
download them as JSON. There's no auth either; the public demo uses my
Gemini key (configured via Streamlit secrets), and the local version takes
yours. If this ever grew into something real, both of those need work..
