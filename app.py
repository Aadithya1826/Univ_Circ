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
from sentence_transformers import SentenceTransformer, util
from huggingface_hub import hf_hub_download

# === Config & Setup ===
UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Tesseract setup (adjust or comment for production)
pytesseract.pytesseract.tesseract_cmd = r"/usr/bin/tesseract"

# === Load Models ===
embedder = SentenceTransformer('all-MiniLM-L6-v2')
llm = Llama(
    model_path=hf_hub_download(
        repo_id="Aadithya1826/Mistral_7B",
        filename="mistral-7b-instruct-v0.1.Q4_K_M.gguf",
        local_dir="./models"
    ),
    n_ctx=4096,
    n_threads=8,
    n_batch=512
)


# === PostgreSQL DB connection helper ===
def get_db_connection():
    return psycopg2.connect(
        dbname=os.environ.get('DB_NAME'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASS'),
        host=os.environ.get('DB_HOST'),
        port=os.environ.get('DB_PORT', 5432)
    )

# === Text Extraction ===
def extract_text(file_path):
    ext = file_path.split('.')[-1].lower()
    if ext == 'pdf':
        return extract_pdf(file_path)
    elif ext == 'docx':
        doc = Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs])
    elif ext in ['png', 'jpg', 'jpeg']:
        return pytesseract.image_to_string(Image.open(file_path))
    return ''

# === Summarization ===
def summarize_text(text):
    prompt = f"[INST] Summarize the university circular:\n\n{text} [/INST]"
    output = llm(prompt, max_tokens=300, stop=["</s>"])
    return output["choices"][0]["text"].strip()

# === Department Detection ===
def get_department_info():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT department FROM students")
            return [row[0] for row in cur.fetchall()]

def detect_departments_by_similarity(summary):
    departments = get_department_info()
    dept_embeddings = embedder.encode(departments, convert_to_tensor=True)
    summary_embedding = embedder.encode(summary, convert_to_tensor=True)
    scores = util.cos_sim(summary_embedding, dept_embeddings)[0]
    best_score = scores.max().item()
    if best_score > 0.5:
        return [departments[scores.argmax().item()]]
    return ['ALL']

def get_students(departments):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            if 'ALL' in departments:
                cur.execute("SELECT name, email FROM students")
            else:
                cur.execute("SELECT name, email FROM students WHERE department = ANY(%s)", (departments,))
            return cur.fetchall()

# === Emailing ===
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

# === Routes ===
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

# === Run on Railway ===
if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

