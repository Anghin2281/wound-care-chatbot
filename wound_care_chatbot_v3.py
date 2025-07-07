import streamlit as st
import openai
import tempfile
import base64
from fpdf import FPDF
from io import BytesIO
from PIL import Image

client = openai.OpenAI()

st.set_page_config(page_title="Wound Care Chatbot (Fixed Upload)", layout="wide")
st.markdown("<h1 style='color:#800000'>🩺 Wound Care AI Chatbot — Fixed Upload & Image Analysis Ready</h1>", unsafe_allow_html=True)

st.markdown("Ask any question about wounds, CMS compliance, dressing, grafts, or upload notes/photos for feedback.")

if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Upload areas
st.markdown("### 🔴 Upload Wound Care Documentation Notes")
doc_files = st.file_uploader("Choose note files (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"], accept_multiple_files=True)

st.markdown("### 🟡 Upload Wound Image (All Types Accepted)")
img_file = st.file_uploader("Upload image of wound", type=["jpg", "jpeg", "png", "bmp", "tif", "tiff", "heic", "webp"])

# Safely handle image
if img_file:
    st.markdown("🟡 **Wound Image Uploaded**")
    image_bytes = img_file.read()
    try:
        image = Image.open(BytesIO(image_bytes))
        st.image(image, caption="Uploaded wound image", use_column_width=True)
    except Exception as e:
        st.error("❌ Invalid image format. Please upload a valid wound image.")
        st.stop()

# System prompt
system_prompt = {
    "role": "system",
    "content": """
You are a wound care expert trained on:
- CMS LCDs (L35125, L35041, A56696, L37228, L37166, L33831)
- Article A58565
- Pressure injury staging: 1–4, unstageable, DTI
- TIMERS framework
- CTP eligibility rules (≥30–50% healing over 4 weeks)
- Wound dressing and debridement protocols
- SMART goals, positioning, infection control, moisture balance
- ICD-10/CPT billing logic

Capabilities:
- Calculate healing benchmarks and graft eligibility
- Recommend dressings and treatment per stage/severity
- Explain documentation standards
- Analyze wound images to suggest clinical treatment with measurable SMART goals
"""
}

# Chat input
user_input = st.chat_input("Ask your clinical or billing question...")

if user_input:
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.spinner("Analyzing..."):
        full_prompt = [system_prompt] + st.session_state["messages"]
        response = client.chat.completions.create(model="gpt-4o", messages=full_prompt)
        reply = response.choices[0].message.content
        st.session_state["messages"].append({"role": "assistant", "content": reply})

# Chat display
for msg in st.session_state["messages"]:
    if msg["role"] == "user":
        st.markdown(f"**You:** {msg['content']}")
    else:
        st.markdown(f"**WoundBot:** {msg['content']}")

# PDF export
if st.button("📄 Export Chat to PDF"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    pdf.cell(200, 10, txt="Wound Care Chatbot Transcript", ln=True, align="C")
    pdf.ln(10)
    for msg in st.session_state["messages"]:
        prefix = "You: " if msg["role"] == "user" else "WoundBot: "
        lines = (prefix + msg["content"]).splitlines()
        for line in lines:
            pdf.multi_cell(0, 8, line)
        pdf.ln(2)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        with open(tmp.name, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
            st.markdown(f'<a href="data:application/octet-stream;base64,{b64}" download="WoundCareChatbotTranscript.pdf">Download Chat PDF</a>', unsafe_allow_html=True)
