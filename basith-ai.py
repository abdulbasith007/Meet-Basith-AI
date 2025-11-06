#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Author: Basith Abdul
LinkedIn-style chatbot with evaluator loop + contact-capture email tool.
"""
import os, json, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate
from typing import List, Dict, Any
from dotenv import load_dotenv
from pydantic import BaseModel
from pypdf import PdfReader
import gradio as gr
from openai import OpenAI

# ---------------------
# Setup
# ---------------------
load_dotenv(override=True)
openai = OpenAI()

# ---------------------
# Context loading
# ---------------------
def read_linkedin_text() -> str:
    linkedin_text = ""
    try:
        reader = PdfReader("me/linkedin.pdf")
        for page in reader.pages:
            text = page.extract_text()
            if text:
                linkedin_text += text
    except Exception:
        linkedin_text = ""
    return linkedin_text

def read_summary_text() -> str:
    try:
        with open("me/summary.txt", "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""

name = "Basith Abdul"
linkedin = read_linkedin_text()
summary = read_summary_text()

# ---------------------
# System prompt
# ---------------------
BASE_SYSTEM_PROMPT = f"""You are acting as {name}. ...
{linkedin if linkedin else "[linkedin.pdf not found]"}
"""

# ---------------------
# Evaluator
# ---------------------
class Evaluation(BaseModel):
    is_acceptable: bool
    feedback: str
# (Evaluator methods omitted for brevity, same as before)

# ---------------------
# Email tool
# ---------------------
TO_EMAIL_DEFAULT = "basithabdul2608@gmail.com"

def send_email_smtp(subject: str, body: str, to_addr: str = None) -> Dict[str,Any]:
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USERNAME")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("FROM_EMAIL") or smtp_user or "no-reply@example.com"
    to_email = to_addr or os.getenv("TO_EMAIL") or TO_EMAIL_DEFAULT

    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Date"] = formatdate(localtime=True)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        if not smtp_server or not smtp_user or not smtp_pass:
            print("[Email Tool] SMTP not configured. Would have sent:\n", msg.as_string())
            return {"sent": False, "reason": "SMTP not configured", "preview": msg.as_string()}

        with smtplib.SMTP(smtp_server, smtp_port, timeout=20) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(from_email, [to_email], msg.as_string())
        return {"sent": True}
    except Exception as e:
        return {"sent": False, "error": str(e)}

def send_contact_email(name: str = "", email: str = "", phone: str = "", company: str = "", notes: str = "") -> Dict[str,Any]:
    subject = f"[Website Lead] {name or 'Prospect'}"
    body = f"""New contact captured from the chatbot:

    Name: {name or '[not provided]'}
    Email: {email or '[not provided]'}
    Phone: {phone or '[not provided]'}
    Company: {company or '[not provided]'}
    Notes: {notes or '[none]'}
    """
    return send_email_smtp(subject, body)

send_contact_email_json = {
    "name": "send_contact_email",
    "description": "Send the visitor's contact information to the owner via email once they share it.",
    "parameters": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "email": {"type": "string"},
            "phone": {"type": "string"},
            "company": {"type": "string"},
            "notes": {"type": "string"}
        },
        "required": ["email"],
        "additionalProperties": False
    }
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Use this when the assistant could not answer a user question.",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {"type": "string"}
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

def record_unknown_question(question: str) -> Dict[str,Any]:
    print(f"[Unknown Question] {question}")
    return {"recorded": "ok"}

TOOLS = [{"type": "function", "function": send_contact_email_json},
         {"type": "function", "function": record_unknown_question_json}]
