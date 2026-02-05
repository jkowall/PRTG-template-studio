"""
PRTG Template Studio - Main Application
This module provides the backend API and server for the PRTG Template Studio.
It handles file management, git versioning, and serving the frontend.
"""
import os
import sys
import shutil
import subprocess
import configparser
from flask import Flask, request, jsonify, render_template
from flask_httpauth import HTTPBasicAuth
from waitress import serve

# --- Configuration ---
__version__ = "1.1.0"
CONFIG_FILE = 'config.ini'

def load_config():
    """Load configuration from file or generate default."""
    cfg = configparser.ConfigParser()
    if not os.path.exists(CONFIG_FILE):
        print(f"[{CONFIG_FILE}] not found. ", end="")
        if os.path.exists('config.example.ini'):
            print("Generating from config.example.ini...")
            shutil.copy('config.example.ini', CONFIG_FILE)
            cfg.read(CONFIG_FILE)
        else:
            print("Generating default...")
            cfg['Server'] = {'Host': '0.0.0.0', 'Port': '8080'}
            cfg['PRTG'] = {
                'TemplatePath': r'C:\Program Files (x86)\PRTG Network Monitor\devicetemplates'
            }
            cfg['SNMP'] = {
                'LibraryPath': r'C:\Program Files (x86)\PRTG Network Monitor\snmplibs'
            }
            cfg['Lookups'] = {
                'LookupPath': r'C:\Program Files (x86)\PRTG Network Monitor\lookups'
            }
            cfg['Security'] = {'Username': 'admin', 'Password': 'changeme'}
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                cfg.write(f)
    else:
        cfg.read(CONFIG_FILE)
    return cfg

config = load_config()

HOST = config.get('Server', 'Host', fallback='0.0.0.0')
PORT = config.getint('Server', 'Port', fallback=8080)
AUTH_USER = config.get('Security', 'Username', fallback='admin')
AUTH_PASS = config.get('Security', 'Password', fallback='changeme')

# Allow configuring which types map to which paths and allowed extensions
DIRECTORIES = {
    'device': {
        'path': config.get('PRTG', 'TemplatePath', fallback='./devicetemplates'),
        'extensions': ('.odt',)
    },
    'snmp': {
        'path': config.get('SNMP', 'LibraryPath', fallback='./snmplibs'),
        'extensions': ('.oidlib', '.xml')
    },
    'lookup': {
        'path': config.get('Lookups', 'LookupPath', fallback='./lookups'),
        'extensions': ('.ovl', '.xml')
    }
}

# --- Helper Functions ---

def ensure_directory_structure():
    """Ensure that all configured directories exist."""
    for key, info in DIRECTORIES.items():
        path = info['path']
        if not os.path.exists(path):
            try:
                os.makedirs(path)
                print(f"Created {key} directory: {path}")
            except OSError as e:
                print(f"Error creating directory {path}: {e}")
                sys.exit(1)

def ensure_git_repo():
    """Ensure that git repositories are initialized in all directories."""
    for key, info in DIRECTORIES.items():
        path = info['path']
        git_dir = os.path.join(path, '.git')
        if not os.path.exists(git_dir):
            print(f"Initializing Git repository for {key}...")
            try:
                subprocess.run(['git', 'init'], cwd=path, check=True)
                # Configure git locally for this repo if needed
                subprocess.run(
                    ['git', 'config', 'user.email', 'prtg-studio@local'],
                    cwd=path, check=False
                )
                subprocess.run(
                    ['git', 'config', 'user.name', 'PRTG Studio'],
                    cwd=path, check=False
                )
            except subprocess.CalledProcessError as e:
                print(f"Failed to init git repo in {path}: {e}")

def git_commit(type_key, filename, message):
    """Commit a file to the git repository."""
    if type_key not in DIRECTORIES:
        return False, "Invalid type"
    path = DIRECTORIES[type_key]['path']
    try:
        subprocess.run(['git', 'add', filename], cwd=path, check=True)
        # Removed -S (GPG init) since not all environments have GPG config
        subprocess.run(['git', 'commit', '-m', message], cwd=path, check=True)
        return True, "Saved and committed."
    except subprocess.CalledProcessError as e:
        return False, f"Git error: {e}"

