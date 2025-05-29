# app.py (version 2)
import os
import re
import requests
from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
from bson import ObjectId

# --- Application Setup ---
app = Flask(__name__)
# A secret key is needed for flashing messages
app.secret_key = os.urandom(24) 

# --- GitHub API Configuration ---
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_API_URL = 'https://api.github.com/repos/'
HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json',
}

# --- Database Configuration ---
try:
    client = MongoClient('mongodb://localhost:27017/')
    db = client['repo_registrar_db']
    projects_collection = db['projects']
    client.admin.command('ping')
    print("MongoDB connection successful!")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    projects_collection = None

# --- Helper Functions ---

def parse_github_url(url):
    """Extracts owner and repo name from a GitHub URL using regex, removing .git suffix."""
    # Regex to capture owner and repo name. Repo name can include dots, hyphens.
    # It will also capture '.git' if present.
    pattern = r"https?://github\.com/([\w\-\.]+)/([\w\-\.]+)" 
    match = re.match(pattern, url)
    if match:
        owner, repo_name_with_git = match.groups()
        # Remove .git suffix if it exists
        if repo_name_with_git.endswith(".git"):
            repo_name = repo_name_with_git[:-4]
        else:
            repo_name = repo_name_with_git
        return owner, repo_name
    return None, None

def fetch_github_metadata(owner, repo):
    """Fetches repository metadata from the GitHub API."""
    if not GITHUB_TOKEN:
        print("WARNING: GITHUB_TOKEN is not set. API requests will be unauthenticated and rate-limited.")
        # Remove Authorization header if token is not available
        local_headers = {'Accept': 'application/vnd.github.v3+json'}
    else:
        local_headers = HEADERS

    api_call_url = f"{GITHUB_API_URL}{owner}/{repo}"
    print(f"Attempting to fetch from GitHub API: {api_call_url}") # Debug print

    try:
        response = requests.get(api_call_url, headers=local_headers)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        data = response.json()
        
        # Extract the most useful info
        metadata = {
            'description': data.get('description'),
            'stars': data.get('stargazers_count'),
            'forks': data.get('forks_count'),
            'language': data.get('language'),
            'open_issues': data.get('open_issues_count'),
            'license': data.get('license', {}).get('name') if data.get('license') else 'No license',
            'owner_avatar': data.get('owner', {}).get('avatar_url')
        }
        return metadata
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from GitHub API for {owner}/{repo}: {e}")
        return None

def get_all_projects():
    """Fetches all projects from the database."""
    if projects_collection is not None:
        return list(projects_collection.find().sort([("_id", -1)])) # Sort by most recent
    return []

def add_project(name, url, notes):
    """Adds a new project to the database, fetching metadata if it's a GitHub repo."""
    if projects_collection is None:
        flash("Database connection error. Cannot add project.", "error")
        return False
        
    metadata = {}
    project_name_to_save = name # Use user-provided name by default

    owner, repo = parse_github_url(url)
    if owner and repo:
        print(f"GitHub URL detected. Parsed as owner='{owner}', repo='{repo}'. Fetching data...")
        fetched_metadata = fetch_github_metadata(owner, repo)
        if fetched_metadata:
            metadata = fetched_metadata
            # If the user didn't provide a name, or provided an empty name, use the repo name from GitHub
            if not project_name_to_save or project_name_to_save.strip() == "":
                project_name_to_save = repo 
            flash(f"Successfully fetched data for {owner}/{repo}!", "success")
        else:
            flash(f"Could not fetch GitHub data for {owner}/{repo}. Please check the URL and ensure the repository is public.", "error")
            # If fetching fails but it looked like a GitHub URL, still save it but without metadata
            if not project_name_to_save or project_name_to_save.strip() == "": # if name was still empty
                 project_name_to_save = url.split('/')[-1].replace('.git','') # fallback name
    elif not project_name_to_save or project_name_to_save.strip() == "":
        # If not a GitHub URL and no name provided, try to make a sensible name from the URL
        try:
            project_name_to_save = url.split('/')[-1] or url.split('/')[-2] or "Untitled Project"
        except:
            project_name_to_save = "Untitled Project"


    project_data = {
        "name": project_name_to_save,
        "url": url,
        "notes": notes,
        "tags": [],
        "category": "",
        "status": "To Do",
        "priority": "Medium",
        "metadata": metadata 
    }
    try:
        projects_collection.insert_one(project_data)
        return True
    except Exception as e:
        print(f"Error inserting project into MongoDB: {e}")
        flash("Error saving project to database.", "error")
        return False


def delete_project_by_id(project_id_str):
    """Deletes a project by its ID."""
    if projects_collection is None: return False
    try:
        projects_collection.delete_one({"_id": ObjectId(project_id_str)})
        return True
    except Exception as e:
        print(f"Error deleting project: {e}")
        return False

# --- Routes ---
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        project_name_input = request.form.get('project_name')
        project_url_input = request.form.get('project_url')
        project_notes_input = request.form.get('project_notes')

        if project_url_input and project_url_input.strip() != "": # URL is the only truly required field now
            if add_project(project_name_input, project_url_input, project_notes_input):
                print(f"Project processed: {project_name_input or project_url_input}")
            # Flash messages are handled within add_project
            return redirect(url_for('index'))
        else:
            flash("Project URL is a required field.", "error")
            
    projects = get_all_projects()
    return render_template('index.html', projects=projects)

@app.route('/delete/<project_id>', methods=['POST'])
def delete_project_route(project_id):
    if delete_project_by_id(project_id):
        flash("Project deleted successfully.", "success")
    else:
        flash("Failed to delete project.", "error")
    return redirect(url_for('index'))

# --- Main Execution ---
if __name__ == '__main__':
    app.run(debug=True)
