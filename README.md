# Meet-Basith-AI

**Meet-Basith-AI** is a LinkedIn-style chatbot designed to act as a professional digital twin of **Basith Abdul** — simulating intelligent, context-aware conversations about his career, technical projects, and background.  
Built with **Python**, **Gradio**, and **OpenAI GPT-4o-mini**, the chatbot includes an evaluator loop for quality assurance and a built-in contact-capture email tool.

---

## Features

### AI-Powered Personal Assistant
- Uses **OpenAI GPT-4o-mini** to generate responses that mirror Basith’s tone, style, and professional background.
- Reads data directly from:
  - `me/linkedin.pdf` → Basith’s LinkedIn export  
  - `me/summary.txt` → concise professional summary

### Response Evaluator Loop
- Every reply is automatically **evaluated for quality** (tone, clarity, factuality).
- If rejected, the chatbot **auto-improves and re-evaluates** up to 5 times before finalizing.

### Contact Capture via Email
- Encourages users to share minimal contact info (name, email, optional phone/company).  
- Sends leads securely via **SMTP**, configurable through environment variables.

### Tool Invocation
Two JSON-schema tools enhance functionality:
1. `send_contact_email` – forwards captured leads  
2. `record_unknown_question` – logs unanswered or uncertain questions  

### Modern UI
- Built with **Gradio Blocks + ChatInterface**  
- Custom gradient theme using `gr.themes.Soft`  
- Title: **Basith-AI | Interactive Chatbot**

---

## Tech Stack

| Component         | Technology |
|------------------|------------|
| Core Language     | Python 3.10 + |
| Framework         | [Gradio](https://gradio.app) |
| LLM API           | [OpenAI GPT-4o-mini](https://platform.openai.com/docs/models/gpt-4o) |
| Evaluation Model  | GPT-4o-mini (JSON structured output via Pydantic) |
| PDF Parsing       | [pypdf](https://pypi.org/project/pypdf/) |
| Env Management    | [python-dotenv](https://pypi.org/project/python-dotenv/) |
| Email Transport   | `smtplib` (TLS) |
| UI Styling        | `gradio.themes.Soft` with custom palette |

---

## Setup & Installation

## 1. Clone the Repository
```bash
git clone https://github.com/abdulbasith007/Meet-Basith-AI.git
cd Meet-Basith-AI
```

## 2. Create a Virtual Environment

### Using uv (recommended):
```
    uv venv
    source .venv/bin/activate        # Linux / macOS
    .venv\Scripts\activate           # Windows PowerShell
```

### Or using standard Python:
```
    python -m venv venv
    source venv/bin/activate
```
---

## 3. Install Dependencies
```
    uv pip install -r requirements.txt
    # (Or pip install -r requirements.txt if not using uv.)
```
---

## 4. Configure Environment Variables

Create a `.env` file in the project root. Example:
```
    # ==== OpenAI API ====
    OPENAI_API_KEY=your_openai_api_key_here

    # ==== Email / SMTP Settings ====
    SMTP_SERVER=smtp.yourprovider.com
    SMTP_PORT=587
    SMTP_USERNAME=your_email@example.com
    SMTP_PASSWORD=your_email_password
    FROM_EMAIL=your_email@example.com
    TO_EMAIL=target_email@gmail.com    # optional override

    # ==== Optional Debug ====
    # DEBUG_EMAIL_MODE=True
```

**Note:** If SMTP is not configured, the chatbot logs contact details to the console instead of sending an email — useful for local testing.

---

## 5. Add Optional Profile Files

For better responses, include personal context files under `me/`:
```
    me/
     ├── linkedin.pdf     # optional LinkedIn export
     └── summary.txt      # concise professional summary or bio
```
---

## 6. Run the Application
```
    uv run python basith-ai.py
```
Open your browser at:  
 [http://127.0.0.1:7860](http://127.0.0.1:7860)

### Developer Mode (Auto Reload):
```
    uv run --reload python basith-ai.py
```
### Deployment (Hugging Face):

- Push the repo to your **Hugging Face Space**.
- Add all `.env` variables in **Settings → Variables and Secrets**.
- Deploy — the app auto-starts on the public Space.

---

##  How It Works

- **Context Injection** – loads summary & LinkedIn profile into the system prompt.  
- **LLM + Tool Loop** – model answers questions or triggers functions (e.g., `send_contact_email`).  
- **Evaluator Loop** – validates responses for quality; re-runs until acceptable.  
- **Email Notifier** – sends captured contact data via SMTP.

---

## Example prompts:

- “Tell me about your experience at Amazon.”
- “What projects have you done with AI or LLMs?”
- “How can I contact you for a collaboration?”

---

## Folder Structure
```
    Meet-Basith-AI/
    ├── basith-ai.py
    ├── requirements.txt
    ├── .env.example
    ├── me/
    │   ├── linkedin.pdf
    │   └── summary.txt
    └── README.md
```
---

## Troubleshooting Tips

- **OpenAI error 401** → verify `OPENAI_API_KEY`.  
- **Email not sending** → check SMTP credentials or enable “less secure apps”.  
- **App not loading** → ensure `Gradio ≥ 4.0` and `Python ≥ 3.10`.  
- **Evaluator fails** → gracefully fallback to last valid reply.

---

## Contributing

Contributions are welcome! Submit issues or pull requests.

