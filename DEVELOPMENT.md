Development & Best Practices

1. Environment Setup

PRTG Template Studio uses a Python backend and a React frontend embedded in a single HTML file to simplify Windows deployment.

# Setup Venv
python -m venv venv
.\venv\Scripts\activate

# Install Deps
pip install -r requirements.txt
pip install pytest flake8 black


2. Design Guidelines (UI)

We strictly adhere to a Modern Dark Mode design system.

Palette: Tailwind's Zinc colors.

Backgrounds: bg-zinc-950 (Main), bg-zinc-900 (Cards/Sidebar).

Borders: border-zinc-800.

Text: text-zinc-100 (Primary), text-zinc-400 (Secondary).

Accents: blue-600 for primary actions.

Typography: Sans-serif (Inter or system default).

Spacing: Use ample padding (p-4, p-6) to avoid clutter.

3. Testing & Linting

Backend

Run pytest to verify API endpoints and XML validation logic.

pytest


Git Workflow

Since the application itself performs Git operations on the server:

Do not develop inside the live PRTG directory.

Use a mock directory or tempfile in your tests (as seen in tests/conftest.py).

4. CI/CD

See .github/workflows/ci.yml for the automated testing pipeline.