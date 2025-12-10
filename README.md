# Digital Loan Officer
**Agentic AI-Based Loan Evaluation Prototype**  
*EY Techathon 6.0 — Round 2 Submission*

A conversational, agent-based prototype that simulates an end-to-end personal loan evaluation workflow used by financial institutions.  
Built for concept validation, modularity, clarity, and explainability.

---

## 📌 Executive Overview
The **Digital Loan Officer** demonstrates how agentic AI architecture can streamline loan origination by automating customer interaction, KYC collection, credit evaluation, and sanction letter generation.

The prototype focuses on:
- Real-time user interaction  
- Explainable rule-based underwriting  
- Modular multi-agent architecture  
- Instant credit decisioning  

> **Note:** This system is a demo and not intended for production banking use.

---

## 🎯 Business Problem
Traditional consumer loan processing is often:
- Manual and time-intensive  
- Fragmented across teams  
- Opaque and non-interactive  

This results in slow turnaround, poor user experience, and limited transparency.

---

## ✅ Proposed Solution
The Digital Loan Officer solves these problems through:
- A **chat-first loan application interface**
- **Agentic AI** handling sales → verification → underwriting → sanctioning
- **Explainable rule-based credit evaluation**
- **Instant approval or rejection**, with reasoning
- **Automated sanction letter PDF generation**

---

## 🧠 Agentic Architecture

### Master–Worker Agent Model

#### 🔹 Master Agent
- Controls workflow and conversation state  
- Calls worker agents in the correct sequence  

#### 🔹 Sales Agent
- Captures loan intent (amount, tenure, purpose)  
- Computes EMI using standard formulas  
- Supports negotiation (e.g., adjust tenure to lower EMI)  

#### 🔹 Verification Agent
- Collects basic KYC  
- Accepts salary slip upload  
- Extracts income via mock OCR  

#### 🔹 Underwriting Agent
Applies explainable rules including:
- Minimum monthly income  
- Derived credit score (demo logic)  
- EMI-to-income ratio (DTI)  
- Maximum loan-to-income multiple  

Outputs approval/rejection + clear explanation.

#### 🔹 Sanction Agent
- Generates a downloadable **PDF sanction letter**
- Includes approved loan amount, EMI, tenure, and terms

---

## 🔄 End-to-End User Flow
1. User starts chat  
2. Sales agent gathers loan intent  
3. EMI is calculated and renegotiated as needed  
4. User confirms loan  
5. User uploads salary slip  
6. Underwriting evaluates eligibility  
7.  
   - **Approved → Sanction letter generated**  
   - **Rejected → Reason + suggested alternatives**

---

## 🛠️ Technology Stack

| Layer | Technology |
|-------|------------|
| Backend | Python, Flask |
| Frontend | HTML, CSS, JavaScript |
| Architecture | Agentic Design Pattern |
| Business Logic | Rule-based Underwriting |
| PDF Generation | ReportLab |
| OCR (Mock) | PyPDF2 |

---

## 📂 Project Structure
```
ey-loan-officer/
├── app.py
├── agents/
│   ├── master_agent.py
│   ├── sales_agent.py
│   ├── verification_agent.py
│   ├── underwriting_agent.py
│   └── sanction_agent.py
├── services/
│   ├── credit_rules.py
│   ├── pdf_generator.py
│   └── ocr_stub.py
├── templates/
│   └── index.html
├── static/
│   ├── css/style.css
│   └── js/chat.js
├── data/
│   └── sample_salary_slip.pdf
├── requirements.txt
└── README.md
```

---

## ⚙️ Installation & Setup

### 1️⃣ Install dependencies
```bash
python -m pip install -r requirements.txt
```

### 2️⃣ Run the application
```bash
python app.py
```

### 3️⃣ Open in browser
```
http://127.0.0.1:5000
```

---

## 🧪 Recommended Demo Script
```
hi
(Your Full Name)
I need a personal loan of 300000
EMI too high
make it 36 months
ok
```

Then upload any PDF as a salary slip → eligibility is evaluated.

---

## 📄 Sanction Letter Output
If approved, the generated PDF includes:
- Customer name  
- Loan amount  
- Tenure  
- Interest rate  
- EMI  
- Terms & conditions  

Generated using ReportLab.

---

## 🔍 Credit Decision Logic (Explainable)
- **Minimum monthly income:** ₹30,000  
- **Credit score:** Derived from income (demo logic)  
- **Maximum EMI:** 40% of monthly income  
- **Maximum loan amount:** 5× annual income  

Rejected cases include clear explanations and suggestions.

---

## 🚀 Deployment Guide
Compatible platforms:
- **Render** (recommended)
- **Replit**
- **Heroku** (ephemeral filesystem caveats)

Deployment checklist:
- Add environment variables  
- Replace stub OCR in real deployments  
- Add secure storage for PDFs  

---

## 🔐 Scope & Disclaimer
- Salary parsing simulated (not real OCR)  
- No real customer or financial data used  
- Not production-ready  
- Intended solely for hackathon/demo purposes  

---

## 👥 Contributors

### Abir Halder
- **GitHub:** [@abirhalder2004](https://github.com/abirhalder2004)
- **LinkedIn:** [Abir Halder](https://www.linkedin.com/in/abir-halder-280b73258/)

### Prasun Nandi
- **GitHub:** [@Prasunnandi](https://github.com/Prasunnandi)
- **LinkedIn:** [Prasun Nandi](https://www.linkedin.com/in/prasun-nandi-07b9841a9/)
