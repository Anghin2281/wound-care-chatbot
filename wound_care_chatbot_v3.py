
import streamlit as st
import openai
import tempfile
import base64
from fpdf import FPDF

openai.api_key = st.secrets.get("OPENAI_API_KEY")
client = openai.OpenAI()

st.set_page_config(page_title="Wound Care Chatbot", layout="wide")
st.markdown("<h1 style='color:#800000'>🩺 Wound Care Chatbot — Clinical & CMS Expert</h1>", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Text-based Q&A chatbot
user_input = st.chat_input("Ask a wound care, infection, ICD-10/CPT, dressing, or CMS documentation question...")
if user_input:
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.spinner("WoundBot is thinking..."):
        full_prompt = [
            {"role": "system", "content": (
                "You are a wound care expert trained in:
"
                "- All major CMS LCDs for CTP and wound billing (L35125, L35041, A56696, L37228, etc.)
"
                "- ICD-10 codes for chronic wounds, infections, and pressure injuries
"
                "- CPT codes for debridement, grafts, and wound procedures
"
                "- Infection management (topicals, antibiotics, wound cultures)
"
                "- Dressing selection by wound type (slough, undermining, tunneling, drainage)
"
                "- SMART goal creation for wound healing
"
                "- Graft layer selection based on wound depth, drainage, and tissue status
"
                "- Documenting conservative care, plan of care, and clinical justification
"
            )}
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

# Export chat to PDF
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

# Reset all
if st.button("🔁 Reset All"):
    st.session_state.clear()
    st.experimental_rerun()
