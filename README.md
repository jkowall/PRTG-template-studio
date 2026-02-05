# PRTG Template Studio

A modern, dark-mode web application for managing PRTG Network Monitor Device Templates (`.odt` files) directly on your Core Server.

## Features

- **Multi-Template Support**: Manage Device Templates (`.odt`), SNMP Libraries (`.oidlib`, `.xml`), and Lookups (`.ovl`, `.xml`) from a single interface.
- **Visual Preview**: View the XML structure of your templates in a readable, nested format.
- **Git Versioning**: Automatically commits changes to a local Git repository on every save.
- **Dark Mode**: A premium, "shadcn/ui"-inspired dark theme using Tailwind CSS.
- **Secure**: Protected by HTTP Basic Authentication.

## Quick Start Configuration

### 1. Set up Environment

Run the following commands in PowerShell to create a virtual environment and install dependencies:

```powershell
# Create Virtual Environment
python -m venv venv

# Activate Virtual Environment
.\venv\Scripts\Activate

# Install Dependencies
pip install -r requirements.txt
```

### 2. Configure Settings (Optional)

The first run will generate a `config.ini` file. You can pre-configure it or edit it later:

```ini
[Server]
Host = 0.0.0.0
Port = 8080

[PRTG]
# Update this to your real PRTG templates directory
TemplatePath = ./devicetemplates

[Security]
# CHANGE THESE FOR PRODUCTION
Username = admin
Password = changeme
```

### 3. Run Application

```powershell
python app.py

# For Development (Auto-Reload)
python app.py --reload
```

Access the application at: [http://localhost:8080](http://localhost:8080)

## Development

### Running Tests

```powershell
# Install test dependencies (if not in requirements.txt)
pip install pytest

# Run tests
pytest
```

## License

Private / Internal Use