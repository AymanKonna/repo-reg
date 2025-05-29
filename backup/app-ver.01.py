# app.py
from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from bson import ObjectId # Required for converting string ID to ObjectId for MongoDB

# --- Application Setup ---
app = Flask(__name__)

# --- Database Configuration ---
# Connect to your local MongoDB instance
# Make sure MongoDB is running on localhost:27017
try:
    client = MongoClient('mongodb://localhost:27017/')
    db = client['repo_registrar_db'] # Database name
    projects_collection = db['projects'] # Collection name
    # Test connection
    client.admin.command('ping')
    print("MongoDB connection successful!")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    # Fallback for if MongoDB is not available, to prevent app crash on startup
    # In a real app, you might handle this more gracefully
    projects_collection = None


# --- Helper Functions ---
def get_all_projects():
    """Fetches all projects from the database."""
    if projects_collection is not None:
        # Sort by 'name' alphabetically, or by '_id' for insertion order if name is not always present
        return list(projects_collection.find().sort("name", 1))
    return []

def add_project(name, url, notes):
    """Adds a new project to the database."""
    if projects_collection is not None:
        project_data = {
            "name": name,
            "url": url,
            "notes": notes,
            # We can add more fields later like tags, category, status, etc.
            "tags": [],
            "category": "",
            "status": "To Do",
            "priority": "Medium",
            "metadata": {} # For fetched data later
        }
        projects_collection.insert_one(project_data)
        return True
    return False

def delete_project_by_id(project_id_str):
    """Deletes a project by its ID."""
    if projects_collection is not None:
        try:
            project_oid = ObjectId(project_id_str)
            result = projects_collection.delete_one({"_id": project_oid})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting project: {e}")
            return False
    return False

# --- Routes ---
@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Main page: Displays projects and handles new project submissions.
    """
    if request.method == 'POST':
        project_name = request.form.get('project_name')
        project_url = request.form.get('project_url')
        project_notes = request.form.get('project_notes')

        if project_name and project_url: # Basic validation
            if add_project(project_name, project_url, project_notes):
                print(f"Project added: {project_name}")
            else:
                print("Failed to add project (MongoDB connection issue?)")
            return redirect(url_for('index')) # Redirect to clear form and show updated list
        else:
            # Handle case where required fields are missing (though HTML 'required' should catch this)
            print("Project name or URL missing.")
            # You could pass an error message to the template here
            pass

    projects = get_all_projects()
    return render_template('index.html', projects=projects)

@app.route('/delete/<project_id>', methods=['POST'])
def delete_project_route(project_id):
    """
    Handles project deletion.
    """
    if delete_project_by_id(project_id):
        print(f"Project deleted: {project_id}")
    else:
        print(f"Failed to delete project: {project_id}")
    return redirect(url_for('index'))


# --- Main Execution ---
if __name__ == '__main__':
    # Create a templates folder in the same directory as app.py
    # and put index.html inside it.
    # To run:
    # 1. Ensure MongoDB is running.
    # 2. Install Flask and pymongo: pip install Flask pymongo
    # 3. Run this script: python app.py
    # 4. Open your browser to http://127.0.0.1:5000
    app.run(debug=True)