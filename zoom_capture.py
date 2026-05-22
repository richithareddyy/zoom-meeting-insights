"""
Zoom Video SDK transcript capture — integration sketch.

The deployed Streamlit prototype currently ingests transcripts via file upload
or paste, because that path is reliable to demo and isolates the LLM pipeline
from Zoom auth / streaming concerns.

This module documents the integration shape for live capture so the same
downstream pipeline (redact → analyze → render) plugs in unchanged.

Two integration points exist for a Zoom Video SDK app:

1. Cloud Recording Transcript (recommended for v1)
   - Enable cloud recording with "Audio transcript" turned on.
   - After the meeting, Zoom emails a .vtt file and exposes it via the
     Recording API: GET /v2/meetings/{meetingId}/recordings.
   - Download the transcript file, hand it to `analyze_transcript()` below.
   - Pros: no real-time infrastructure; full transcript is well-formatted VTT.
   - Cons: post-meeting only (not live during the call).

2. Live SDK transcription (v2)
   - Initialize the Zoom Video SDK with a JWT signed by your SDK Key/Secret.
   - Join the session and subscribe to the live transcription stream.
   - Buffer text chunks per speaker, then flush to `analyze_transcript()` on
     end-of-meeting OR on a sliding window.

Both paths converge on the same function signature so the UI doesn't need to
know which one fed it.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class ZoomConfig:
    sdk_key: str
    sdk_secret: str
    session_name: str
    user_identity: str = "insights-bot"
    role: int = 0

    @classmethod
    def from_env(cls, session_name: str) -> "ZoomConfig":
        return cls(
            sdk_key=os.environ["ZOOM_SDK_KEY"],
            sdk_secret=os.environ["ZOOM_SDK_SECRET"],
            session_name=session_name,
        )


def generate_sdk_jwt(cfg: ZoomConfig, ttl_seconds: int = 7200) -> str:
    """Build a Zoom Video SDK JWT.

    Zoom requires HS256 JWT with a specific payload for Video SDK sessions:
        { app_key, version, role_type, tpc, iat, exp, ... }

    Kept as a thin wrapper so credentials never leave the server process.
    Implementation deferred to v2 — current prototype demos on cloud-recording
    transcripts.
    """
    raise NotImplementedError(
        "Live SDK auth is wired to ZoomConfig but not implemented in v1. "
        "v1 ingests transcripts via cloud recording or file upload."
    )


def fetch_cloud_recording_transcript(meeting_id: str, access_token: str) -> Optional[str]:
    """Pull the VTT transcript from Zoom Cloud Recording API.

    Returns raw VTT string, or None if the recording has no transcript yet
    (transcripts are produced asynchronously and may take several minutes
    after meeting end).
    """
    raise NotImplementedError(
        "v1 demos via file upload. Cloud recording fetch is documented in "
        "docs/zoom_video_sdk_integration.md and will land in v2."
    )


# Downstream pipeline entrypoint — same shape regardless of capture path.
def analyze_transcript(vtt_text: str, gemini_api_key: str, model: str) -> dict:
    """Convergence point: any capture path feeds into this function.

    The Streamlit app calls this directly via `app.call_gemini` after local
    redaction. Exposing it here makes the SDK integration story explicit:
    Zoom is the *source*; analysis is *source-agnostic*.
    """
    from app import call_gemini, redact, vtt_to_plain  # local import avoids Streamlit at import time

    plain = vtt_to_plain(vtt_text)
    redacted, _stats = redact(plain, emails=True, phones=True, names=False)
    return call_gemini(redacted, gemini_api_key, model)
