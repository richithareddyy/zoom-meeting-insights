# Zoom Video SDK integration

This document describes how the prototype's analysis pipeline plugs into
Zoom Video SDK as a capture source, and why v1 demos on file uploads
rather than live streaming.

## Two viable paths

### Path A — Cloud Recording Transcript (recommended for v1.5)

Zoom's cloud recording supports automatic audio transcripts. When a host
enables both "Cloud Recording" and "Audio transcript" in account
settings, Zoom processes the meeting after it ends and produces a `.vtt`
transcript file accessible via the Recording API.

**Flow:**

1. Host runs a Zoom meeting with cloud recording enabled.
2. Meeting ends. Zoom processes the recording (typically 5–15 minutes
   for a one-hour meeting).
3. The app polls `GET /v2/meetings/{meetingId}/recordings`. When the
   response contains a `recording_file` entry with `file_type:
   "TRANSCRIPT"`, the file is downloaded.
4. The downloaded `.vtt` is fed to the same `analyze_transcript()`
   function the file-upload path uses today.

**Why this is the right v1.5 step:** no real-time infrastructure, no
in-meeting bot, and the transcript quality is identical to what the
prototype already handles.

### Path B — Live Video SDK transcription (v2)

Zoom Video SDK exposes a live transcription stream for sessions joined
by an SDK-authenticated client. This enables in-meeting insights and
running summaries.

**Flow:**

1. Server generates a JWT signed with the SDK Key/Secret pair.
2. A headless SDK client joins the session as a non-presenting
   participant (e.g. "Insights Bot").
3. The client subscribes to the live transcript stream and accumulates
   text by speaker.
4. On a sliding window (e.g. every two minutes) or at session end,
   accumulated text is flushed to the analysis pipeline.

**Why this is deferred to v2:** live SDK clients require either native
language bindings or a server-side headless browser environment.
Building that reliably is a real piece of infrastructure work — bigger
than the prototype's scope.

## Auth model

The Zoom Video SDK requires JWTs signed with HS256 against the account's
SDK Key/Secret. The signing happens server-side; the client never sees
the secret. The shape of the payload (see `zoom_capture.generate_sdk_jwt`)
is documented by Zoom and is straightforward — the engineering complexity
is in the streaming client, not the auth.

## Why file uploads for the demo

For the prototype review, file upload is the right capture surface
because:

- It demonstrates the full pipeline (redact → analyze → render) on a
  known input.
- It removes "is the meeting being recorded right now" as a failure
  mode during the demo.
- The integration story is honest: the same code path runs whether the
  transcript came from upload, cloud recording, or live SDK. Swapping
  the capture layer doesn't require rewriting the downstream pipeline.

## What changes when v1.5 lands

Only the source of the VTT string changes. `app.call_gemini`,
`app.redact`, and `app.vtt_to_plain` are untouched. The Streamlit UI
gains a "Connect Zoom" sidebar option that authenticates against the
Recording API and lists recent meetings instead of (or in addition to)
the upload field.
