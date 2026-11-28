"""Streamlit demonstration interface."""

import streamlit as st

try:
    from .orchestrator import Session, handle
except ImportError:
    from orchestrator import Session, handle

st.set_page_config(page_title="SE-Agentic-Finance", layout="wide")
st.title("SE-Agentic-Finance")
st.caption("Agent 1 generates source-grounded requirements. Agent 2 recommends an SDLC model when you ask.")

with st.sidebar:
    st.header("Optional settings")
    use_adapter = st.checkbox(
        "Use trained LoRA adapter",
        value=False,
        help="CPU inference can take several minutes per request. Keep this off for fast demonstrations.",
    )
    with st.expander("SDLC project factors"):
        stability = st.selectbox("Requirement stability", ["Unknown", "Stable", "Changing"])
        stakeholder_feedback = st.selectbox("Stakeholder feedback", ["Unknown", "High", "Low"])
        delivery_pressure = st.selectbox("Delivery pressure", ["Unknown", "High", "Low"])

if not use_adapter:
    st.info("Fast grounded mode is active. Enable the trained adapter in the sidebar for the slower LLM path.")

if "session" not in st.session_state:
    st.session_state.session = Session(use_adapter=use_adapter)
else:
    st.session_state.session.use_adapter = use_adapter
st.session_state.session.constraints = {
    "stability": stability.lower(),
    "stakeholder_feedback": stakeholder_feedback.lower(),
    "delivery_pressure": delivery_pressure.lower(),
}
if "messages" not in st.session_state:
    st.session_state.messages = []

for role, text in st.session_state.messages:
    with st.chat_message(role):
        st.write(text)

prompt = st.chat_input("Ask for finance requirements, or reply with a sub-branch such as loan")
if prompt:
    st.session_state.messages.append(("user", prompt))
    result = handle(st.session_state.session, prompt)
    st.session_state.messages.append(("assistant", result["text"]))
    st.rerun()

session = st.session_state.session
if session.requirements:
    st.subheader(f"Agent 1 — Generated requirements ({len(session.requirements)})")
    for module, requirements in session.requirements_by_module.items():
        st.markdown(f"### {module} ({len(requirements)} requirements)")
        st.dataframe(requirements, use_container_width=True)
        st.caption("Draft, source-grounded output. Review requirements before using them in a project.")
if session.sdlc:
    st.subheader("Agent 2 — SDLC recommendation")
    st.metric("Recommended model", session.sdlc["winner"])
    st.write(session.sdlc["explanation"])
    st.bar_chart({item["model"]: item["score"] for item in session.sdlc["scores"]})
    st.caption("This is a decision-support recommendation; the project team makes the final selection.")
if session.trace:
    with st.expander("Execution trace"):
        st.json(session.trace)
if session.artifacts:
    with st.expander("Analysis artifacts"):
        st.json(session.artifacts)
