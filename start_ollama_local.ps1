$env:OLLAMA_MODELS = "C:\Users\ai1\Desktop\chatbot\models"
$env:OLLAMA_HOST = "127.0.0.1:11436"
$env:HTTP_PROXY = ""
$env:HTTPS_PROXY = ""
$env:ALL_PROXY = ""

Write-Host "Starting project-local Ollama on $env:OLLAMA_HOST"
Write-Host "Models directory: $env:OLLAMA_MODELS"

ollama serve
