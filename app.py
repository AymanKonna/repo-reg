# app.py (version 3.1 - Categories, Status, Priority)
import os
import re
import requests
from flask import Flask, render_template, request, redirect, url_for, flash
from pymongo import MongoClient
from bson import ObjectId

# --- Application Setup ---
app = Flask(__name__)
app.secret_key = os.urandom(24) 

# --- Predefined Options ---
# These can be expanded or moved to a config file/database later
PROJECT_CATEGORIES = ["Work Utility", "Side Project", "Learning Resource", "Homelab Setup", "Tool", "Library", "Framework", "Miscellaneous"]
PROJECT_STATUSES = ["To Do", "Backlog", "In Progress", "On Hold", "Completed", "Archived", "Idea"]
PROJECT_PRIORITIES = ["Low", "Medium", "High", "Urgent"]

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
    pattern = r"https?://github\.com/([\w\-\.]+)/([\w\-\.]+)" 
    match = re.match(pattern, url)
    if match:
        owner, repo_name_with_git = match.groups()
        repo_name = repo_name_with_git[:-4] if repo_name_with_git.endswith(".git") else repo_name_with_git
        return owner, repo_name
    return None, None

def fetch_github_metadata(owner, repo):
    """Fetches repository metadata from the GitHub API."""
    if not GITHUB_TOKEN:
        print("WARNING: GITHUB_TOKEN is not set. API requests will be unauthenticated and rate-limited.")
        local_headers = {'Accept': 'application/vnd.github.v3+json'}
    else:
        local_headers = HEADERS
    
    api_call_url = f"{GITHUB_API_URL}{owner}/{repo}"
    print(f"Attempting to fetch from GitHub API: {api_call_url}")
    try:
        response = requests.get(api_call_url, headers=local_headers)
        response.raise_for_status()
        data = response.json()
        return {
            'description': data.get('description'),
            'stars': data.get('stargazers_count'),
            'forks': data.get('forks_count'),
            'language': data.get('language'),
            'open_issues': data.get('open_issues_count'),
            'license': data.get('license', {}).get('name') if data.get('license') else 'No license',
            'owner_avatar': data.get('owner', {}).get('avatar_url')
        }
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from GitHub API for {owner}/{repo}: {e}")
        return None

def get_all_projects():
    """Fetches all projects from the database, sorted by most recent."""
    if projects_collection is not None:
        return list(projects_collection.find().sort([("_id", -1)]))
    return []

def add_project(name, url, notes, tags_string, category, status, priority): # Added new params
    """Adds a new project to the database, including new organizational fields."""
    if projects_collection is None:
        flash("Database connection error. Cannot add project.", "error")
        return False
        
    metadata = {}
    project_name_to_save = name

    if tags_string:
        tags_list = sorted(list(set([tag.strip() for tag in tags_string.split(',') if tag.strip()])))
    else:
        tags_list = []

    owner, repo = parse_github_url(url)
    if owner and repo:
        print(f"GitHub URL detected. Parsed as owner='{owner}', repo='{repo}'. Fetching data...")
        fetched_metadata = fetch_github_metadata(owner, repo)
        if fetched_metadata:
            metadata = fetched_metadata
            if not project_name_to_save or project_name_to_save.strip() == "":
                project_name_to_save = repo 
            flash(f"Successfully fetched data for {owner}/{repo}!", "success")
        else:
            flash(f"Could not fetch GitHub data for {owner}/{repo}. Check URL/public status.", "error")
            if not project_name_to_save or project_name_to_save.strip() == "":
                 project_name_to_save = url.split('/')[-1].replace('.git','') if '.git' in url else url.split('/')[-1]
    elif not project_name_to_save or project_name_to_save.strip() == "":
        try:
            path_parts = [part for part in url.split('/') if part]
            project_name_to_save = path_parts[-1] if path_parts else "Untitled Project"
        except:
            project_name_to_save = "Untitled Project"

    project_data = {
        "name": project_name_to_save,
        "url": url,
        "notes": notes,
        "tags": tags_list,
        "category": category if category in PROJECT_CATEGORIES else PROJECT_CATEGORIES[0], # Validate or default
        "status": status if status in PROJECT_STATUSES else PROJECT_STATUSES[0],       # Validate or default
        "priority": priority if priority in PROJECT_PRIORITIES else PROJECT_PRIORITIES[0], # Validate or default
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
    """Main page: Displays projects and handles new project submissions."""
    if request.method == 'POST':
        project_name_input = request.form.get('project_name', '').strip()
        project_url_input = request.form.get('project_url', '').strip()
        project_notes_input = request.form.get('project_notes', '').strip()
        project_tags_input = request.form.get('project_tags', '').strip()
        project_category_input = request.form.get('project_category') # New field
        project_status_input = request.form.get('project_status')     # New field
        project_priority_input = request.form.get('project_priority') # New field

        if project_url_input:
            if add_project(project_name_input, project_url_input, project_notes_input, project_tags_input,
                           project_category_input, project_status_input, project_priority_input): # Pass new fields
                pass
            return redirect(url_for('index'))
        else:
            flash("Project URL is a required field.", "error")
            projects = get_all_projects()
            # Pass options to template even on failed POST to repopulate dropdowns
            return render_template('index.html', projects=projects,
                                   categories=PROJECT_CATEGORIES,
                                   statuses=PROJECT_STATUSES,
                                   priorities=PROJECT_PRIORITIES)
            
    projects = get_all_projects()
    # Pass options to template for GET request to populate dropdowns
    return render_template('index.html', projects=projects,
                           categories=PROJECT_CATEGORIES,
                           statuses=PROJECT_STATUSES,
                           priorities=PROJECT_PRIORITIES)

@app.route('/delete/<project_id>', methods=['POST'])
def delete_project_route(project_id):
    """Handles project deletion."""
    if delete_project_by_id(project_id):
        flash("Project deleted successfully.", "success")
    else:
        flash("Failed to delete project.", "error")
    return redirect(url_for('index'))

# --- Main Execution ---
if __name__ == '__main__':
    app.run(debug=True)