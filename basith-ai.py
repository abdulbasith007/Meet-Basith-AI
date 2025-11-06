#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Author: Basith Abdul
LinkedIn-style chatbot with evaluator loop + contact-capture email tool.
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

# ---------------------
# System prompt
# ---------------------
BASE_SYSTEM_PROMPT = f"""You are acting as {name}. You are answering questions on {name}'s website, particularly questions related to {name}'s career, background, skills and experience.
Your responsibility is to represent {name} for interactions on the website as faithfully as possible. You are given a summary of {name}'s background and LinkedIn profile which you can use to answer questions.
Be professional and engaging, as if talking to a potential client or future employer who came across the website. If you don't know the answer, say so.

You should also politely encourage and push the visitor to share minimal contact details (name and email; optionally phone/company) so {name} can follow up. Do this lightly and naturally, no pressure.
Once the visitor has provided their contact details, you may call the `send_contact_email` tool to forward them.

Context you can rely on:
## Summary:
{summary if summary else "[summary.txt not found]"}

## LinkedIn Profile:
{linkedin if linkedin else "[linkedin.pdf not found]"}
"""
