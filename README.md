# UpAndUp Life - Lead Extractor & WhatsApp Sender

## Deployment on Termux (Android)
1. Install basic packages:
   `pkg update && pkg upgrade -y`
   `pkg install python git clang -y`
2. Unzip this folder and navigate into it:
   `cd upandup_app`
3. Install requirements (this might take a few minutes):
   `pip install -r requirements.txt`
4. Run the application:
   `streamlit run app.py`

## Cloud Deployment (Vercel / Railway / Streamlit Cloud)
1. Upload this extracted folder to a GitHub repository.
2. Go to [share.streamlit.io](https://share.streamlit.io/) or Railway.
3. Deploy the repository. The environment will automatically read `requirements.txt`.
4. Add your Groq API Key directly in the sidebar of the live website!
