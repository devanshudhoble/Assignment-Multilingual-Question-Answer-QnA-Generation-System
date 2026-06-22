"""
Multilingual QnA Generation System
====================================
Streamlit-based UI for generating Question-Answer pairs from documents
in English, Hindi, and Marathi using Google Gemini API.

Usage:
    streamlit run app.py
"""

import streamlit as st
import time
from document_parser import extract_text
from qna_generator import generate_multilingual_qna
from excel_writer import create_excel

# ─── Page Configuration ───────────────────────────────────────────────
st.set_page_config(
    page_title="Multilingual QnA Generator",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS for Premium Look ──────────────────────────────────────
st.markdown("""
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global font */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main header */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
    }
    .main-header h1 {
        color: white;
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .main-header p {
        color: rgba(255,255,255,0.85);
        font-size: 1.05rem;
        margin-top: 0.5rem;
        font-weight: 300;
    }
    
    /* Feature badges */
    .feature-row {
        display: flex;
        justify-content: center;
        gap: 12px;
        margin-top: 1rem;
        flex-wrap: wrap;
    }
    .feature-badge {
        background: rgba(255,255,255,0.2);
        color: white;
        padding: 6px 16px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.15);
    }
    
    /* Cards */
    .info-card {
        background: #f8f9fc;
        border: 1px solid #e8ecf4;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    .info-card h3 {
        color: #1a1a2e;
        margin-top: 0;
        font-size: 1.1rem;
    }
    
    /* Step indicator */
    .step-indicator {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 12px 18px;
        background: #eef2ff;
        border-radius: 10px;
        margin-bottom: 0.8rem;
        border-left: 4px solid #667eea;
    }
    .step-number {
        background: #667eea;
        color: white;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.85rem;
        flex-shrink: 0;
    }
    .step-text {
        color: #333;
        font-weight: 500;
        font-size: 0.95rem;
    }
    
    /* Stats row */
    .stats-row {
        display: flex;
        gap: 12px;
        margin: 1rem 0;
    }
    .stat-box {
        flex: 1;
        background: linear-gradient(135deg, #f5f7ff, #eef2ff);
        border: 1px solid #d4daef;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    .stat-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #667eea;
    }
    .stat-label {
        font-size: 0.8rem;
        color: #666;
        margin-top: 2px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Success banner */
    .success-banner {
        background: linear-gradient(135deg, #00b894 0%, #00cec9 100%);
        color: white;
        padding: 1.2rem 1.5rem;
        border-radius: 12px;
        text-align: center;
        font-weight: 600;
        font-size: 1.1rem;
        margin: 1rem 0;
        box-shadow: 0 6px 20px rgba(0, 184, 148, 0.3);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px 10px 0 0;
        padding: 10px 24px;
        font-weight: 600;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }
    [data-testid="stSidebar"] * {
        color: #e0e0e0 !important;
    }
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: #ffffff !important;
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ─── Sidebar ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    st.markdown("---")
    
    api_key = st.text_input(
        "🔑 Google Gemini API Key",
        type="password",
        placeholder="Enter your Gemini API key...",
        help="Get a free key at https://aistudio.google.com/apikey",
    )
    
    st.markdown("---")
    
    num_pairs = st.slider(
        "📊 Number of QnA Pairs",
        min_value=5,
        max_value=25,
        value=10,
        step=1,
        help="Number of Question-Answer pairs to generate per language",
    )
    
    st.markdown("---")
    st.markdown("### 📁 Supported Formats")
    st.markdown("""
    - 📄 **PDF** (.pdf)
    - 📝 **Word** (.docx)
    - 📃 **Text** (.txt)
    """)
    
    st.markdown("---")
    st.markdown("### 🌐 Output Languages")
    st.markdown("""
    - 🇬🇧 **English**
    - 🇮🇳 **Hindi** (हिन्दी)
    - 🇮🇳 **Marathi** (मराठी)
    """)
    
    st.markdown("---")
    st.markdown(
        "<div style='text-align:center; opacity:0.5; font-size:0.8rem;'>"
        "Powered by Google Gemini API"
        "</div>",
        unsafe_allow_html=True,
    )

# ─── Main Content ─────────────────────────────────────────────────────

# Header
st.markdown("""
<div class="main-header">
    <h1>🌐 Multilingual QnA Generator</h1>
    <p>Transform any document into intelligent Question-Answer pairs in English, Hindi & Marathi</p>
    <div class="feature-row">
        <span class="feature-badge">📄 PDF / DOCX / TXT</span>
        <span class="feature-badge">🤖 AI-Powered</span>
        <span class="feature-badge">🌍 3 Languages</span>
        <span class="feature-badge">📊 Excel Export</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Workflow steps
st.markdown("""
<div class="step-indicator">
    <div class="step-number">1</div>
    <div class="step-text">Enter your Gemini API key in the sidebar</div>
</div>
<div class="step-indicator">
    <div class="step-number">2</div>
    <div class="step-text">Upload a document (.pdf, .docx, or .txt)</div>
</div>
<div class="step-indicator">
    <div class="step-number">3</div>
    <div class="step-text">Click "Generate QnA" and download your Excel file</div>
</div>
""", unsafe_allow_html=True)

st.markdown("")

# File uploader
uploaded_file = st.file_uploader(
    "📂 Upload Your Document",
    type=["pdf", "docx", "txt"],
    help="Upload a document in PDF, DOCX, or TXT format",
)

# Display file info
if uploaded_file:
    file_size = uploaded_file.size
    size_str = f"{file_size / 1024:.1f} KB" if file_size < 1024 * 1024 else f"{file_size / (1024*1024):.2f} MB"
    
    st.markdown(f"""
    <div class="stats-row">
        <div class="stat-box">
            <div class="stat-value">📄</div>
            <div class="stat-label">{uploaded_file.name}</div>
        </div>
        <div class="stat-box">
            <div class="stat-value">{size_str}</div>
            <div class="stat-label">File Size</div>
        </div>
        <div class="stat-box">
            <div class="stat-value">{uploaded_file.name.split('.')[-1].upper()}</div>
            <div class="stat-label">Format</div>
        </div>
        <div class="stat-box">
            <div class="stat-value">{num_pairs}</div>
            <div class="stat-label">QnA Pairs</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Generate button
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    generate_btn = st.button(
        "🚀 Generate Multilingual QnA",
        use_container_width=True,
        type="primary",
        disabled=not (uploaded_file and api_key),
    )

if not api_key:
    st.info("👈 Please enter your **Gemini API key** in the sidebar to get started.")

if uploaded_file and api_key and generate_btn:
    try:
        # ── Step 1: Extract text ──
        with st.spinner("📝 Extracting text from document..."):
            uploaded_file.seek(0)
            extracted_text = extract_text(uploaded_file, uploaded_file.name)
        
        if not extracted_text or len(extracted_text.strip()) < 50:
            st.error("⚠️ Could not extract enough text from the document. Please try a different file.")
            st.stop()
        
        # Show extracted text preview
        with st.expander("📄 Extracted Text Preview", expanded=False):
            st.text(extracted_text[:3000] + ("..." if len(extracted_text) > 3000 else ""))
            st.caption(f"Total characters: {len(extracted_text):,}")
        
        # ── Step 2: Generate QnA ──
        progress_bar = st.progress(0, text="Initializing QnA generation...")
        status_text = st.empty()
        
        def update_progress(step, total, message):
            progress_bar.progress(step / total, text=message)
            status_text.markdown(f"**{message}**")
        
        results = generate_multilingual_qna(
            text=extracted_text,
            api_key=api_key,
            num_pairs=num_pairs,
            progress_callback=update_progress,
        )
        
        progress_bar.progress(1.0, text="✅ All QnA pairs generated successfully!")
        time.sleep(0.5)
        status_text.empty()
        
        # ── Step 3: Display Results ──
        st.markdown('<div class="success-banner">✅ QnA Generation Complete — All 3 Languages Ready!</div>', unsafe_allow_html=True)
        
        # Show results in tabs
        tab_en, tab_hi, tab_mr = st.tabs(["🇬🇧 English", "🇮🇳 Hindi (हिन्दी)", "🇮🇳 Marathi (मराठी)"])
        
        with tab_en:
            st.markdown(f"### English QnA Pairs ({len(results['english'])} pairs)")
            for i, pair in enumerate(results["english"], 1):
                q = pair.get("question", pair.get("Question", ""))
                a = pair.get("answer", pair.get("Answer", ""))
                with st.container():
                    st.markdown(f"**Q{i}.** {q}")
                    st.markdown(f"**A{i}.** {a}")
                    st.markdown("---")
        
        with tab_hi:
            st.markdown(f"### हिन्दी QnA ({len(results['hindi'])} pairs)")
            for i, pair in enumerate(results["hindi"], 1):
                q = pair.get("question", pair.get("Question", ""))
                a = pair.get("answer", pair.get("Answer", ""))
                with st.container():
                    st.markdown(f"**Q{i}.** {q}")
                    st.markdown(f"**A{i}.** {a}")
                    st.markdown("---")
        
        with tab_mr:
            st.markdown(f"### मराठी QnA ({len(results['marathi'])} pairs)")
            for i, pair in enumerate(results["marathi"], 1):
                q = pair.get("question", pair.get("Question", ""))
                a = pair.get("answer", pair.get("Answer", ""))
                with st.container():
                    st.markdown(f"**Q{i}.** {q}")
                    st.markdown(f"**A{i}.** {a}")
                    st.markdown("---")
        
        # ── Step 4: Generate Excel ──
        st.markdown("")
        st.markdown("### 📥 Download Excel Output")
        
        excel_buffer = create_excel(
            english_qna=results["english"],
            hindi_qna=results["hindi"],
            marathi_qna=results["marathi"],
        )
        
        col_a, col_b, col_c = st.columns([1, 2, 1])
        with col_b:
            st.download_button(
                label="📥 Download QnA.xlsx",
                data=excel_buffer,
                file_name="QnA.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                type="primary",
            )
        
        st.markdown("""
        <div class="info-card">
            <h3>📊 Excel File Details</h3>
            <ul>
                <li><strong>File Name:</strong> QnA.xlsx</li>
                <li><strong>Sheet 1:</strong> English — QnA pairs in English</li>
                <li><strong>Sheet 2:</strong> Hindi — QnA pairs in हिन्दी</li>
                <li><strong>Sheet 3:</strong> Marathi — QnA pairs in मराठी</li>
                <li><strong>Columns:</strong> Questions, Answers</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"❌ An error occurred: {str(e)}")
        st.markdown("**Possible fixes:**")
        st.markdown("- Check that your Gemini API key is valid")
        st.markdown("- Ensure the document has readable text content")
        st.markdown("- Try a smaller document or fewer QnA pairs")
        with st.expander("🔧 Full Error Details"):
            st.exception(e)
