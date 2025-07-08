
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
                        "- Identifying undermining, tunneling, exudate, eschar, slough, granulation
"
                        "- Interpreting NPIAP pressure staging
"
                        "- Describing wound bed and periwound status
"
                        "ONLY respond with visual features and wound description. DO NOT suggest treatment."
                    )
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe this wound based on its visual characteristics only."},
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

# Text-based chatbot
user_input = st.chat_input("Ask a wound care or documentation question...")
if user_input:
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.spinner("WoundBot is thinking..."):
        full_prompt = [
            {
                "role": "system",
                "content": (
                    "You are a wound care expert trained in:
"
                    "- Identifying and managing wound infections
"
                    "- Selecting appropriate dressings for each wound type and stage
"
                    "- ICD-10 and CPT coding for wound types, treatments, and CTP application
"
                    "- Recommending CTPs by graft layer (1–4 ply) based on wound presentation
"
                    "- Choosing topicals and pharmaceuticals for bacterial, fungal, and mixed infections
"
                    "- CMS LCD compliance, healing rate benchmarks, SMART care planning
"
                    "Answer questions with clear explanations and clinical reasoning. Use medical terminology."
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

# Export to PDF
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
