# Launch script for Streamlit Legal Document Summarization App
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Legal Document Summarization: Agentic Workflow System" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "[!] Note: .env file not found. Copying .env.example to .env..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "[*] Created .env. Please update GEMINI_API_KEY if needed." -ForegroundColor Green
}

# Run Streamlit
streamlit run app.py
