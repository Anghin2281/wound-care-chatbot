import streamlit as st
import openai
import tempfile
import base64
from fpdf import FPDF

openai.api_key = st.secrets.get("OPENAI_API_KEY")
client = openai.OpenAI()

st.set_page_config(page_title="Wound Care Chatbot", layout="wide")
st.markdown("<h1 style='color:#800000'>🩺 Wound Care Chatbot — Text Q&A</h1>", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Chat-based Q&A functionality
user_input = st.chat_input("Ask a wound care or documentation question...")
if user_input:
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.spinner("WoundBot is thinking..."):
        full_prompt = [
            {
                "role": "system",
                "content": (
                    "You are a wound care expert trained in:\n"
                    "- Pressure injury staging (NPIAP)\n"
                    "- CMS LCDs for CTP qualification\n"
                    "- Infection control, moisture balance, tunneling, undermining, slough, granulation\n"
                    "- ICD-10 and CPT code usage for wound care\n"
                    "- Dressing selection and application by wound type\n"
                    "- Graft recommendations (single, double, triple layer)\n"
                    "- Appropriate pharmaceuticals and topicals to treat infections\n"
                    "Answer all questions in a clinical, evidence-based manner."
                )
            }
        ] + st.session_state["messages"]
        response = client.chat.completions.create(model="gpt-4o", messages=full_prompt)
        reply = response.choices[0].message.content
        st.session_state["messages"].append({"role": "assistant", "content": reply})

# Display chat history
for msg in st.session_state["messages"]:
    if msg["role"] == "user":
        st.markdown(f"**You:** {msg['content']}")
    else:
        st.markdown(f"**WoundBot:** {msg['content']}")

# Export result to PDF
if st.button("📄 Export Chat to PDF"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    pdf.cell(200, 10, txt="Wound Care Chat Transcript", ln=True, align="C")
    pdf.ln(10)
    for msg in st.session_state["messages"]:
        speaker = "You" if msg["role"] == "user" else "WoundBot"
        lines = msg["content"].splitlines()
        for line in lines:
            pdf.multi_cell(0, 8, f"{speaker}: {line}")
        pdf.ln(2)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        with open(tmp.name, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
            st.markdown(f'<a href="data:application/octet-stream;base64,{b64}" download="WoundCareChat.pdf">Download Chat PDF</a>', unsafe_allow_html=True)

# Reset session
if st.button("🔁 Reset All"):
    st.session_state.clear()
    st.experimental_rerun()
