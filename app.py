import json
import os
import re
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from google import genai
from google.genai import types

load_dotenv()

st.set_page_config(
    page_title="Meeting Insights",
    layout="wide",
)

st.title("Meeting Insights")
st.write(
    "Turn a Zoom meeting transcript into a shared post-session brief: "
    "summary, action items, decisions, and participant breakdown."
)

def _get_default_key() -> str:
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass
    return os.getenv("GEMINI_API_KEY", "")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Setup")
    api_key = st.text_input(
        "Gemini API key",
        value=_get_default_key(),
        type="password",
        help="Get one free at aistudio.google.com/apikey",
    )
    model_name = st.selectbox(
        "Model",
        [
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
            "gemini-2.0-flash-lite",
            "gemini-2.0-flash",
            "gemini-2.5-pro",
        ],
        index=0,
        help="If you hit a 404 or quota error, try a different one. Lite/flash variants have the best free tier.",
    )
    if st.button("List models my key can use", use_container_width=True):
        if not api_key:
            st.warning("Add your API key first.")
        else:
            try:
                client = genai.Client(api_key=api_key)
                names = []
                for m in client.models.list():
                    actions = getattr(m, "supported_actions", None) or getattr(m, "supported_generation_methods", []) or []
                    if not actions or "generateContent" in actions:
                        names.append(m.name.replace("models/", ""))
                st.success(f"{len(names)} model(s) available:")
                st.code("\n".join(names) or "(none)", language="text")
            except Exception as e:
                st.error(f"Could not list models: {e}")
    st.divider()
    st.subheader("Privacy")
    redact_emails = st.checkbox("Redact emails before API call", value=True)
    redact_phones = st.checkbox("Redact phone numbers", value=True)
    redact_names = st.checkbox(
        "Pseudonymize speaker names", value=False,
        help="Replaces names with 'Speaker 1', 'Speaker 2', etc.",
    )
    st.divider()
    st.caption(
        "Redaction runs in the browser process before the transcript is sent to Gemini."
    )

# ── Helpers ────────────────────────────────────────────────────────────────────
def load_sample_transcript() -> str:
    sample_path = Path(__file__).parent / "sample_transcript.vtt"
    if sample_path.exists():
        return sample_path.read_text()
    return ""

def vtt_to_plain(text: str) -> str:
    """Strip VTT timestamps/headers; keep speaker: line format."""
    if "WEBVTT" not in text and "-->" not in text:
        return text.strip()
    lines, out, buf = text.splitlines(), [], []
    for line in lines:
        s = line.strip()
        if not s or s == "WEBVTT" or "-->" in s or re.match(r"^\d+$", s):
            if buf:
                out.append(" ".join(buf))
                buf = []
            continue
        buf.append(s)
    if buf:
        out.append(" ".join(buf))
    return "\n".join(out)

def redact(text: str, emails: bool, phones: bool, names: bool) -> tuple[str, dict]:
    """Local PII redaction. Returns (redacted_text, stats)."""
    stats = {"emails": 0, "phones": 0, "names": 0}
    if emails:
        text, n = re.subn(r"[\w\.-]+@[\w\.-]+\.\w+", "[EMAIL]", text)
        stats["emails"] = n
    if phones:
        text, n = re.subn(
            r"(\+?\d{1,2}[\s\-\.]?)?\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4}",
            "[PHONE]", text,
        )
        stats["phones"] = n
    if names:
        speakers = set(re.findall(r"^([A-Z][a-zA-Z]+):", text, flags=re.MULTILINE))
        mapping = {name: f"Speaker {i+1}" for i, name in enumerate(sorted(speakers))}
        for original, pseudo in mapping.items():
            text = re.sub(rf"\b{re.escape(original)}\b", pseudo, text)
        stats["names"] = len(mapping)
    return text, stats

ANALYSIS_PROMPT_TEMPLATE = """You are an expert meeting analyst. Analyze the meeting transcript below
and return a SINGLE valid JSON object with EXACTLY these keys:

- "summary": string — 2-3 sentence executive summary
- "key_topics": array of short topic strings
- "action_items": array of objects, each with keys "task" (string), "owner" (string, person name or "unassigned"), "due" (string, date or "unspecified")
- "decisions": array of strings — things the group resolved
- "open_questions": array of strings — questions left unanswered
- "participants": array of objects, each with keys "name" (string), "speaking_share_pct" (number 0-100), "key_contributions" (1-sentence string)
- "sentiment": one of "positive", "neutral", "mixed", "tense"
- "followup_suggestions": array of strings — suggested next steps

Rules:
- Be concise. Only include action items that are clearly committed to in the meeting.
- speaking_share_pct values should sum to roughly 100.
- Return ONLY the JSON object. No prose, no markdown fences.

TRANSCRIPT:
---
__TRANSCRIPT__
---
"""

