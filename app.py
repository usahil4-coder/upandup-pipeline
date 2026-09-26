import streamlit as st
import pandas as pd
import json
import urllib.parse
import os
import pdfplumber
from groq import Groq

# Page Config
st.set_page_config(layout="wide", page_title="UpAndUp Life - Bulk Lead Pipeline")

# Initialize Session State for Data
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["Company", "Mobile", "Decision Maker", "Email", "Website", "Pitch", "Status"])

# Sidebar for API Key
st.sidebar.title("⚙️ Config")
api_key = st.sidebar.text_input("Enter Groq API Key", type="password")
st.sidebar.markdown("Get it from [console.groq.com](https://console.groq.com/)")

def extract_leads(text_data):
    if not api_key:
        st.error("Please add Groq API Key in sidebar!")
        return []
    try:
        client = Groq(api_key=api_key)
        prompt = '''You are an expert data extractor. Extract ALL business leads from the raw text below.
Return ONLY a valid JSON object with a single key "leads" containing an array of objects.
Object keys must exactly be: "Company", "Mobile", "Decision Maker", "Email", "Website".
If a value is missing, return an empty string "". Extract as many as you can find.
Text: ''' + text_data
        
        res = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        data = json.loads(res.choices[0].message.content)
        return data.get("leads", [])
    except Exception as e:
        st.error(f"Error during extraction: {e}")
        return []

def get_pitch(company, name):
    if not api_key: return "API Key missing"
    try:
        client = Groq(api_key=api_key)
        prompt = f"Write a professional, 2-line WhatsApp pitch in Hinglish for {company} (Contact: {name}). Pitch 'UpAndUp Life' - a platform for managing workers, attendance, and workforce tracking. Make it specific to their business. No placeholders."
        res = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}]
        )
        return res.choices[0].message.content.strip()
    except:
        return "Error generating pitch"

st.title("🚀 UpAndUp Life - Intelligent Outbound System")

tab1, tab2 = st.tabs(["📥 1. Add & Extract Leads", "📊 2. Lead Dashboard & Action Center"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Mass Text Extraction")
        raw_text = st.text_area("Paste unstructured text, chats, or website data here:", height=200)
        if st.button("Extract Leads from Text"):
            with st.spinner("AI is parsing data..."):
                extracted = extract_leads(raw_text)
                if extracted:
                    new_df = pd.DataFrame(extracted)
                    new_df["Pitch"] = ""
                    new_df["Status"] = "Pending"
                    st.session_state.df = pd.concat([st.session_state.df, new_df], ignore_index=True)
                    st.success(f"{len(extracted)} leads successfully extracted and added!")

    with col2:
        st.subheader("File Upload (CSV, Excel, PDF)")
        uploaded_file = st.file_uploader("Upload documents for bulk adding", type=["csv", "xlsx", "pdf"])
        if uploaded_file and st.button("Process File"):
            with st.spinner("Processing file..."):
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                    st.session_state.df = pd.concat([st.session_state.df, df], ignore_index=True)
                    st.success("CSV Leads added!")
                elif uploaded_file.name.endswith('.xlsx'):
                    df = pd.read_excel(uploaded_file)
                    st.session_state.df = pd.concat([st.session_state.df, df], ignore_index=True)
                    st.success("Excel Leads added!")
                elif uploaded_file.name.endswith('.pdf'):
                    text = ""
                    with pdfplumber.open(uploaded_file) as pdf:
                        for page in pdf.pages:
                            text += (page.extract_text() or "") + " "
                    extracted = extract_leads(text)
                    if extracted:
                        new_df = pd.DataFrame(extracted)
                        new_df["Pitch"] = ""
                        new_df["Status"] = "Pending"
                        st.session_state.df = pd.concat([st.session_state.df, new_df], ignore_index=True)
                        st.success(f"Extracted {len(extracted)} leads from PDF!")

with tab2:
    st.subheader("Dynamic Lead Grid")
    
    # Custom column viewer
    all_cols = st.session_state.df.columns.tolist()
    default_cols = ["Company", "Mobile", "Decision Maker", "Pitch", "Status"]
    show_cols = st.multiselect("Toggle Columns (Company & Mobile are mandatory)", all_cols, default=default_cols)
    
    # Ensure mandatory columns are present
    if "Company" not in show_cols: show_cols.insert(0, "Company")
    if "Mobile" not in show_cols: show_cols.insert(1, "Mobile")
    show_cols = list(dict.fromkeys(show_cols)) # Remove duplicates

    if not st.session_state.df.empty:
        # Spreadsheet Editor
        edited_df = st.data_editor(st.session_state.df[show_cols], num_rows="dynamic", use_container_width=True)
        st.session_state.df.update(edited_df)
        
        st.markdown("---")
        st.subheader("Action Center")
        
        # Action Buttons per row
        for idx, row in st.session_state.df.iterrows():
            company = row.get('Company', 'Unknown')
            mobile = str(row.get('Mobile', ''))
            status = row.get('Status', 'Pending')
            
            if pd.isna(company) or not str(company).strip(): continue
            if pd.isna(mobile) or not mobile.strip(): continue
            
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.markdown(f"**{company}** | 📱 {mobile}")
            
            # Generate Button
            if c2.button("Generate Pitch", key=f"gen_{idx}"):
                with st.spinner("Writing..."):
                    new_pitch = get_pitch(company, row.get('Decision Maker', 'Sir/Madam'))
                    st.session_state.df.at[idx, 'Pitch'] = new_pitch
                    st.rerun()
            
            # Send Button & Delete Logic
            if status == "Sent":
                c3.error("Message Sent (Locked)")
                if c3.button("Delete Log", key=f"del_{idx}"):
                    st.session_state.df.at[idx, 'Status'] = "Pending"
                    st.rerun()
            else:
                pitch_text = row.get('Pitch', '')
                clean_mobile = ''.join(filter(str.isdigit, mobile))
                encoded_msg = urllib.parse.quote(str(pitch_text))
                link = f"https://api.whatsapp.com/send?phone=91{clean_mobile}&text={encoded_msg}"
                
                c3.markdown(f'<a href="{link}" target="_blank"><button style="background-color:#25D366; color:white; border:none; padding:5px 15px; border-radius:5px; width:100%; cursor:pointer;">Send WA</button></a>', unsafe_allow_html=True)
                if c3.button("Mark Sent", key=f"mark_{idx}"):
                    st.session_state.df.at[idx, 'Status'] = "Sent"
                    st.rerun()
    else:
        st.info("No leads available. Go to Tab 1 to add data.")
