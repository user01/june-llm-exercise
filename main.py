import streamlit as st
from agno.models.openai import OpenAIChat
from agno.models.ollama import Ollama

from exercise_tooling.config import CLI
from exercise_tooling.team import generate_team  # parses flags before Streamlit boots


def main():
    if CLI.provider == "openai":
        model = OpenAIChat(id=CLI.model)
    elif CLI.provider == "ollama":
        model = Ollama(id=CLI.model)
    else:
        raise ValueError("Invalid provider")

    team = generate_team(model, CLI.database_path)

    # ---------- page & state ----------
    st.set_page_config(
        page_title="Medical Agent Exercise", page_icon="💊", layout="wide"
    )

    # Chat history: seed with a greeting the very first time
    if "history" not in st.session_state:
        st.session_state.history = [
            (
                "assistant",
                "👋 Hi! I'm your medical-data assistant.\n\n"
                "Ask me anything about the CMS Information on Part D formulary and pharmacy networks for \n"
                "Medicare Prescription Drug Plans and Medicare Advantage Plans.",
            )
        ]

    # ---------- header ----------
    st.header("💊 CMS Analytics Chat")
    st.caption(
        "Explore the Centers for Medicare & Medicaid Services data. "
        "Type a question or prompt below to begin."
    )

    # ---------- sidebar ----------
    with st.sidebar:
        st.title("💊 CMS Analytics")
        st.write(f"Model: **{CLI.model}**")

    # ---------- chat transcript ----------
    for role, msg in st.session_state.history:
        st.chat_message(role).write(msg)

    # ---------- user input ----------
    prompt = st.chat_input("Ask about the data…")
    if prompt:
        st.chat_message("user").write(prompt)
        st.session_state.history.append(("user", prompt))

        # ---------- assistant response ----------
        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                out = team.run(prompt)

            st.markdown(out.content)
            st.session_state.history.append(("assistant", out.content))


if __name__ == "__main__":
    main()
