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
BASE_SYSTEM_PROMPT = f"""You are acting as {name}. ...
## LinkedIn Profile:
{linkedin if linkedin else "[linkedin.pdf not found]"}
"""

# ---------------------
# Evaluator
# ---------------------
class Evaluation(BaseModel):
    is_acceptable: bool
    feedback: str

def build_evaluator_system_prompt() -> str:
    p = f"""You are an evaluator that decides whether a response to a question is acceptable.
You are provided with a conversation between a User and an Agent. Decide whether the Agent's latest response is acceptable quality.
The Agent is playing the role of {name} on their website and should be professional, helpful, and aligned with the context above.
Evaluate the latest agent reply for: factuality (relative to provided context or honest uncertainty), tone (polite, concise, professional), clarity, avoidance of hallucinations, and whether it gently encourages contact (without being pushy or repetitive).

Context you may reference:
## Summary
{summary if summary else "[summary.txt not found]"}

## LinkedIn
{linkedin if linkedin else "[linkedin.pdf not found]"}

Return a JSON with fields: is_acceptable (boolean) and feedback (string).
"""
    return p

def evaluator_user_prompt(reply: str, message: str, history: List[Dict[str,str]]) -> str:
    return f"""Conversation:\n{history}\n\nUser message:\n{message}\n\nAgent reply:\n{reply}\n\nEvaluate the reply and respond in the specified JSON schema."""

def evaluate_reply(reply: str, message: str, history: List[Dict[str,str]]) -> Evaluation:
    messages = [
        {"role": "system", "content": build_evaluator_system_prompt()},
        {"role": "user", "content": evaluator_user_prompt(reply, message, history)},
    ]
    resp = openai.chat.completions.create(model="gpt-4o-mini", messages=messages, response_format=Evaluation)
    return resp.choices[0].message.parsed

def rerun_with_feedback(prev_reply: str, message: str, history: List[Dict[str,str]], feedback_text: str) -> str:
    updated_system_prompt = BASE_SYSTEM_PROMPT + "\n\n" + \
        "## Previous answer was rejected by quality control.\n" + \
        f"### Your attempted answer:\n{prev_reply}\n\n" + \
        f"### Reason to improve:\n{feedback_text}\n\n" + \
        "Please produce an improved response that addresses the feedback faithfully and concisely."
    messages = [{"role": "system", "content": updated_system_prompt}] + history + [{"role": "user", "content": message}]
    resp = openai.chat.completions.create(model="gpt-4o-mini", messages=messages)
    return resp.choices[0].message.content
