# 🚀 PATLens – Placement Manager

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python&logoColor=white)
![Gmail API](https://img.shields.io/badge/Gmail%20API-Google-red?logo=gmail&logoColor=white)
![Google Sheets API](https://img.shields.io/badge/Google%20Sheets%20API-Google-green?logo=google-sheets&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-LLM-black?logo=ollama&logoColor=white)
![Automation](https://img.shields.io/badge/Automation-Enabled-brightgreen)
![Status](https://img.shields.io/badge/Project-Active-success)

**PATLens** is an AI-powered automation system that reads campus placement emails from a college Gmail account, extracts structured placement information using a Large Language Model (LLM), and maintains an up-to-date Google Sheets tracker of all placement opportunities.

---

## 📌 Problem Statement

Campus placement emails are unstructured, inconsistent, and human-written. Traditional regex-based extraction fails due to varying formats, terminology, and human errors.

---

## 💡 Solution

PATLens combines:
- Gmail API for email ingestion  
- LLM-based semantic extraction (Ollama – Mistral)  
- Deterministic post-processing & sanitization  
- Append-only persistence to Google Sheets  

---

## ✨ Key Features

- 📩 Automated Gmail inbox scanning
- 🤖 LLM-based extraction of placement details
- 📊 Auto-updated Google Sheets tracker
- 📅 Mail received date & time extraction
- 🔁 Incremental updates (no data overwrite)
- ⚙️ Automation-ready (manual or scheduled)

---

## 🏗️ Project Structure

```
PATLens - Placement Manager
│
├── main.py
├── config/
│   └── config.py
├── utils/
│   ├── ai_extractor.py
│   ├── email_utils.py
│   ├── filters.py
│   ├── parsing_utils.py
│   ├── sheets_utils.py
│   └── testing.py
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 🔄 Execution Flow

Gmail Inbox → Mail Filtering → LLM Extraction → Data Cleaning → Google Sheets

---

## 📊 Google Sheets Columns

1. Sr. No  
2. Company Name  
3. Category  
4. Eligible Branches  
5. 10th %  
6. 12th %  
7. CGPA  
8. CTC  
9. Stipend  
10. Last Date  
11. Application Source  
12. Application Status  
13. Registration Links  
14. Mail Date  
15. Mail Time  

---

## 🤖 LLM Engine

- **Model**: Mistral via Ollama
- Handles inconsistent phrasing & real-world variability better than regex

---

## 🔐 Security

Sensitive files excluded via `.gitignore`:
- `.env`
- OAuth credentials & tokens
- `venv/`

---

## ⚙️ Setup

```bash
git clone https://github.com/HarshK0103/PATLens---Placement-Manager.git
cd PATLens---Placement-Manager
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
ollama pull mistral
ollama serve
python main.py
```

---

## 🔁 Automation

Can be scheduled every 6 hours using:
- Windows Task Scheduler
- Cron (Linux/macOS)

---

## 🚀 Future Scope

- Date-based Gmail queries
- Duplicate detection
- Eligibility matching
- Analytics dashboard
- Notifications

---

## 👤 Author

**Harsh Karekar**  
B.Tech – Electronics & Communication Engineering  
Aspiring Data Scientist / AI/ML Engineer
 
📫 [LinkedIn](https://www.linkedin.com/in/harsh-karekar-01h6910a04/) | 💻 [GitHub](https://github.com/HarshK0103)