def build_prompt(transcript: str) -> str:
    return ANALYSIS_PROMPT_TEMPLATE.replace("__TRANSCRIPT__", transcript)

def call_gemini(transcript: str, key: str, model: str) -> dict:
    client = genai.Client(api_key=key)
    resp = client.models.generate_content(
        model=model,
        contents=build_prompt(transcript),
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )
    raw = (resp.text or "").strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    raise ValueError(
        "Could not parse Gemini response as JSON. "
        f"First 800 chars of response:\n\n{raw[:800]}"
    )

# ── Main flow ──────────────────────────────────────────────────────────────────
def _load_sample_into_box():
    st.session_state["transcript_box"] = load_sample_transcript()

def _load_upload_into_box():
    f = st.session_state.get("uploader")
    if f is not None:
        st.session_state["transcript_box"] = f.read().decode("utf-8", errors="ignore")

st.subheader("Transcript")
col_a, col_b = st.columns([1, 1])
with col_a:
    st.file_uploader(
        "Upload .vtt or .txt",
        type=["vtt", "txt"],
        label_visibility="collapsed",
        key="uploader",
        on_change=_load_upload_into_box,
    )
with col_b:
    st.button(
        "Use sample transcript",
        use_container_width=True,
        on_click=_load_sample_into_box,
    )

raw = st.text_area("Or paste transcript here:", height=200, key="transcript_box")

if raw.strip():
    plain = vtt_to_plain(raw)
    redacted, stats = redact(plain, redact_emails, redact_phones, redact_names)

    with st.expander("Privacy preprocessing (runs locally before API call)", expanded=False):
        st.info(
            f"Local redaction stripped {stats['emails']} email(s), "
            f"{stats['phones']} phone number(s), and pseudonymized "
            f"{stats['names']} name(s) before sending to Gemini."
        )
        c1, c2 = st.columns(2)
        c1.markdown("**Original (local only)**")
        c1.code(plain[:1200] + ("\n..." if len(plain) > 1200 else ""), language="text")
        c2.markdown("**Sent to Gemini**")
        c2.code(redacted[:1200] + ("\n..." if len(redacted) > 1200 else ""), language="text")

    st.subheader("Analysis")
    if st.button("Analyze meeting", type="primary", use_container_width=True):
        if not api_key:
            st.error("Add your Gemini API key in the sidebar first.")
        else:
            with st.spinner("Asking Gemini to analyze the meeting..."):
                try:
                    result = call_gemini(redacted, api_key, model_name)
                    st.session_state["result"] = result
                except Exception as e:
                    st.error(f"Gemini call failed: {e}")

# ── Results ────────────────────────────────────────────────────────────────────
result = st.session_state.get("result")
if result:
    st.divider()
    st.subheader("Insights")

    summary = result.get("summary", "")
    if summary:
        st.markdown("**Summary**")
        st.write(summary)

    topics = result.get("key_topics", [])
    if topics:
        st.markdown("**Topics:** " + " · ".join(f"`{t}`" for t in topics))

    tabs = st.tabs(["Action items", "Decisions", "Open questions", "Participants", "Follow-ups"])

    with tabs[0]:
        items = result.get("action_items", [])
        if items:
            st.dataframe(pd.DataFrame(items), use_container_width=True, hide_index=True)
        else:
            st.info("No committed action items detected.")

    with tabs[1]:
        for d in result.get("decisions", []) or ["(none recorded)"]:
            st.markdown(f"- {d}")

    with tabs[2]:
        for q in result.get("open_questions", []) or ["(none)"]:
            st.markdown(f"- {q}")

    with tabs[3]:
        parts = result.get("participants", [])
        if parts:
            df = pd.DataFrame(parts)
            left, right = st.columns([1, 1])
            with left:
                st.dataframe(df, use_container_width=True, hide_index=True)
            with right:
                if "speaking_share_pct" in df.columns and "name" in df.columns:
                    st.bar_chart(df.set_index("name")["speaking_share_pct"])

    with tabs[4]:
        sentiment = result.get("sentiment", "neutral")
        st.markdown(f"**Overall sentiment:** `{sentiment}`")
        for s in result.get("followup_suggestions", []) or ["(none)"]:
            st.markdown(f"- {s}")

    with st.expander("Raw JSON (for debugging / export)"):
        st.json(result)
        st.download_button(
            "Download insights as JSON",
            data=json.dumps(result, indent=2),
            file_name="meeting_insights.json",
            mime="application/json",
        )

else:
    st.info("Load a transcript above to get started. Click **Use sample transcript** for a quick demo.")
