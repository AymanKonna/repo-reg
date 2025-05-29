# Repository Registrar

## Project Documentation
> Version: 1.0
> Date: May 29, 2025

### 1. Project Overview
Project Name: Repository Registrar

**Objectives:** 
To create a self-hosted web application that allows a user to save, track, and organize interesting software projects, code repositories, and other online resources. The goal is to solve the common problem of discovering a useful project but later forgetting about it.

**Current Status:**
The core application is functional. It features a single-page interface for adding new projects and viewing the existing list. It successfully integrates with the GitHub API to automatically fetch metadata for public repositories and allows users to add their own organizational data (tags, categories, etc.).

### 2. Implemented Features
As of the current version, the application supports the following features:

### Project Registration

Users can add a new project via a primary URL.

#### Automatic Metadata Fetching (GitHub)

When a valid public GitHub repository URL is provided, the application automatically fetches key metadata.

**Fetched Data:**
Repository Description, Star Count, Fork Count, Primary Programming Language, and Open Issues Count.

**Auto-Naming:**
If the "Project Name" field is left blank, the application uses the repository's name from GitHub.

#### Manual Data Entry & Organization

**Personal Notes:**
A dedicated text area for users to add their own notes, reminders, or to-do items for a project.

**Tagging:**
Users can add multiple, comma-separated tags to each project for flexible organization (e.g., python, homelab, data-science).

**Categorization:**
Each project can be assigned a category from a predefined list (e.g., "Work Utility," "Side Project," "Learning Resource").

**Status Tracking:**
Projects can be marked with a status from a predefined list (e.g., "To Do," "In Progress," "Completed").

**Priority Setting:**
Projects can be assigned a priority level ("Low," "Medium," "High," "Urgent").

**Data Persistence:**
All project information, including user notes and fetched metadata, is stored in a MongoDB database.

**User Interface:**

A clean, single-page web interface built with Flask and styled with Tailwind CSS.

Project listings are displayed as cards, showing all relevant information in a readable format.

The form includes dropdowns for predefined categories, statuses, and priorities.

Flash messages provide user feedback for successful actions or errors.

Project Deletion: Users can delete a project from the database via a "Delete" button on its card.

3. Technical Architecture
Backend:

Language: Python 3.12

Web Framework: Flask

Database: MongoDB (communicating via the pymongo driver)

Key Dependencies:

Flask: For the web server and routing.

pymongo: For all database interactions.

requests: For making HTTP requests to the external GitHub API.

Frontend:

Technology: Server-side rendered HTML using the Jinja2 templating engine, which is integrated with Flask.

Styling: Tailwind CSS, loaded via a CDN for rapid styling and a modern look.

Environment:

Python Environment: Managed using Miniconda to ensure isolated and reproducible dependencies.

API Keys: Requires a GITHUB_TOKEN to be set as an environment variable for making authenticated requests to the GitHub API, which provides a higher rate limit.

4. Project Setup & Usage
To run the project locally, the following steps are required:

Prerequisites:

Miniconda installed.

A running MongoDB instance.

Environment Setup:

# Create and activate a new conda environment
conda create --name repo-reg python=3.12 -y
conda activate repo-reg

Install Dependencies:

pip install Flask pymongo requests

Set Environment Variable:

# Set your GitHub Personal Access Token (for the current terminal session)
export GITHUB_TOKEN='your_github_token_here'

File Structure:

A main app.py file containing the Flask application logic.

A templates/ directory containing the index.html file.

Run the Application:

python app.py

Access: Open a web browser and navigate to http://127.0.0.1:5000.

5. Future Roadmap & Pending Requirements
This section outlines features and improvements planned for future development iterations:

Search & Filtering (High Priority): Implement a search bar and filtering controls to allow users to easily find projects by name, tag, category, status, or other metadata.

Edit Functionality: Add the ability for users to edit the details of an already registered project (e.g., change its status, add new tags, update notes).

Expanded Metadata Fetching: Add support for fetching metadata from other popular sources like:

YouTube (video title, channel)

GitLab / Bitbucket

UI/UX Overhaul (Decision Pending):

Migrate the frontend to a modern JavaScript framework like React or Next.js.

Integrate a component library like shadcn/ui for a more polished and interactive user experience.

Explore data visualization options, such as a graph-view, to show relationships between projects.

User Authentication: Implement a full user login/registration system to make the application private and potentially multi-tenant.

Deployment:

Create a Dockerfile and docker-compose.yml to containerize the application for easy, reproducible deployment on a homelab server or in the cloud.

The current code for the project is captured in the immersive artifact: repo_registrar_app_v0_2.
