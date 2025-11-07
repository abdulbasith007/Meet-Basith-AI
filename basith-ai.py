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
import gradio.themes.base
from gradio.themes.utils import colors, fonts, sizes

# Custom theme
basith_theme = gr.themes.Soft(
    primary_hue=colors.blue,
    secondary_hue=colors.sky,
    font=fonts.GoogleFont("Inter"),
).set(
    body_background_fill="linear-gradient(to right, #f8fafc, #eef2ff)",
    button_primary_background_fill="linear-gradient(90deg, #2563eb, #3b82f6)",
    button_primary_background_fill_hover="linear-gradient(90deg, #1d4ed8, #2563eb)",
    button_primary_text_color="white",
)

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
            # Graceful fallback: just print to logs if SMTP is not configured
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

# JSON schema for tools (function-calling API)
send_contact_email_json = {
    "name": "send_contact_email",
    "description": "Send the visitor's contact information to the owner via email once they share it.",
    "parameters": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Full name of the visitor"},
            "email": {"type": "string", "description": "Email address of the visitor"},
            "phone": {"type": "string", "description": "Phone number if provided"},
            "company": {"type": "string", "description": "Company or organization if provided"},
            "notes": {"type": "string", "description": "Any extra notes or context from the chat"}
        },
        "required": ["email"],
        "additionalProperties": False
    }
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Use this when the assistant could not answer a user question. It will be logged for follow-up.",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {"type": "string", "description": "The question the assistant couldn't answer"}
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

# ---------------------
# Tool-call handler
# ---------------------
def handle_tool_calls(tool_calls: List[Any]) -> List[Dict[str,Any]]:
    results = []
    for call in tool_calls:
        fn = call.function
        name = fn.name
        args = json.loads(fn.arguments or "{}")
        if name == "send_contact_email":
            res = send_contact_email(**args)
        elif name == "record_unknown_question":
            res = record_unknown_question(**args)
        else:
            res = {"error": f"Unknown tool {name}"}
        results.append({"role": "tool", "tool_call_id": call.id, "name": name, "content": json.dumps(res)})
    return results

# ---------------------
# Chat with tools + evaluator loop
# ---------------------
def generate_reply_with_tools(system_prompt: str, message: str, history: List[Dict[str,str]]) -> str:
    # Tool loop: allow model to call tools repeatedly until it produces a final message
    messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": message}]
    while True:
        response = openai.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=TOOLS)
        finish_reason = response.choices[0].finish_reason
        if finish_reason == "tool_calls":
            model_msg = response.choices[0].message
            tool_calls = model_msg.tool_calls or []
            tool_results = handle_tool_calls(tool_calls)
            messages.append(model_msg)
            messages.extend(tool_results)
            # continue loop
        else:
            return response.choices[0].message.content

def chat(message: str, history: List[Dict[str,str]]):
    # 1) Draft with tools
    draft = generate_reply_with_tools(BASE_SYSTEM_PROMPT, message, history)

    # 2) Evaluate; rerun until acceptable (with max safety bound)
    max_iters = 5  # prevent infinite loops
    iters = 0
    reply = draft
    while True:
        iters += 1
        try:
            evaluation = evaluate_reply(reply, message, history)
            if evaluation.is_acceptable:
                if iters > 1:
                    print(f"[Evaluator] Accepted after {iters} iterations.")
                break
            else:
                print(f"[Evaluator] Not acceptable: {evaluation.feedback}")
                reply = rerun_with_feedback(reply, message, history, evaluation.feedback)
        except Exception as e:
            # If evaluator fails for any reason, return the current reply
            print(f"[Evaluator] Error: {e}. Returning current reply.")
            break
        if iters >= max_iters:
            print("[Evaluator] Reached max iterations; returning best-effort reply.")
            break

    return reply

# ---------------------
# Gradio App (Hugging Face entry point)
# ---------------------
def make_demo():
    with gr.Blocks(theme=basith_theme, title="Basith-AI | Interactive Chatbot") as demo:
        gr.HTML("""
        <div style="text-align:center; padding: 1.5em; border-radius: 15px; background: #f1f5f9;">
            <h1 style="margin-top:10px;">🤖 Basith-AI</h1>
            <p style="font-size:16px; color:#475569;">
                Hi! I'm Basith Abdul’s virtual twin. Feel free to ask me about my work experience, personal projects, or any other professional topics.
                <br>I’ll respond just like Basith would, you might not even notice any difference. 😉
            </p>
        </div>
        """)

        chat_ui = gr.ChatInterface(
            fn=chat,
            type="messages",
            chatbot=gr.Chatbot(
                type="messages",
                show_copy_button=True,
                show_label=False,
                height=600
            ),
            examples=[
                ["Tell me about your experience at Amazon."],
                ["What projects have you done with AI or LLMs?"],
                ["How can I contact you about employment opportunities?"]
            ],
            title="Talk with Basith-AI",
            # description="A conversational mirror of Basith Abdul — product-minded, AI-driven, and always curious.",
        )

    return demo

if __name__ == "__main__":
    demo = make_demo()
    # On Spaces, huggingface sets PORT; for local running, defaults used by Gradio
    demo.launch()