def git_history(type_key, filename):
    """Get the git history for a specific file."""
    if type_key not in DIRECTORIES:
        return []
    path = DIRECTORIES[type_key]['path']
    try:
        # Format: Hash|Author|Date|Message
        # %H: Commit hash, %an: Author name, %ad: Author date (iso-strict), %s: Subject
        cmd = [
            'git', 'log', '--pretty=format:%H|%an|%ad|%s',
            '--date=iso-strict', '-n', '20', filename
        ]
        # Use errors='replace' to handle potential non-utf8 commit messages
        result = subprocess.run(
            cmd, cwd=path, capture_output=True, text=True,
            check=True, encoding='utf-8', errors='replace'
        )

        history = []
        if result.stdout:
            for line in result.stdout.splitlines():
                parts = line.split('|', 3)
                if len(parts) == 4:
                    history.append({
                        'hash': parts[0],
                        'author': parts[1],
                        'date': parts[2],
                        'message': parts[3]
                    })
        return history
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Git History Error: {e}", file=sys.stderr)
        return []

def git_get_version(type_key, filename, commit_hash):
    """Retrieve a specific version of a file from git."""
    if type_key not in DIRECTORIES:
        return None
    path = DIRECTORIES[type_key]['path']
    try:
        # Standardize on forward slashes for git
        filename = filename.replace('\\', '/')
        target = f"{commit_hash}:{filename}"
        cmd = ['git', 'show', target]
        result = subprocess.run(
            cmd, cwd=path, capture_output=True, text=True,
            check=True, encoding='utf-8', errors='replace'
        )
        return result.stdout
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Git Version Error: {e}", file=sys.stderr)
        return None

def git_get_diff(type_key, filename, commit_hash):
    """Get the diff for a specific commit."""
    if type_key not in DIRECTORIES:
        return None
    path = DIRECTORIES[type_key]['path']
    try:
        # Standardize on forward slashes for git
        filename = filename.replace('\\', '/')
        # git show --format= -p <hash> -- <filename>
        # Add --text (treat as text), --no-textconv (skip filters), --no-ext-diff
        # (skip external tools)
        # to avoid "unsupported filetype" errors from system-wide .odt handlers
        cmd = [
            'git', 'show', '--format=', '-p', '--text',
            '--no-textconv', '--no-ext-diff', commit_hash, '--', filename
        ]
        result = subprocess.run(
            cmd, cwd=path, capture_output=True, text=True,
            check=True, encoding='utf-8', errors='replace'
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Git Diff Error: {e}", file=sys.stderr)
        print(f"Git Stderr: {e.stderr}", file=sys.stderr)
        return None
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Git Diff Error (General): {e}", file=sys.stderr)
        return None

# --- Flask App ---
app = Flask(__name__)
auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username, password):
    """Verify HTTP Basic Auth credentials."""
    if username == AUTH_USER and password == AUTH_PASS:
        return username
    return None

# --- Routes ---

@app.route('/')
@auth.login_required
def index():
    """Serve the index page."""
    return render_template('index.html')

@app.route('/api/templates', methods=['GET'])
@auth.login_required
def list_templates():
    """List all templates for a specific type."""
    type_key = request.args.get('type', 'device')
    if type_key not in DIRECTORIES:
        return jsonify({"error": "Invalid type"}), 400

    info = DIRECTORIES[type_key]
    path = info['path']
    exts = info['extensions']

    files = []
    if os.path.exists(path):
        # Walk recursively to find files, including those in 'custom' subfolder
        for root, dirs, filenames in os.walk(path):
            # Skip .git directory
            if '.git' in dirs:
                dirs.remove('.git')

            for f in filenames:
                if f.lower().endswith(exts):
                    # Store relative path from the base directory
                    full_path = os.path.join(root, f)
                    rel_path = os.path.relpath(full_path, path)
                    # Normalize to forward slashes for API consistency
                    rel_path = rel_path.replace(os.sep, '/')
                    files.append(rel_path)

    # Sort files for better UX
    files.sort()
    return jsonify(files)

