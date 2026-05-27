import streamlit as st

from agent_core import (
    llm_with_tools,
    tools,
    system_prompt
)

from langchain_core.messages import (
    HumanMessage,
    ToolMessage,
    AIMessage
)

st.set_page_config(page_title="City Intelligence Agent")

st.title("🌍 City Intelligence Agent")

# =========================
# SESSION STATE
# =========================

if "messages" not in st.session_state:
    st.session_state.messages = [system_prompt]

# =========================
# DISPLAY CHAT HISTORY
# =========================

for msg in st.session_state.messages:

    if isinstance(msg, HumanMessage):
        st.chat_message("user").write(msg.content)

    elif isinstance(msg, AIMessage):

        # avoid blank assistant messages
        if msg.content:
            st.chat_message("assistant").write(msg.content)

# =========================
# USER INPUT
# =========================

user_input = st.chat_input(
    "Ask about weather or city news..."
)

if user_input:

    # show user input
    st.chat_message("user").write(user_input)

    # store user input
    st.session_state.messages.append(
        HumanMessage(content=user_input)
    )

    # =========================
    # FIRST LLM CALL
    # =========================

    result = llm_with_tools.invoke(
        st.session_state.messages
    )

    st.session_state.messages.append(result)

    # =========================
    # TOOL EXECUTION
    # =========================

    if result.tool_calls:

        tool_outputs = []

        for tool_call in result.tool_calls:

            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            # execute tool
            tool_result = tools[tool_name].invoke(
                tool_args
            )

            tool_outputs.append(tool_result)

            # send tool result back
            st.session_state.messages.append(
                ToolMessage(
                    content=tool_result,
                    tool_call_id=tool_call["id"]
                )
            )

        # =========================
        # FINAL LLM RESPONSE
        # =========================

        final_result = llm_with_tools.invoke(
            st.session_state.messages
        )

        response_text = final_result.content

        # fallback if model returns empty
        if not response_text:
            response_text = "\n\n".join(tool_outputs)

        st.chat_message("assistant").write(
            response_text
        )

        st.session_state.messages.append(
            AIMessage(content=response_text)
        )

    else:

        st.chat_message("assistant").write(
            result.content
        )

        st.session_state.messages.append(
            AIMessage(content=result.content)
        )