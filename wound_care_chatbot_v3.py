import streamlit as st
import openai
import tempfile
import base64
from io import BytesIO
from fpdf import FPDF
from PIL import Image
from pillow_heif import register_heif_opener

register_heif_opener()

openai.api_key = st.secrets.get("OPENAI_API_KEY")
client = openai.OpenAI()


st.markdown("### 🔴 Upload Documentation Notes")
doc_files = st.file_uploader("Upload wound documentation (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"], accept_multiple_files=True)

# Red button: Audit uploaded documentation notes (placeholder logic)
if doc_files and st.button("🔴 Start Documentation Audit"):
    st.success("📑 Documentation audit triggered.")
    st.session_state["messages"].append({
        "role": "assistant",
        "content": "📋 Placeholder: CMS-compliant audit logic will run here. Each document will be checked against LCDs and flagged for compliance."
    })


st.set_page_config(page_title="Wound Care Chatbot", layout="wide")
st.markdown("<h1 style='color:#800000'>🩺 Wound Care Chatbot — Vision + Chat + Reset</h1>", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state["messages"] = []

st.markdown("### 🟡 Upload Wound Image (HEIC, JPG, PNG, etc.)")
img_file = st.file_uploader("Upload a wound photo", type=["jpg", "jpeg", "png", "bmp", "tif", "tiff", "heic", "webp"])

image_bytes = None
if img_file:
    try:
        image = Image.open(BytesIO(img_file.read())).convert("RGB")
        buffer = BytesIO()
        image.save(buffer, format="JPEG")
        image_bytes = buffer.getvalue()
        st.image(image, caption="Uploaded wound image (converted to JPEG)", use_container_width=True)
    except Exception as e:
        st.error("❌ Invalid image format or corrupted file.")
        st.stop()

if image_bytes and st.button("🟡 Analyze Wound Image"):
    with st.spinner("Analyzing wound image..."):
        try:
            b64_img = base64.b64encode(image_bytes).decode()
            vision_prompt = [
                {
                    "role": "system",
                    "content": (
                        "You are a wound care expert trained in:
"
                        "- Pressure injury staging (NPIAP)
"
                        "- CMS LCDs for CTP qualification
"
                        "- Infection control, moisture balance, tunneling, undermining, slough, granulation
"
                        "- Dressing selection and SMART goals
"
                        "You will analyze wound images and respond with:
"
                        "1. Wound type & stage
"
                        "2. Key visual features
"
                        "3. Recommended treatment plan
"
                        "4. Measurable SMART healing goal"
                    )
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analyze this wound and recommend treatment with a SMART goal."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}
                    ]
                }
            ]
            response = client.chat.completions.create(model="gpt-4o", messages=vision_prompt)
            result = response.choices[0].message.content
            st.session_state["messages"].append({"role": "assistant", "content": result})
            st.markdown(f"**WoundBot:** {result}")
        except Exception as e:
            st.error("❌ GPT-4o failed to analyze the image.")
            st.exception(e)

# Text-based Q&A chatbot
user_input = st.chat_input("Ask a wound care or documentation question...")
if user_input:
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.spinner("WoundBot is thinking..."):
        full_prompt = [{"role": "system", "content": "You are a wound care expert answering clinical, billing, and CMS-related questions."}] + st.session_state["messages"]
        response = client.chat.completions.create(model="gpt-4o", messages=full_prompt)
        reply = response.choices[0].message.content
        st.session_state["messages"].append({"role": "assistant", "content": reply})

# Display chat history
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

# Reset everything
if st.button("🔁 Reset All"):
    st.session_state.clear()
    st.experimental_rerun()
