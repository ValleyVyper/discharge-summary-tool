import streamlit as st
from pdf2image import convert_from_bytes
from PIL import Image
import google.generativeai as genai

st.set_page_config(page_title="Discharge Summary Generator", page_icon="🏥", layout="wide")
st.title("🏥 Discharge Summary Automation Tool")
st.subheader("DEPT OF SALYATANTRA, GOVT AYURVEDA COLLEGE, TVM")
st.caption("Upload patient PDF or images → Gemini AI generates exact discharge summary")

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

    # Handle PDF (converts to high-quality images)
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

    gemini_key = st.text_input(
        "🔑 Gemini API Key (free from https://aistudio.google.com/app/apikey)",
        type="password",
        value=""
    )

    if st.button("🚀 Generate Discharge Summary", type="primary"):
        if not gemini_key:
            st.error("Please enter your Gemini API key")
        else:
            with st.spinner("Gemini is reading all pages and generating exact summary... (~10-20 seconds)"):
                genai.configure(api_key=gemini_key)
                
                model = genai.GenerativeModel(
                    model_name="gemini-1.5-pro",
                    system_instruction=SYSTEM_PROMPT,
                    generation_config={"temperature": 0.0}
                )

                # Prepare content (text + all images)
                contents = ["Here is the complete patient data (all pages). Generate the discharge summary in the exact required format."]
                for img in images:
                    contents.append(img)   # Gemini accepts PIL images directly

                response = model.generate_content(contents)
                summary = response.text

                # Display result
                st.subheader("📄 Generated Discharge Summary")
                st.markdown(summary)

                # Download buttons
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="⬇️ Download as Markdown (.md)",
                        data=summary,
                        file_name="DISCHARGE_SUMMARY.md",
                        mime="text/markdown"
                    )
                with col2:
                    st.info("Tip: Open .md in Google Docs / Word on your phone → Save as PDF")

                st.success("✅ Done! Ready to print or save.")
