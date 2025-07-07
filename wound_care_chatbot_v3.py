import streamlit as st
import openai
import tempfile
import base64
from fpdf import FPDF
from io import BytesIO
from PIL import Image
from pillow_heif import register_heif_opener

register_heif_opener()

openai.api_key = st.secrets.get("OPENAI_API_KEY")
client = openai.OpenAI()

st.set_page_config(page_title="Wound Care Image Analyzer", layout="wide")
st.markdown("<h1 style='color:#800000'>🩺 Wound Care Chatbot — Image Analyzer + SMART Plan</h1>", unsafe_allow_html=True)

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
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": (
    "You are a wound care expert trained in:\n"
    "- Pressure injury staging (NPIAP)\n"
    "- CMS LCDs for CTP qualification\n"
    "- Infection control, moisture balance, tunneling, undermining, slough, granulation\n"
    "- Dressing selection and SMART goals\n"
    "You will analyze wound images and respond with:\n"
    "1. Wound type & stage\n"
    "2. Key visual features\n"
    "3. Recommended treatment plan\n"
    "4. Measurable SMART healing goal"
)

)\n
"
                            "- CMS LCDs for CTP qualification\n
"
                            "- Infection control, moisture balance, tunneling, undermining, slough, granulation\n
"
                            "- Dressing selection and SMART goals\n
"
                            "You will analyze wound images and respond with:
"
                            "1. Wound type & stage\n
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
            )
            result = response.choices[0].message.content
            st.session_state["messages"].append({"role": "assistant", "content": result})
            st.markdown(f"**WoundBot:** {result}")
        except Exception as e:
            st.error("❌ GPT-4o failed to analyze the image.")
            st.exception(e)

# Export result to PDF
if st.button("📄 Export Result to PDF"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    pdf.cell(200, 10, txt="Wound Image Analysis Report", ln=True, align="C")
    pdf.ln(10)
    for msg in st.session_state["messages"]:
        lines = msg["content"].splitlines()
        for line in lines:
            pdf.multi_cell(0, 8, line)
        pdf.ln(2)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
        pdf.output(tmpfile.name)
        with open(tmpfile.name, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
            st.markdown(f'<a href="data:application/octet-stream;base64,{b64}" download="Wound_Image_Analysis.pdf">Download PDF</a>', unsafe_allow_html=True)

# Reset interface
if st.button("🔁 Reset All"):
    st.session_state.clear()
    st.experimental_rerun()
