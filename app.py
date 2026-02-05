import os
import sys
import subprocess
import configparser
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_httpauth import HTTPBasicAuth
from waitress import serve

# --- Configuration ---
CONFIG_FILE = 'config.ini'

def load_config():
    config = configparser.ConfigParser()
    if not os.path.exists(CONFIG_FILE):
        print(f"[{CONFIG_FILE}] not found. Generating default...")
        config['Server'] = {'Host': '0.0.0.0', 'Port': '8080'}
        config['PRTG'] = {'TemplatePath': './devicetemplates'}
        config['Security'] = {'Username': 'admin', 'Password': 'changeme'}
        with open(CONFIG_FILE, 'w') as f:
            config.write(f)
    else:
        config.read(CONFIG_FILE)
    return config

config = load_config()

HOST = config.get('Server', 'Host', fallback='0.0.0.0')
PORT = config.getint('Server', 'Port', fallback=8080)
TEMPLATE_PATH = config.get('PRTG', 'TemplatePath', fallback='./devicetemplates')
AUTH_USER = config.get('Security', 'Username', fallback='admin')
AUTH_PASS = config.get('Security', 'Password', fallback='changeme')

# --- Helper Functions ---

def ensure_directory_structure():
    if not os.path.exists(TEMPLATE_PATH):
        try:
            os.makedirs(TEMPLATE_PATH)
            print(f"Created template directory: {TEMPLATE_PATH}")
        except OSError as e:
            print(f"Error creating directory {TEMPLATE_PATH}: {e}")
            sys.exit(1)

def ensure_git_repo():
    git_dir = os.path.join(TEMPLATE_PATH, '.git')
    if not os.path.exists(git_dir):
        print("Initializing Git repository...")
        try:
            subprocess.run(['git', 'init'], cwd=TEMPLATE_PATH, check=True)
            # Configure git locally for this repo if needed, but assuming user git config exists or we set local
            subprocess.run(['git', 'config', 'user.email', 'prtg-studio@local'], cwd=TEMPLATE_PATH, check=False)
            subprocess.run(['git', 'config', 'user.name', 'PRTG Studio'], cwd=TEMPLATE_PATH, check=False)
        except subprocess.CalledProcessError as e:
            print(f"Failed to init git repo: {e}")

def git_commit(filename, message):
    try:
        subprocess.run(['git', 'add', filename], cwd=TEMPLATE_PATH, check=True)
        subprocess.run(['git', 'commit', '-S', '-m', message], cwd=TEMPLATE_PATH, check=True)
        return True, "Saved and committed."
    except subprocess.CalledProcessError as e:
        return False, f"Git error: {e}"

# --- Flask App ---
app = Flask(__name__)
auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username, password):
    if username == AUTH_USER and password == AUTH_PASS:
        return username
    return None

# --- Routes ---

@app.route('/')
@auth.login_required
def index():
    return render_template('index.html')

@app.route('/api/templates', methods=['GET'])
@auth.login_required
def list_templates():
    files = []
    if os.path.exists(TEMPLATE_PATH):
        for f in os.listdir(TEMPLATE_PATH):
            if f.endswith('.odt') and os.path.isfile(os.path.join(TEMPLATE_PATH, f)):
                files.append(f)
    return jsonify(files)

@app.route('/api/template/<filename>', methods=['GET'])
@auth.login_required
def get_template(filename):
    # Security check: prevent directory traversal
    if '..' in filename or filename.startswith('/'):
        return jsonify({"error": "Invalid filename"}), 400
    
    filepath = os.path.join(TEMPLATE_PATH, filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    return jsonify({"filename": filename, "content": content})

@app.route('/api/template/<filename>', methods=['POST'])
@auth.login_required
def save_template(filename):
    if '..' in filename or filename.startswith('/'):
        return jsonify({"error": "Invalid filename"}), 400

    data = request.json
    content = data.get('content')
    if content is None:
        return jsonify({"error": "No content provided"}), 400

    # Basic XML validation could go here, but relying on frontend for now or simple check
    if not content.strip().startswith('<'): # Very basic check
         pass # Allow saving even if broken XML? Maybe warning. For now let it pass.

    filepath = os.path.join(TEMPLATE_PATH, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        success, msg = git_commit(filename, f"Update {filename} via PRTG Studio")
        if success:
            return jsonify({"message": msg})
        else:
            return jsonify({"warning": "Saved but git commit failed", "details": msg}), 200 # Return 200 as file is saved
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Main ---
if __name__ == "__main__":
    ensure_directory_structure()
    ensure_git_repo()
    print(f"Starting server on http://{HOST}:{PORT}")
    serve(app, host=HOST, port=PORT)
