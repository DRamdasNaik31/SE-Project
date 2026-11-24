"""Streamlit demonstration interface."""

import streamlit as st

try:
    from .orchestrator import Session, handle
except ImportError:
    from orchestrator import Session, handle

st.set_page_config(page_title="SE-Agentic-Finance", layout="wide")
st.title("SE-Agentic-Finance")
st.caption("Source-grounded requirements engineering and transparent SDLC decision support")

with st.sidebar:
    st.header("Demo settings")
    use_adapter = st.checkbox(
        "Use trained LoRA adapter",
        value=False,
        help="CPU inference can take several minutes per request. Keep this off for fast demonstrations.",
    )

if not use_adapter:
    st.info("Fast grounded mode is active. Enable the trained adapter in the sidebar for the slower LLM path.")

if "session" not in st.session_state:
    st.session_state.session = Session(use_adapter=use_adapter)
else:
    st.session_state.session.use_adapter = use_adapter
if "messages" not in st.session_state:
    st.session_state.messages = []

for role, text in st.session_state.messages:
    with st.chat_message(role):
        st.write(text)

prompt = st.chat_input("Ask about a banking requirement or SDLC model")
if prompt:
    st.session_state.messages.append(("user", prompt))
    result = handle(st.session_state.session, prompt)
    st.session_state.messages.append(("assistant", result["text"]))
    st.rerun()

session = st.session_state.session
if session.requirements:
    st.subheader("Agent 1 — Requirements")
    st.caption(f"Generated all {len(session.requirements)} grounded requirement(s) for the selected module.")
    st.dataframe(session.requirements, use_container_width=True)
    st.info("Requirements remain pending human approval. AI output is advisory.")
if session.sdlc:
    st.subheader("Agent 2 — SDLC scores")
    st.bar_chart({item["model"]: item["score"] for item in session.sdlc["scores"]})
    st.write(session.sdlc["explanation"])
    st.info("SDLC selection remains pending approval by the project manager, architect, security, and compliance roles.")
if session.trace:
    with st.expander("Execution trace"):
        st.json(session.trace)
if session.artifacts:
    with st.expander("Analysis artifacts"):
        st.json(session.artifacts)
