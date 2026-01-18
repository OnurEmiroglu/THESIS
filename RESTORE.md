# Restore after format

Repo: https://github.com/OnurEmiroglu/THESIS.git

## 1) Install
- Git
- VS Code
- Python
- Pandoc

## 2) Clone
git clone https://github.com/OnurEmiroglu/THESIS.git
cd THESIS

## 3) VS Code extensions
Get-Content .\vscode-extensions.txt | ForEach-Object { code --install-extension  }

## 4) Python env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

## 5) Build
VS Code: Ctrl+Shift+P -> Run Task -> Build thesis (DOCX)
