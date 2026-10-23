@echo off
echo ==========================================================
echo  Legal Document Summarization: Agentic Workflow System
echo ==========================================================

if not exist .env (
    echo [*] Copying .env.example to .env...
    copy .env.example .env
)

streamlit run app.py
pause
