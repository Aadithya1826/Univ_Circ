from flask import Flask, request, jsonify, render_template
import os
import pytesseract
from pdfminer.high_level import extract_text as extract_pdf
from docx import Document
from PIL import Image
import psycopg2
import smtplib
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from llama_cpp import Llama
from sentence_transformers import util
from functools import lru_cache
from google.cloud import storage

UPLOAD_FOLDER = './uploads'
EMBEDDER_DIR = './sentence_model'
EMBEDDER_GCS_PATH = 'sentence_model/'
BUCKET_NAME = 'univ_circ'
MODEL_PATH = './models/mistral-7b-instruct-v0.1.Q4_K_M.gguf'
MODEL_GCS_PATH = 'mistral-7b-instruct-v0.1.Q4_K_M.gguf'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)

pytesseract.pytesseract.tesseract_cmd = r"/usr/bin/tesseract"

def download_from_gcs(bucket_name, gcs_path, local_path):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(gcs_path)
    blob.download_to_filename(local_path)

if not os.path.exists(MODEL_PATH):
    download_from_gcs(BUCKET_NAME, MODEL_GCS_PATH, MODEL_PATH)

if not os.path.exists(EMBEDDER_DIR):
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blobs = client.list_blobs(BUCKET_NAME, prefix=EMBEDDER_GCS_PATH)
    for blob in blobs:
        rel_path = blob.name[len(EMBEDDER_GCS_PATH):].lstrip('/')
        local_path = os.path.join(EMBEDDER_DIR, rel_path)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        blob.download_to_filename(local_path)

@lru_cache()
def get_embedder():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(EMBEDDER_DIR)

llm = Llama(model_path=MODEL_PATH, n_ctx=4096, n_threads=8, n_batch=512)

def get_db_connection():
    return psycopg2.connect(
        dbname=os.environ.get('DB_NAME'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASS'),
        host=os.environ.get('DB_HOST'),
        port=os.environ.get('DB_PORT', 5432)
    )

def extract_text(file_path):
    ext = file_path.split('.')[-1].lower()
    if ext == 'pdf':
        return extract_pdf(file_path)
    elif ext == 'docx':
        return "\n".join([p.text for p in Document(file_path).paragraphs])
    elif ext in ['png', 'jpg', 'jpeg']:
        return pytesseract.image_to_string(Image.open(file_path))
    return ''

def summarize_text(text):
    prompt = f"[INST] Summarize the university circular:\n\n{text} [/INST]"
    output = llm(prompt, max_tokens=300, stop=["</s>"])
    return output["choices"][0]["text"].strip()

def get_department_info():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT department FROM students")
            return [row[0] for row in cur.fetchall()]

def detect_departments_by_similarity(summary):
    departments = get_department_info()
    dept_embeddings = get_embedder().encode(departments, convert_to_tensor=True)
    summary_embedding = get_embedder().encode(summary, convert_to_tensor=True)
    scores = util.cos_sim(summary_embedding, dept_embeddings)[0]
    best_score = scores.max().item()
    return [departments[scores.argmax().item()]] if best_score > 0.5 else ['ALL']

def get_students(departments):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            if 'ALL' in departments:
                cur.execute("SELECT name, email FROM students")
            else:
                cur.execute("SELECT name, email FROM students WHERE department = ANY(%s)", (departments,))
            return cur.fetchall()

def send_email(name, email, summary, file_path):
    def send():
        msg = MIMEMultipart()
        msg['From'] = 'admin@univ.edu'
        msg['To'] = email
        msg['Subject'] = 'University Circular Update'

        body = f"Dear {name},\n\nHere is a summary of the latest circular:\n\n{summary}\n\nRegards,\nAdmin"
        msg.attach(MIMEText(body, 'plain'))

        with open(file_path, 'rb') as f:
            part = MIMEApplication(f.read(), Name=os.path.basename(file_path))
        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
        msg.attach(part)

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(os.environ.get("EMAIL_USER"), os.environ.get("EMAIL_PASS"))
        server.send_message(msg)
        server.quit()

    threading.Thread(target=send).start()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_and_process():
    file = request.files['file']
    filename = file.filename
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    text = extract_text(filepath)
    summary = summarize_text(text)
    departments = detect_departments_by_similarity(summary)
    students = get_students(departments)

    for name, email in students:
        send_email(name, email, summary, filepath)

    return jsonify({'summary': summary, 'status': f"Summary sent to: {', '.join(departments)} department(s)."})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