@app.route('/api/template/<path:filename>', methods=['GET'])
@auth.login_required
def get_template(filename):
    """Get the content of a template file."""
    type_key = request.args.get('type', 'device')
    if type_key not in DIRECTORIES:
        return jsonify({"error": "Invalid type"}), 400

    # Security check: prevent directory traversal
    if '..' in filename or filename.startswith('/'):
        return jsonify({"error": "Invalid filename"}), 400

    path = DIRECTORIES[type_key]['path']
    filepath = os.path.join(path, filename)

    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        return jsonify({"error": "Binary or invalid encoding"}), 400

    return jsonify({"filename": filename, "content": content, "type": type_key})

@app.route('/api/template/<path:filename>', methods=['POST'])
@auth.login_required
def save_template(filename):
    """Save content to a template file and commit to git."""
    type_key = request.args.get('type', 'device')
    if type_key not in DIRECTORIES:
        return jsonify({"error": "Invalid type"}), 400

    if '..' in filename or filename.startswith('/'):
        return jsonify({"error": "Invalid filename"}), 400

    data = request.json
    content = data.get('content')
    if content is None:
        return jsonify({"error": "No content provided"}), 400

    # Basic XML validation could go here.
    # We might want looser validation for non-XML OIDLIBS if those exist,
    # but standards say .oidlib is mostly XML or JSON?
    # Actually PRTG OIDLIBs are XML. OVLs are XML. So XML check is still decent valid sanity check.
    if content.strip() and not content.strip().startswith('<') \
            and not content.strip().startswith('{'):
        pass # Allow saving

    path = DIRECTORIES[type_key]['path']
    filepath = os.path.join(path, filename)

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        success, msg = git_commit(type_key, filename, f"Update {filename} via PRTG Studio")
        if success:
            return jsonify({"message": msg})

        return jsonify({"warning": "Saved but git commit failed", "details": msg}), 200

    except Exception as e:  # pylint: disable=broad-exception-caught
        return jsonify({"error": str(e)}), 500

@app.route('/api/template/<path:filename>/history', methods=['GET'])
@auth.login_required
def get_template_history(filename):
    """Get the git history of a template file."""
    type_key = request.args.get('type', 'device')
    if type_key not in DIRECTORIES:
        return jsonify({"error": "Invalid type"}), 400

    if '..' in filename or filename.startswith('/'):
        return jsonify({"error": "Invalid filename"}), 400

    history = git_history(type_key, filename)
    return jsonify(history)

@app.route('/api/template/<path:filename>/version/<commit_hash>', methods=['GET'])
@auth.login_required
def get_template_version(filename, commit_hash):
    """Get a specific legacy version of a template file."""
    type_key = request.args.get('type', 'device')
    if type_key not in DIRECTORIES:
        return jsonify({"error": "Invalid type"}), 400

    if '..' in filename or filename.startswith('/'):
        return jsonify({"error": "Invalid filename"}), 400

    content = git_get_version(type_key, filename, commit_hash)
    if content is None:
        return jsonify({"error": "Version not found or git error"}), 404

    return jsonify({"content": content})

@app.route('/api/template/<path:filename>/diff/<commit_hash>', methods=['GET'])
@auth.login_required
def get_template_diff(filename, commit_hash):
    """Get the diff for a specific version."""
    type_key = request.args.get('type', 'device')
    if type_key not in DIRECTORIES:
        return jsonify({"error": "Invalid type"}), 400

    if '..' in filename or filename.startswith('/'):
        return jsonify({"error": "Invalid filename"}), 400

    diff = git_get_diff(type_key, filename, commit_hash)
    if diff is None:
        return jsonify({"error": "Diff not found or git error"}), 404

    return jsonify({"diff": diff})

# --- Main ---
def main():
    """Main entry point."""
    ensure_directory_structure()
    ensure_git_repo()
    print(f"Starting server on http://{HOST}:{PORT}")
    serve(app, host=HOST, port=PORT)

if __name__ == "__main__":
    if '--reload' in sys.argv or os.environ.get('PRTG_DEBUG'):
        import hupper
        hupper.start_reloader('app.main')
    main()
