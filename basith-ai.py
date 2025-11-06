#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Author: Basith Abdul
LinkedIn-style chatbot with evaluator loop + contact-capture email tool.

Environment variables (set in Spaces Secrets or .env):
- OPENAI_API_KEY: for OpenAI responses (primary model)
- SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, FROM_EMAIL: for sending emails
- TO_EMAIL (optional): default receiver override; if not set, uses basithabdul2608@gmail.com

Files (optional):
- me/linkedin.pdf : LinkedIn export
- me/summary.txt  : Summary profile text
"""
import os
import json
import smtplib
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
    except Exception as e:
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
