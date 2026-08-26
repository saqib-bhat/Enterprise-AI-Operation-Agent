import streamlit as st
import httpx
import os

st.set_page_config(page_title="Enterprise AI Operations Agent", layout="wide")

st.title("Enterprise AI Operations Agent")
st.markdown(
    "Ask operational questions about your business data. "
    "The agent will route your query to the appropriate tools (SQL, RAG, Calculator) and provide verified answers."
)

st.sidebar.header("Connection")


api_url = st.sidebar.text_input(
    "API URL",
    value=os.getenv(
        "API_URL",
        "https://entopsaiagent-musf.onrender.com"
    )
)
question = st.text_area(
    "Ask an operational question",
    value="Why did inventory costs increase in July?",
    height=120,
)

if st.button("Submit"):
    if not question.strip():
        st.error("Please enter a question.")
    else:
        with st.spinner("Processing your query..."):
            response_data = None
            error_message = None
            
            try:
                payload = {"query": question}
                res = httpx.post(
                    f"{api_url.rstrip('/')}/chat",
                    json=payload,
                    timeout=60,
                )
                
                if res.status_code == 200:
                    response_data = res.json()
                elif res.status_code == 422:
                    error_message = "Invalid query format. Please enter a valid question."
                elif res.status_code == 500:
                    error_message = "Internal server error. Please try again later."
                else:
                    error_message = f"Unexpected response: {res.status_code}"
                    
            except httpx.ConnectError:
                error_message = "Could not connect to the API. Please check the API URL and ensure the server is running."
            except httpx.TimeoutException:
                error_message = "Request timed out. The server may be busy or unreachable."
            except Exception:
                error_message = "An unexpected error occurred while processing your request."

        # Display results or error
        if error_message:
            st.error(error_message)
        elif response_data:
            # Answer section
            st.subheader("Answer")
            st.write(response_data.get("answer", "No answer returned."))
            
            # Tools used section
            tools_used = response_data.get("tools_used", [])
            if tools_used:
                st.markdown("**Tools Used**")
                st.write(", ".join(tools_used) if tools_used else "None")
            
            # Evidence/sources section
            evidence = response_data.get("evidence", [])
            if evidence:
                st.markdown("**Evidence**")
                for i, doc in enumerate(evidence, 1):
                    source = doc.get("source", "Unknown")
                    page = doc.get("page", "")
                    text = doc.get("text", "")
                    st.markdown(f"**{i}. {source}**" + (f" (page {page})" if page else ""))
                    st.write(text)
            
            # Verification section
            verification = response_data.get("verification", {})
            if verification:
                st.markdown("**Verification**")
                ok = verification.get("ok", False)
                if ok:
                    st.success("✓ Answer verified successfully")
                else:
                    st.warning("⚠ Verification could not confirm the answer")
                attempts = verification.get("attempts", 0)
                if attempts:
                    st.write(f"Verification attempts: {attempts}")
            
            # Errors section
            errors = response_data.get("errors", [])
            if errors:
                st.markdown("**Errors**")
                for error in errors:
                    st.warning(error)
            
            # Latency section
            latency = response_data.get("latency", {})
            if latency:
                st.markdown("**Latency**")
                latency_items = [f"{k}: {v:.3f}s" for k, v in latency.items()]
                st.write(", ".join(latency_items))