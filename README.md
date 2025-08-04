
# 📘 GO's REPORT — University Circular Summarizer & Mailer

AI-powered web application that automates the **classification**, **summarization**, and **distribution** of university circulars. Upload a document (PDF, Word, Image, etc.), and the system extracts key information, summarizes it using a local LLM model, detects the relevant departments, and emails the summary with the original file attached.

---

## 🚀 Features

- 📄 **Document Upload** (PDF, DOCX, TXT, JPG, PNG)
- 🧠 **Text Summarization** using LLaMA-based model (`mistral-7b`)
- 🧪 **Department Detection** via Sentence Embeddings
- 📧 **Automatic Emailing** of summary to department students
- 💾 **PostgreSQL Database** for student info
- 📦 **Deployable on Railway**
- 🖼️ **OCR Support** with Tesseract for image files

---

## 🖥️ Tech Stack

- **Backend**: Flask, LLaMA-C++ (LlamaCpp), SentenceTransformers
- **Frontend**: TailwindCSS, HTML5
- **Database**: PostgreSQL
- **Emailing**: SMTP with Gmail
- **OCR**: pytesseract
- **Deployment**: Railway

---

## 📁 Project Structure

```
project/
├── app.py                  # Flask app
├── templates/
│   └── index.html          # UI frontend
├── static/                 # (optional) static assets
├── uploads/                # Temporarily uploaded files
├── mistral-7b...gguf       # LLM model file
├── requirements.txt        # Python dependencies
├── Procfile                # For Railway deployment
├── .env.example            # Template for secrets
└── README.md
```

---

## ⚙️ Local Setup

1. **Clone Repo**
   ```bash
   git clone https://github.com/your-username/gos-report.git
   cd gos-report
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download Mistral GGUF model**
   Place `mistral-7b-instruct-v0.1.Q4_K_M.gguf` in root directory.

5. **Set Environment Variables**
   Create a `.env` file:
   ```env
   PORT=5000
   DB_NAME=postgres
   DB_USER=postgres
   DB_PASS=your_password
   DB_HOST=localhost
   EMAIL_USER=your_email@gmail.com
   EMAIL_PASS=your_app_password
   ```

6. **Run Flask App**
   ```bash
   python app.py
   ```

---

## 🛰️ Deploy on Railway

1. Push your code to GitHub
2. Go to [https://railway.app](https://railway.app)
3. Click **New Project → Deploy from GitHub**
4. Set the environment variables in the Railway dashboard
5. Deploy 🚀

---

## 🧪 Example Use Case

- Upload: `NPTEL Circular.pdf`
- Summary Generated: “This circular is about NPTEL course enrollment for Jan-Apr 2025...”
- Department Matched: `CSE`
- Email sent to all students in CSE department with the PDF + Summary

---

## 🔐 Security Notes

- Your `.env` file should **never** be committed to GitHub.
- Use **App Passwords** for Gmail instead of your actual account password.

---

## 🙌 Contributions

Pull requests are welcome! For major changes, open an issue first to discuss what you'd like to change.

---

## 📜 License

This project is for educational and non-commercial use. Please respect institutional and student data privacy.
