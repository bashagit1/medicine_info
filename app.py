import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter
import io
import os
from dotenv import load_dotenv
from openai import OpenAI
import pytesseract

# Load environment variables
load_dotenv()

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Set page configuration
st.set_page_config(page_title="Medication Info App", layout="centered")

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'query_history' not in st.session_state:
    st.session_state.query_history = []
if 'on_landing_page' not in st.session_state:
    st.session_state.on_landing_page = True
if 'navigation_history' not in st.session_state:
    st.session_state.navigation_history = []  # To track navigation history

# Custom CSS styling for modern 3D-style UI
st.markdown("""
<style>
body {
    font-family: 'Segoe UI', sans-serif;
    background: linear-gradient(135deg, #f5f7fa 0%, #e4e8f0 100%);
    color: #202124;
}

.stApp {
    max-width: 850px;
    margin: 0 auto;
    padding: 30px;
    background-color: white;
    border-radius: 20px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

h1, h2, h3 {
    color: #1a73e8;
    text-align: center;
}

h1 {
    font-size: 2.5rem;
    margin-bottom: 10px;
    padding-bottom: 10px;
    border-bottom: 3px solid #e8eaed;
}

h2 {
    font-size: 1.8rem;
    margin-top: 25px;
    color: #1a73e8;
}

h3 {
    font-size: 1.5rem;
}

.stButton>button {
    background: linear-gradient(135deg, #1a73e8 0%, #4285f4 100%);
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    display: flex;
    align-items: center;
    gap: 8px;
}

.stButton>button:hover {
    background: linear-gradient(135deg, #4285f4 0%, #1a73e8 100%);
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.stTextInput>div>div>input {
    padding: 12px;
    border: 2px solid #e8eaed;
    border-radius: 8px;
    font-size: 16px;
    transition: border-color 0.3s ease;
}

.stTextInput>div>div>input:focus {
    border-color: #1a73e8;
    box-shadow: 0 0 0 2px rgba(26, 115, 232, 0.2);
}

.stFileUploader>div>div>input {
    padding: 12px;
    border: 2px dashed #e8eaed;
    border-radius: 8px;
    font-size: 16px;
    transition: border-color 0.3s ease;
}

.stFileUploader>div>div>input:focus {
    border-color: #1a73e8;
    box-shadow: 0 0 0 2px rgba(26, 115, 232, 0.2);
}

.stRadio>div>div {
    display: flex;
    justify-content: center;
    gap: 20px;
    margin: 25px 0;
}

.stRadio>div>div>div {
    background-color: #f8f9fa;
    padding: 10px 20px;
    border-radius: 20px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    gap: 8px;
}

.stRadio>div>div>div:hover {
    background-color: #e8eaed;
}

.stRadio>div>div>div[data-baseweb="radio"]:hover {
    background-color: #e8eaed;
}

.stSpinner {
    text-align: center;
}

.stMarkdown {
    background-color: #f8f9fa;
    padding: 15px;
    border-radius: 8px;
    border-left: 4px solid #1a73e8;
}

/* Error messages */
.stError {
    background-color: #ff7961;
    color: white;
    padding: 10px;
    border-radius: 8px;
    margin: 10px 0;
}

/* Success messages */
.stSuccess {
    background-color: #4caf50;
    color: white;
    padding: 10px;
    border-radius: 8px;
    margin: 10px 0;
}

/* Image display */
.stImage {
    text-align: center;
}

.stImage img {
    max-width: 100%;
    border-radius: 10px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    margin: 15px 0;
}

/* Card styling */
.card {
    background-color: #f8f9fa;
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
    margin: 20px 0;
}

/* Header styling */
header {
    display: none;
}

/* Footer styling */
footer {
    display: none;
}

/* Navigation header */
.nav-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 15px 0;
    border-bottom: 1px solid #e8eaed;
    margin-bottom: 20px;
}

.nav-button {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 5px;
}

.nav-button i {
    font-size: 1.2rem;
}

/* Title styling */
.main-title {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    margin: 30px 0;
}

.pill-icon {
    width: 40px;
    height: 40px;
}
</style>
""", unsafe_allow_html=True)

