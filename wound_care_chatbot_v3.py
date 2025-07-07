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

st.set_page_config(page_title="Wound Care Chatbot (Image Format Fixed)", layout="wide")
st.markdown("<h1 style='color:#800000'>🩺 Wound Care Chatbot — Supported Image Format Fix</h1>", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state["messages"] = []

st.markdown("### 🔴 Upload Documentation Notes")
doc_files = st.file_uploader("Upload wound notes (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"], accept_multiple_files=True)

st.markdown("### 🟡 Upload Wound Image (JPG, PNG, HEIC, etc.)")
img_file = st.file_uploader("Upload a wound photo", type=["jpg", "jpeg", "png", "bmp", "tif", "tiff", "heic", "webp"])

image_bytes = None
image_mime = "image/jpeg"  # default fallback MIME type

if img_file:
    try:
        image = Image.open(BytesIO(img_file.read()))
        converted = BytesIO()
        image = image.convert("RGB")
        image.save(converted, format="JPEG")
        converted.seek(0)
        image_bytes = converted.read()
        st.image(image, caption="Uploaded wound image (converted to JPEG)", use_column_width=True)
    except Exception as e:
        st.error("❌ Invalid image format or corrupted image file.")
        st.stop()

if image_bytes and st.button("🟡 Analyze Wound Image"):
    with st.spinner("Analyzing wound image with GPT-4o..."):
        b64_img = base64.b64encode(image_bytes).decode()
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a wound care expert trained in pressure injuries, wound staging, dressings, CTP rules, and infection protocols. Analyze the wound image and give a treatment plan + SMART goal."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Please analyze this wound and suggest a treatment plan."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}
                        ]
                    }
                ]
            )
            result = response.choices[0].message.content
            st.session_state["messages"].append({"role": "assistant", "content": result})
            st.markdown(f"**WoundBot:** {result}")
        except Exception as e:
            st.error("❌ GPT-4o image analysis failed.")
            st.exception(e)

if doc_files and st.button("🔴 Start Documentation Audit"):
    st.success("📑 Documentation audit triggered (logic placeholder).")

user_input = st.chat_input("Ask your wound care or billing question...")
if user_input:
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.spinner("WoundBot is reviewing your question..."):
        full_prompt = [{"role": "system", "content": "You are a wound care expert using all mastered LCDs, dressing standards, graft benchmarks, pressure injury stages, and documentation rules."}] + st.session_state["messages"]
        response = client.chat.completions.create(model="gpt-4o", messages=full_prompt)
        reply = response.choices[0].message.content
        st.session_state["messages"].append({"role": "assistant", "content": reply})

for msg in st.session_state["messages"]:
    if msg["role"] == "user":
        st.markdown(f"**You:** {msg['content']}")
    else:
        st.markdown(f"**WoundBot:** {msg['content']}")

if st.button("📄 Export Chat to PDF"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    pdf.cell(200, 10, txt="Wound Care Chat Log", ln=True, align="C")
    pdf.ln(10)
    for msg in st.session_state["messages"]:
        role = "You" if msg["role"] == "user" else "WoundBot"
        lines = (f"{role}: {msg['content']}").splitlines()
        for line in lines:
            pdf.multi_cell(0, 8, line)
        pdf.ln(2)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
        pdf.output(tmpfile.name)
        with open(tmpfile.name, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
            st.markdown(f'<a href="data:application/octet-stream;base64,{b64}" download="Wound_Care_Chat_Log.pdf">Download Chat PDF</a>', unsafe_allow_html=True)
