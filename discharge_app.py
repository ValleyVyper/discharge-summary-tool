import streamlit as st
from pdf2image import convert_from_bytes
from PIL import Image
import google.generativeai as genai
import markdown
from weasyprint import HTML

st.set_page_config(page_title="Discharge Summary Generator", page_icon="🏥", layout="wide")

# ====================== PASSWORD PROTECTION ======================
if "password_correct" not in st.session_state:
    st.session_state.password_correct = False

if not st.session_state.password_correct:
    st.title("🔒 Discharge Summary Tool - Login")
    st.subheader("DEPT OF SALYATANTRA, GOVT AYURVEDA COLLEGE, TVM")
    
    password = st.text_input("Enter Password", type="password")
    
    if st.button("Login", type="primary"):
        if password == st.secrets["app_password"]:
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("❌ Wrong password")
    st.stop()  # Stop here until password is correct

# ====================== MAIN APP (only visible after login) ======================
st.title("🏥 Discharge Summary Automation Tool")

# ====================== DEBUG: SHOW AVAILABLE MODELS ======================
if st.button("🔍 Show Available Gemini Models for my Key"):
    with st.spinner("Fetching available models..."):
        genai.configure(api_key=st.secrets["gemini_key"])
        available_models = genai.list_models()
        st.success("✅ Here are the models your API key can use:")
        for model in available_models:
            st.write(f"• **{model.name}**")
            if "flash" in model.name.lower():
                st.caption("← Recommended for fast discharge summary")


st.subheader("DEPT OF SALYATANTRA, GOVT AYURVEDA COLLEGE, TVM")
st.caption("Upload patient PDF or images → Gemini AI generates exact discharge summary + PDF")

# ====================== YOUR EXACT TEMPLATE ======================
EXAMPLE_TEMPLATE = """DISCHARGE SUMMARY 

DEPT OF SALYATANTRA, GOVT AYURVEDA COLLEGE, TVM 

NAME                            :   
AGE AND SEX               :     
ADDRESS                       :     
ADMISSION DATE         :                                        OP NO:     
DISCHARGE DATE         :                                        IP NO:       WARD:     
CONSULTED PHYSICIAN:   

DIAGNOSIS:   

PRESENTING COMPLAINTS     
C/O   

HISTORY OF PRESENT ILLNESS IN BRIEF     

HISTORY OF PAST ILLNESS    

SURGICAL HISTORY    

INVESTIGATIONS    

Other blood parameters within normal limits.   

EXTERNAL FINDINGS:    

PRE OP    
OP    
POST OP    

SURGERY DONE:     

INTERNAL MEDICATIONS     

SL.NO   MEDICINES   DOSE    

EXTERNAL MEDICATION:    

DISCHARGE MEDICINES:    

SL.NO   MEDICINES   DOSE    

ADVICE ON DISCHARGE    

PREPARED BY                                                                            MEDICAL OFFICER IN CHARGE"""

# ====================== SYSTEM PROMPT ======================
SYSTEM_PROMPT = f"""You are an expert medical discharge summary generator for the Department of Salyatantra, Govt Ayurveda College, TVM.

Your ONLY job is to create a discharge summary in the **EXACT same format, layout, section headings, and table style** as the example template below.

Example template:
{EXAMPLE_TEMPLATE}

Rules:
- Auto-detect and correctly fill: patient name, age/sex, address, dates, OP/IP numbers, ward, physicians, diagnosis, complaints, history, investigations, external findings, surgery details, medicines (exact names & dosages), advice, etc.
- Use exact Ayurvedic medicine spellings and format as they appear in the uploaded documents.
- Create proper markdown tables for INTERNAL MEDICATIONS, DISCHARGE MEDICINES, and PRE-OP/OP/POST-OP.
- If any information is missing, write "Not mentioned".
- Output **ONLY** the completed discharge summary. No extra text, no explanations."""

# ====================== FILE UPLOAD ======================
uploaded_files = st.file_uploader(
    "Upload Patient Data (PDF preferred or multiple images)",
    type=["pdf", "png", "jpg", "jpeg"],
    accept_multiple_files=True
)

if uploaded_files:
    images = []

    pdf_files = [f for f in uploaded_files if f.type == "application/pdf"]
    if pdf_files:
        pdf_file = pdf_files[0]
        st.info(f"Processing PDF: {pdf_file.name}")
        images = convert_from_bytes(pdf_file.getvalue(), dpi=300)
    else:
        st.info(f"Processing {len(uploaded_files)} image(s)")
        for file in uploaded_files:
            img = Image.open(file)
            images.append(img)

    st.success(f"✅ {len(images)} page(s) loaded successfully!")

    if st.button("🚀 Generate Discharge Summary", type="primary"):
        with st.spinner("Gemini is reading all pages and generating exact summary... (~10-20 seconds)"):
            genai.configure(api_key=st.secrets["gemini_key"])
            
            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                system_instruction=SYSTEM_PROMPT,
                generation_config={"temperature": 0.0}
            )

            contents = ["Here is the complete patient data (all pages). Generate the discharge summary in the exact required format."]
            for img in images:
                contents.append(img)

            response = model.generate_content(contents)
            summary = response.text

            # ====================== DISPLAY & DOWNLOADS ======================
            st.subheader("📄 Generated Discharge Summary")
            st.markdown(summary)

            # Convert markdown → beautiful PDF
            md = markdown.markdown(summary, extensions=['tables', 'nl2br'])
            css = """
            <style>
            @page { margin: 2cm; }
            body { font-family: Arial, sans-serif; font-size: 11pt; line-height: 1.6; }
            h1 { text-align: center; font-size: 16pt; margin-bottom: 10px; }
            h2 { font-size: 12pt; margin-top: 25px; margin-bottom: 5px; }
            table { border-collapse: collapse; width: 100%; margin: 15px 0; }
            th, td { border: 1px solid #000; padding: 8px; text-align: left; vertical-align: top; }
            th { background-color: #f5f5f5; }
            </style>
            """
            full_html = css + md
            pdf_bytes = HTML(string=full_html).write_pdf()

            # Download buttons
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="⬇️ Download as PDF (Recommended)",
                    data=pdf_bytes,
                    file_name="DISCHARGE_SUMMARY.pdf",
                    mime="application/pdf",
                    type="primary"
                )
            with col2:
                st.download_button(
                    label="⬇️ Download as Markdown (.md)",
                    data=summary,
                    file_name="DISCHARGE_SUMMARY.md",
                    mime="text/markdown"
                )

            st.success("✅ Done! PDF is ready for printing or sharing.")

# Logout button (optional)
if st.button("🔓 Logout"):
    st.session_state.password_correct = False
    st.rerun()