# Image processing functions
def enhance_image(image):
    """Enhance image contrast and sharpness"""
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.5)
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(1.5)
    return image

def preprocess_image(image):
    """Convert to grayscale and apply thresholding"""
    image = image.convert('L')
    image = image.point(lambda x: 0 if x < 128 else 255, '1')
    return image

def analyze_image(image):
    """Analyze image using multiple OCR approaches"""
    text = ""
    
    # First attempt: original image
    text += pytesseract.image_to_string(image) + "\n"
    
    # Second attempt: enhanced image
    enhanced = enhance_image(image.copy())
    text += pytesseract.image_to_string(enhanced) + "\n"
    
    # Third attempt: preprocessed image
    processed = preprocess_image(image.copy())
    text += pytesseract.image_to_string(processed) + "\n"
    
    return text

# Authentication system (simplified for demonstration)
def login_form():
    st.title("🔒 Secure Login")
    username = st.text_input("Username", placeholder="Enter your username")
    password = st.text_input("Password", type="password", placeholder="Enter your password")
    if st.button("Login"):
        # Dummy authentication - replace with proper validation
        if username == "admin" and password == "admin123":
            st.session_state.logged_in = True
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid credentials")
    return st.session_state.logged_in

# Landing page content
def show_landing_page():
    st.title("Welcome to Medication Information Lookup")
    st.header("Your Trusted Medication Information Assistant")
    
    # Main image of doctor and nurse
    st.image("d1.png", 
             caption="Healthcare Professionals Collaborating", 
             use_container_width=True)
    
    st.markdown("""
    This application helps healthcare professionals quickly find detailed information about medications. 
    Simply enter a medication name or upload an image of the medication packaging, and we'll provide:
    
    - Primary uses
    - Benefits
    - Side effects
    - Patient selection criteria
    - Dosage guidelines
    - Important precautions
    
    The app leverages advanced AI technology to deliver accurate and comprehensive information.
    """)
    
    # Additional images and descriptions
    st.subheader("Why Choose Our Medication Lookup App?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.image("d2.png", 
                 caption="Quick and Accurate Information", 
                 use_container_width=True)
        st.markdown("""
        **Instant Access to Information**
        
        Get the medication details you need in seconds, 
        helping you make informed decisions faster.
        """)
    
    with col2:
        st.image("d3.png", 
                 caption="Advanced AI Technology", 
                 use_container_width=True)
        st.markdown("""
        **Powered by AI**
        
        Our app uses advanced artificial intelligence to 
        analyze images and provide comprehensive medication information.
        """)
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.image("d4.png", 
                 caption="User-Friendly Interface", 
                 use_container_width=True)
        st.markdown("""
        **Easy to Use**
        
        Simple interface designed for healthcare 
        professionals with intuitive navigation.
        """)
    
    with col4:
        st.image("d6.png", 
                 caption="Comprehensive Database", 
                 use_container_width=True)
        st.markdown("""
        **Extensive Medication Database**
        
        Access information on thousands of medications, 
        including generic and brand-name drugs.
        """)
    
    # Call to action
    if st.button("Get Started"):
        st.session_state.on_landing_page = False
        st.session_state.navigation_history.append("landing_page")
        st.rerun()

# Navigation header
def show_navigation_header():
    col1, col2, col3 = st.columns([1, 10, 1])
    
    with col1:
        if st.button("🏠 Home"):
            st.session_state.on_landing_page = True
            st.session_state.navigation_history = []
            st.rerun()
    
    with col3:
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.session_state.on_landing_page = True
            st.session_state.navigation_history = []
            st.rerun()

# Check login
if not st.session_state.logged_in:
    login_form()
    st.stop()

# Show landing page first
if st.session_state.on_landing_page:
    show_landing_page()
