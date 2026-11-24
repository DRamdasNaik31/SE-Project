"""Streamlit demonstration interface."""

import streamlit as st

try:
    from .orchestrator import Session, handle
    from .governance import GovernanceLog, require_approval
except ImportError:
    from orchestrator import Session, handle
    from governance import GovernanceLog, require_approval

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
    st.subheader("SDLC project factors")
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
    edited_requirements = st.data_editor(
        session.requirements,
        use_container_width=True,
        num_rows="dynamic",
        key="requirement_editor",
    )

    actor = st.text_input("Human reviewer/actor")
    review_columns = st.columns(4)
    if review_columns[0].button("Accept baseline"):
        if not actor.strip():
            st.error("Enter the authorised reviewer name before approval.")
        else:
            try:
                require_approval("requirement_baseline", actor.strip())
                for requirement in session.requirements:
                    requirement["approval_status"] = "accepted"
                GovernanceLog().record("requirement_baseline_accepted", actor.strip(), {
                    "requirement_count": len(session.requirements),
                    "module": session.last_module,
                })
                st.success("Requirement baseline accepted and recorded.")
            except PermissionError as exc:
                st.error(str(exc))
    if review_columns[1].button("Reject"):
        if actor.strip():
            for requirement in session.requirements:
                requirement["approval_status"] = "rejected"
            GovernanceLog().record("requirement_baseline_rejected", actor.strip(), {
                "requirement_count": len(session.requirements),
                "module": session.last_module,
            })
            st.warning("Requirements rejected and recorded.")
        else:
            st.error("Enter the authorised reviewer name before recording rejection.")
    if review_columns[2].button("Save modifications"):
        session.requirements = edited_requirements
        if actor.strip():
            for requirement in session.requirements:
                requirement["approval_status"] = "modified_pending_review"
            GovernanceLog().record("requirement_baseline_modified", actor.strip(), {
                "requirement_count": len(session.requirements),
                "module": session.last_module,
            })
        st.info("Modified requirements are pending human review.")
    if review_columns[3].button("Regenerate"):
        if session.last_request:
            result = handle(session, session.last_request)
            st.session_state.messages.append(("assistant", result["text"]))
            st.rerun()
    st.info("Requirements remain pending human approval. AI output is advisory.")
if session.sdlc:
    st.subheader("Agent 2 — SDLC scores")
    st.bar_chart({item["model"]: item["score"] for item in session.sdlc["scores"]})
    st.write(session.sdlc["explanation"])
    sdlc_actor = st.text_input("SDLC approving authority", key="sdlc_actor")
    sdlc_columns = st.columns(2)
    if sdlc_columns[0].button("Approve SDLC recommendation"):
        if not sdlc_actor.strip():
            st.error("Enter the authorised approving authority.")
        else:
            try:
                require_approval("sdlc_selection", sdlc_actor.strip())
                session.sdlc["approval_status"] = "approved"
                GovernanceLog().record("sdlc_selection_approved", sdlc_actor.strip(), {
                    "winner": session.sdlc["winner"],
                    "scores": session.sdlc["scores"],
                })
                st.success("SDLC recommendation approved and recorded.")
            except PermissionError as exc:
                st.error(str(exc))
    if sdlc_columns[1].button("Reject SDLC recommendation"):
        if sdlc_actor.strip():
            session.sdlc["approval_status"] = "rejected"
            GovernanceLog().record("sdlc_selection_rejected", sdlc_actor.strip(), {
                "winner": session.sdlc["winner"],
            })
            st.warning("SDLC recommendation rejected and recorded.")
        else:
            st.error("Enter the authorised approving authority.")
    st.info("SDLC selection remains pending approval by the project manager, architect, security, and compliance roles.")
if session.trace:
    with st.expander("Execution trace"):
        st.json(session.trace)
if session.artifacts:
    with st.expander("Analysis artifacts"):
        st.json(session.artifacts)