else:
    # Show navigation header
    show_navigation_header()
    
    # Main app
    st.markdown('<div class="main-title"><img src="https://cdn-icons-png.flaticon.com/512/1105/1105708.png" class="pill-icon" alt="pill"> <h1>Medication Information Lookup</h1></div>', unsafe_allow_html=True)

    # Navigation menu
    menu = ["🔍 Text Lookup", "🖼️ Image Upload", "📸 Camera Snapshot"]
    choice = st.radio("Select Lookup Method", menu, horizontal=True)

    # Text Lookup Section
    if choice == "🔍 Text Lookup":
        st.session_state.navigation_history.append("text_lookup")
        st.header("🔍 Lookup by Medicine Name")
        
        medication_name = st.text_input("Enter medication name", placeholder="e.g., Paracetamol, Ibuprofen")
        if st.button("🔍 Get Information") and medication_name:
            with st.spinner("🔍 Fetching medication information..."):
                # Add to query history
                st.session_state.query_history.append(f"Text Lookup: {medication_name}")
                
                prompt = f"""
                Provide detailed information about the medication: {medication_name}
                
                Include:
                - Primary use
                - Benefits
                - Side effects
                - Patient selection criteria
                - Dosage guidelines
                - Important precautions
                
                Format the response as markdown.
                """
                
                # OpenAI API call
                response = openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a medical information assistant."},
                        {"role": "user", "content": prompt}
                    ]
                )
                
                info = response.choices[0].message.content
                st.markdown(info)

    # Image Upload Section
    elif choice == "🖼️ Image Upload":
        st.session_state.navigation_history.append("image_upload")
        st.header("🖼️ Lookup by Image Upload")
        
        uploaded_file = st.file_uploader("Upload medication image", type=["jpg", "png", "jpeg"])
        if uploaded_file:
            image = Image.open(uploaded_file)
            
            with st.spinner("🔍 Analyzing image..."):
                # Analyze image with multiple methods
                text = analyze_image(image)
                
                # Add to query history
                st.session_state.query_history.append(f"Image Upload: {text[:50]}...")
                
                # Get medication information
                prompt = f"""
                Analyze the following text extracted from a medication image:
                ```
                {text}
                ```
                
                Identify any medication names mentioned and provide detailed information about them.
                
                For each identified medication, include:
                - Primary use
                - Benefits
                - Side effects
                - Patient selection criteria
                - Dosage guidelines
                - Important precautions
                
                Format the response as markdown.
                """
                
                # OpenAI API call
                response = openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a medical information assistant."},
                        {"role": "user", "content": prompt}
                    ]
                )
                
                info = response.choices[0].message.content
                st.markdown(info)

    # Camera Snapshot Section
    elif choice == "📸 Camera Snapshot":
        st.session_state.navigation_history.append("camera_snapshot")
        st.header("📸 Lookup by Camera Snapshot")
        
        st.write("Take a photo of the medication packaging")
        picture = st.camera_input("📸 Take a snapshot")
        
        if picture:
            image = Image.open(picture)
            st.image(image, caption="Captured Medication Image", use_container_width=True)
            
            with st.spinner("🔍 Analyzing image..."):
                # Analyze image with multiple methods
                text = analyze_image(image)
                st.write("🔍 Text extracted from image:", text)
                
                # Add to query history
                st.session_state.query_history.append(f"Camera Snapshot: {text[:50]}...")
                
                # Get medication information
                prompt = f"""
                Analyze the following text extracted from a medication image:
                ```
                {text}
                ```
                
                Identify any medication names mentioned and provide detailed information about them.
                
                For each identified medication, include:
                - Primary use
                - Benefits
                - Side effects
                - Patient selection criteria
                - Dosage guidelines
                - Important precautions
                
                Format the response as markdown.
                """
                
                # OpenAI API call
                response = openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a medical information assistant."},
                        {"role": "user", "content": prompt}
                    ]
                )
                
                info = response.choices[0].message.content
                st.markdown(info)