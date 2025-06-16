from flask import Flask, request, jsonify, send_file
from datetime import datetime, timedelta # Add timedelta
from base64 import b64encode
from flask_cors import CORS
import os # ADDED
import sys # ADDED
import logging # ADDED
import requests # ADDED: Importing requests module
import time # ADDED: Importing time module for debugging
import sqlite3
from threading import Lock
from functools import lru_cache

# Import logging
# stdout logging için
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode # Add urllib.parse

# Azure DevOps SDK imports
from msrest.authentication import BasicAuthentication
from azure.devops.connection import Connection
# Note: Specific clients like CoreClient, GitClient are obtained via connection.clients.get_..._client()
# and do not need to be imported directly if using that pattern.

app = Flask(__name__)
CORS(app)

# Logging ayarları
app.logger.handlers.clear() # Mevcut handler'ları temizle
app.logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler(sys.stdout) # Logları stdout'a yönlendir
stream_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s [in %(pathname)s:%(lineno)d]')
stream_handler.setFormatter(formatter)
app.logger.addHandler(stream_handler)

AZURE_DEVOPS_ORG_URL = os.getenv('AZURE_DEVOPS_ORG_URL')
AZURE_DEVOPS_PAT = os.getenv('AZURE_DEVOPS_PAT')

DB_PATH = 'devops_cache.db'
db_lock = Lock()

# In-memory cache for project metrics
metrics_cache = {}
metrics_cache_expiry = 300  # seconds (5 minutes)

def init_db():
    with db_lock, sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS projects_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cache_key TEXT UNIQUE,
            data TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        conn.commit()

init_db()

def get_cache(cache_key):
    with db_lock, sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('SELECT data, updated_at FROM projects_cache WHERE cache_key=?', (cache_key,))
        row = c.fetchone()
        if row:
            return row[0], row[1]
        return None, None

def set_cache(cache_key, data):
    with db_lock, sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('''INSERT INTO projects_cache (cache_key, data, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)
                     ON CONFLICT(cache_key) DO UPDATE SET data=excluded.data, updated_at=CURRENT_TIMESTAMP''', (cache_key, data))
        conn.commit()

@app.route('/api/health', methods=['GET'])
def health_check():
    app.logger.info("Health check endpoint called.")
    return jsonify({"status": "healthy", "message": "API is running."}), 200

@app.route('/api/env-check', methods=['GET'])
def env_check():
    app.logger.info("Environment check endpoint called.")
    org_url_set = bool(AZURE_DEVOPS_ORG_URL)
    pat_set = bool(AZURE_DEVOPS_PAT)
    return jsonify({
        "AZURE_DEVOPS_ORG_URL_SET": org_url_set,
        "AZURE_DEVOPS_PAT_SET": pat_set,
        "ORG_URL_VALUE_DEBUG": AZURE_DEVOPS_ORG_URL[:15] + "..." if org_url_set else "Not set"
    }), 200

# Get Azure DevOps API headers
# def get_headers(organization, pat):
#     token = b64encode(f':{pat}'.encode()).decode()
#     return {
#         'Authorization': f'Basic {token}',
#         'Content-Type': 'application/json'
#     }

def get_devops_pat():
    pat = os.environ.get('AZURE_DEVOPS_PAT')
    if not pat:
        app.logger.error("AZURE_DEVOPS_PAT environment variable not set.") # ADDED logger
        raise ValueError("Azure DevOps PAT not configured in environment.")
    return pat

def get_devops_org_url():
    org_url = os.environ.get('AZURE_DEVOPS_ORG_URL')
    if not org_url:
        app.logger.error("AZURE_DEVOPS_ORG_URL environment variable not set.")
        raise ValueError("Azure DevOps Org URL not configured in environment.")
    # Ensure it doesn't end with a slash for consistent joining
    return org_url.rstrip('/')

def get_headers():
    pat = get_devops_pat()
    token = b64encode(f':{pat}'.encode()).decode()
    return {
        'Authorization': f'Basic {token}',
        'Content-Type': 'application/json'
    }

# Helper function to fetch projects
# def get_projects_data(organization, pat):
#     app.logger.info(f\"[get_projects_data] Org: {organization}, PAT: {\'******\' if pat else \'None\'}\")
#     api_version = \'7.1-preview.1\'
#     url = f\'https://dev.azure.com/{organization}/_apis/projects?api-version={api_version}\'
#     response = requests.get(url, headers=get_headers(organization, pat))
#     response.raise_for_status() 
#     return response.json().get(\'value\', [])

def get_projects_data():
    org_url = get_devops_org_url()
    app.logger.info(f"[get_projects_data] Fetching projects for org: {org_url}")
    api_version = '7.1-preview.1' # Corrected: Removed backslashes
    # The org_url from env is expected to be like https://dev.azure.com/OrgName
    url = f'{org_url}/_apis/projects?api-version={api_version}' # Corrected: Removed backslashes
    response = requests.get(url, headers=get_headers())
    response.raise_for_status()
    return response.json().get('value', [])

# Helper function to fetch pipelines for a project
# def get_pipelines_data(organization, pat, project_name):
#     api_version = '7.1-preview.1' # Corrected: Removed backslashes
#     url = f'https://dev.azure.com/{organization}/{project_name}/_apis/pipelines?api-version={api_version}' # Corrected: Removed backslashes
#     response = requests.get(url, headers=get_headers(organization, pat))
#     response.raise_for_status()
#     return response.json().get('value', [])

def get_pipelines_data(project_name):
    org_url = get_devops_org_url()
    app.logger.info(f"[get_pipelines_data] Fetching pipelines for project: {project_name} in org: {org_url}")
    api_version = '7.1-preview.1' # Corrected: Removed backslashes
    url = f'{org_url}/{project_name}/_apis/pipelines?api-version={api_version}' # Corrected: Removed backslashes
    response = requests.get(url, headers=get_headers())
    response.raise_for_status()
    return response.json().get('value', [])

# Helper function to fetch repositories for a project
# def get_repos_data(organization, pat, project_name):
#     api_version = '7.1-preview.1' # Corrected: Removed backslashes
#     url = f'https://dev.azure.com/{organization}/{project_name}/_apis/git/repositories?api-version={api_version}' # Corrected: Removed backslashes
#     response = requests.get(url, headers=get_headers(organization, pat))
#     response.raise_for_status()
#     return response.json().get('value', [])

def get_repos_data(project_name): # Assuming this might be needed later
    org_url = get_devops_org_url()
    app.logger.info(f"[get_repos_data] Fetching repos for project: {project_name} in org: {org_url}")
    api_version = '7.1-preview.1' # Corrected: Removed backslashes
    url = f'{org_url}/{project_name}/_apis/git/repositories?api-version={api_version}' # Corrected: Removed backslashes
    response = requests.get(url, headers=get_headers())
    response.raise_for_status()
    return response.json().get('value', [])

# Helper function to fetch release definitions for a project
# def get_releases_data(organization, pat, project_name):
#     api_version = '7.0' # Corrected: Removed backslashes
#     url = f'https://vsrm.dev.azure.com/{organization}/{project_name}/_apis/release/definitions?api-version={api_version}' # Corrected: Removed backslashes
#     response = requests.get(url, headers=get_headers(organization, pat))
#     response.raise_for_status()
#     return response.json().get('value', [])

def get_releases_data(project_name):
    org_url = get_devops_org_url()
    # Extract organization name for vsrm URL
    # org_url is like https://dev.azure.com/OrgName. We need OrgName.
    organization_name = org_url.split('/')[-1]
    app.logger.info(f"[get_releases_data] Fetching release definitions for project: {project_name} in org: {organization_name}")
    api_version = '7.0' 
    url = f'https://vsrm.dev.azure.com/{organization_name}/{project_name}/_apis/release/definitions?api-version={api_version}' # Corrected: Removed backslashes
    response = requests.get(url, headers=get_headers())
    response.raise_for_status()
    return response.json().get('value', [])

# Helper function to fetch commits for a repository within a date range
def get_commits_data(organization, project_name, repository_id, start_date, end_date, repository_name=None):
    api_version = '7.1-preview.1'
    url = f'https://dev.azure.com/{organization}/{project_name}/_apis/git/repositories/{repository_id}/commits'
    params = {
        'searchCriteria.fromDate': start_date,
        'searchCriteria.toDate': end_date,
        'api-version': api_version,
        '$top': 50 # Fetch more to ensure we have enough after filtering, if needed
    }
    response = requests.get(url, headers=get_headers(), params=params)
    response.raise_for_status()
    commits = response.json().get('value', [])
    if repository_name:
        for commit in commits:
            commit['repositoryName'] = repository_name
    return commits

# Helper function to fetch all deployments for a project within a date range
def get_all_deployments_for_project(organization, project_name, start_date_str, end_date_str): # REMOVED pat
    api_version = '7.0'  # Use a recent, stable API version for deployments
    deployments = []
    
    headers = get_headers() # CHANGED: get_headers() called without args
    
    # Initial URL construction
    # Note: The 'organization' parameter here is the organization NAME, not the full URL.
    # vsrm.dev.azure.com requires the organization name.
    base_url_for_pagination = f"https://vsrm.dev.azure.com/{organization}/{project_name}/_apis/release/deployments"
    query_params = {
        'api-version': api_version,
        'minCompletedTime': start_date_str,
        'maxCompletedTime': end_date_str,
        '$expand': 'releaseEnvironment',
        # '$top': 100 # Optionally add $top to control page size
    }
    current_url = f"{base_url_for_pagination}?{urlencode(query_params)}"
    app.logger.info(f"[get_all_deployments_for_project] Initial URL: {current_url}")

    while current_url:
        try:
            response = requests.get(current_url, headers=headers)
            app.logger.debug(f"[get_all_deployments_for_project] Request to {current_url} status: {response.status_code}")
            response.raise_for_status()
            data = response.json()
            page_deployments = data.get('value', [])
            deployments.extend(page_deployments)
            app.logger.debug(f"[get_all_deployments_for_project] Fetched {len(page_deployments)} deployments this page. Total so far: {len(deployments)}")
            
            if 'x-ms-continuationtoken' in response.headers:
                continuation_token = response.headers['x-ms-continuationtoken']
                app.logger.debug(f"[get_all_deployments_for_project] Got continuation token: {continuation_token}")
                # Update query_params for the next request
                query_params['continuationToken'] = continuation_token
                current_url = f"{base_url_for_pagination}?{urlencode(query_params)}" # Construct next page URL
                app.logger.info(f"[get_all_deployments_for_project] Next page URL: {current_url}")
            else:
                app.logger.debug("[get_all_deployments_for_project] No continuation token. All pages fetched.")
                current_url = None # No more pages
        except requests.exceptions.RequestException as e:
            app.logger.error(f"Error fetching deployments for project {project_name} at {current_url}: {e}")
            # Depending on desired behavior, could raise e or return partial/empty list
            # For counting, it's important to get all, so an error here might mean incomplete counts.
            break # Exit loop on error to avoid infinite loops on persistent issues

    app.logger.info(f"Found {len(deployments)} total deployments for project {project_name} in the time range.")
    return deployments

# Helper function to get pipeline runs count for a project
def get_pipeline_runs_count_for_project(organization_name, project_name, min_time_str, max_time_str):
    # This function uses the global get_headers() which relies on environment variables for PAT.
    # organization_name is extracted from AZURE_DEVOPS_ORG_URL for constructing the API URL.
    app.logger.info(f"[get_pipeline_runs_count_for_project] Project: {project_name}, Org: {organization_name}, MinTime: {min_time_str}, MaxTime: {max_time_str}")
    
    org_url_base = get_devops_org_url() # This is https://dev.azure.com/OrgName

    api_version = '7.0' 
    # Base URL for the API endpoint (without query parameters for pagination initially)
    endpoint_path = f"/{project_name}/_apis/build/builds"
    
    # Initial query parameters
    query_params = {
        'api-version': api_version,
        'minTime': min_time_str,
        'maxTime': max_time_str,
        'queryOrder': 'finishTimeDescending',
        # '$top': 100 # Optionally add $top to control page size
    }
    
    current_url = f"{org_url_base}{endpoint_path}?{urlencode(query_params)}"
    app.logger.info(f"[get_pipeline_runs_count_for_project] Initial URL: {current_url}")
    
    headers = get_headers() # Uses PAT from env
    
    all_runs_count = 0 # We only need the count, but we'll sum up counts from paged results.
                       # More efficiently, some APIs return a total count in headers or body.
                       # The builds API returns 'value' list and continuation token.

    page_num = 1
    while current_url:
        try:
            response = requests.get(current_url, headers=headers)
            app.logger.debug(f"[get_pipeline_runs_count_for_project] Page {page_num} request to {current_url} status: {response.status_code}")
            response.raise_for_status()
            data = response.json()
            runs_on_page = data.get('value', [])
            all_runs_count += len(runs_on_page)
            app.logger.debug(f"[get_pipeline_runs_count_for_project] Fetched {len(runs_on_page)} runs this page. Total count so far: {all_runs_count}")
            
            if 'x-ms-continuationtoken' in response.headers:
                continuation_token = response.headers['x-ms-continuationtoken']
                app.logger.debug(f"[get_pipeline_runs_count_for_project] Got continuation token: {continuation_token}")
                query_params['continuationToken'] = continuation_token # Add/update token for next page
                current_url = f"{org_url_base}{endpoint_path}?{urlencode(query_params)}"
                app.logger.info(f"[get_pipeline_runs_count_for_project] Next page URL: {current_url}")
                page_num +=1
            else:
                app.logger.debug("[get_pipeline_runs_count_for_project] No continuation token. All pages fetched.")
                current_url = None 
        except requests.exceptions.RequestException as e:
            app.logger.error(f"Error fetching pipeline runs for project {project_name} at {current_url}: {e}")
            break # Exit loop on error
            
    app.logger.info(f"Found {all_runs_count} pipeline runs for project {project_name} in the time range.")
    return all_runs_count

# Helper function to get commits count for a project
def get_commits_count_for_project(organization_name, project_name, start_date_str, end_date_str): # REMOVED pat
    # This function calls get_commits_data which expects 'organization_name'.
    app.logger.info(f"[get_commits_count_for_project] Project: {project_name}, Org: {organization_name}, Start: {start_date_str}, End: {end_date_str}")
    total_commits = 0
    try:
        # get_repos_data uses global get_headers() and get_devops_org_url()
        repos = get_repos_data(project_name) 
        app.logger.info(f"Found {len(repos)} repositories in project {project_name}.")
        for repo in repos:
            repo_id = repo['id'] # Ensure no backslashes
            repo_name = repo.get('name', 'UnknownRepo') # Ensure no backslashes
            # get_commits_data is an existing function. We pass parameters as it expects.
            # The 'pat' is no longer passed here.
            commits_list = get_commits_data(organization_name, project_name, repo_id, start_date_str, end_date_str) # REMOVED pat
            total_commits += len(commits_list)
            app.logger.debug(f"Repo {repo_name} ({repo_id}): {len(commits_list)} commits.")
        app.logger.info(f"Total commits for project {project_name}: {total_commits}")
        return total_commits
    except Exception as e:
        app.logger.error(f"Error fetching commits for project {project_name}: {e}", exc_info=True)
        return 0

@app.route('/api/activity_summary', methods=['GET']) # REMOVED backslashes
def activity_summary():
    app.logger.info("Activity summary endpoint called.")
    try:
        pat = get_devops_pat() # Still fetched, might be used elsewhere or for future needs.
        org_url_full = get_devops_org_url() 
        
        if not org_url_full: 
            raise ValueError("Azure DevOps Org URL not configured.")
        organization_name = org_url_full.split('/')[-1] # REMOVED backslashes
        
        app.logger.info(f"Operating for organization: {organization_name}")

        projects = get_projects_data() 
        if not projects:
            app.logger.warning("No projects found for the organization.")
            return jsonify({"message": "No projects found for the organization. Please check PAT and Org URL."}), 404

        now_utc = datetime.utcnow()
        
        today_start_utc = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
        
        periods = {
            "daily": {"start": today_start_utc, "end": now_utc},
            "weekly": {"start": now_utc - timedelta(days=7), "end": now_utc},
            "monthly": {"start": now_utc - timedelta(days=30), "end": now_utc}
        }
        
        summary_data = {
            period_name: {"pipeline_runs": 0, "releases": 0, "commits": 0}
            for period_name in periods
        }

        for project in projects:
            project_name = project.get('name') # REMOVED backslashes
            if not project_name:
                app.logger.warning(f"Project found with no name: {project.get('id')}. Skipping.") # REMOVED backslashes
                continue
            app.logger.info(f"Processing project: {project_name}")

            for period_name, dates in periods.items():
                start_date_iso = dates["start"].isoformat() + "Z"
                end_date_iso = dates["end"].isoformat() + "Z"
                
                app.logger.debug(f"Project: {project_name}, Period: {period_name}, Range: {start_date_iso} to {end_date_iso}")
                                
                pipeline_runs = get_pipeline_runs_count_for_project(organization_name, project_name, start_date_iso, end_date_iso)
                summary_data[period_name]["pipeline_runs"] += pipeline_runs
                app.logger.info(f"Project {project_name}, Period {period_name}: {pipeline_runs} pipeline runs.")

                # get_all_deployments_for_project no longer takes pat
                deployments_list = get_all_deployments_for_project(organization_name, project_name, start_date_iso, end_date_iso) # REMOVED pat
                releases_count = len(deployments_list)
                summary_data[period_name]["releases"] += releases_count
                app.logger.info(f"Project {project_name}, Period {period_name}: {releases_count} releases.")
                
                # get_commits_count_for_project no longer takes pat
                commits_count = get_commits_count_for_project(organization_name, project_name, start_date_iso, end_date_iso) # REMOVED pat
                summary_data[period_name]["commits"] += commits_count
                app.logger.info(f"Project {project_name}, Period {period_name}: {commits_count} commits.")

        app.logger.info(f"Final aggregated summary data: {summary_data}")
        return jsonify(summary_data)

    except ValueError as ve: 
        app.logger.error(f"Configuration error in activity_summary: {ve}", exc_info=True)
        return jsonify({"error": str(ve)}), 500
    except requests.exceptions.HTTPError as hre:
        app.logger.error(f"Azure DevOps API HTTP error in activity_summary: {hre.response.text if hre.response else hre}", exc_info=True)
        status_code = hre.response.status_code if hre.response is not None else 503
        return jsonify({"error": f"Azure DevOps API request error: {hre}", "details": hre.response.text if hre.response else "No response body"}), status_code
    except requests.exceptions.RequestException as re:
        app.logger.error(f"Azure DevOps API request error in activity_summary: {re}", exc_info=True)
        return jsonify({"error": f"Azure DevOps API request error: {re}"}), 503
    except Exception as e:
        app.logger.error(f"An unexpected error occurred in activity_summary: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred processing your request."}), 500

# API endpoints
@app.route('/api/projects', methods=['GET'])
def list_projects():
    try:
        projects = get_projects_data()
        project_list = [{"id": p.get("id"), "name": p.get("name")} for p in projects]
        return jsonify(project_list)
    except ValueError as ve: # Catch config errors
        app.logger.error(f"Configuration error: {ve}")
        return jsonify({"error": str(ve)}), 500
    except requests.exceptions.HTTPError as http_err:
        app.logger.error(f"HTTP error fetching projects: {http_err.response.status_code} - {http_err.response.text[:200]}")
        return jsonify({"error": "Failed to fetch projects from Azure DevOps", "details": str(http_err)}), http_err.response.status_code
    except Exception as e:
        app.logger.error(f"Error fetching projects: {e}")
        return jsonify({"error": "An unexpected error occurred while fetching projects."}), 500

@app.route('/api/projects/<project_name>/pipeline-counts', methods=['GET'])
def get_project_pipeline_counts(project_name):
    try:
        build_pipelines = get_pipelines_data(project_name)
        release_pipelines = get_releases_data(project_name)
        counts = {
            "project_name": project_name,
            "build_pipeline_count": len(build_pipelines),
            "release_pipeline_count": len(release_pipelines)
        }
        return jsonify(counts)
    except ValueError as ve: # Catch config errors
        app.logger.error(f"Configuration error: {ve}")
        return jsonify({"error": str(ve)}), 500
    except requests.exceptions.HTTPError as http_err:
        app.logger.error(f"HTTP error fetching pipeline counts for {project_name}: {http_err.response.status_code} - {http_err.response.text[:200]}")
        return jsonify({"error": f"Failed to fetch pipeline counts for project {project_name}", "details": str(http_err)}), http_err.response.status_code
    except Exception as e:
        app.logger.error(f"Error fetching pipeline counts for {project_name}: {e}")
        return jsonify({"error": f"An unexpected error occurred while fetching pipeline counts for {project_name}."}), 500

@app.route('/api/projects/<project_name>/metrics', methods=['GET'])
def get_project_metrics(project_name):
    import json
    from datetime import datetime
    from dateutil import parser as dtparser
    period = request.args.get('period', '7d')
    cache_key = f"metrics-{project_name}:{period}"
    now = time.time()
    # 1. Önce in-memory cache kontrolü
    if cache_key in metrics_cache and now - metrics_cache[cache_key]['time'] < metrics_cache_expiry:
        app.logger.info(f'[CACHE] Returning in-memory cached metrics for {cache_key}')
        return jsonify(metrics_cache[cache_key]['data'])
    # 2. Sonra SQLite cache kontrolü
    cache_data, cache_time = get_cache(cache_key)
    if cache_data:
        cache_dt = dtparser.parse(cache_time)
        if (datetime.utcnow() - cache_dt).total_seconds() < metrics_cache_expiry:
            app.logger.info(f'[CACHE] Returning SQLite cached metrics for {cache_key}')
            # Bellek cache'ini de güncelle
            metrics_cache[cache_key] = {'data': json.loads(cache_data), 'time': now}
            return jsonify(json.loads(cache_data))
    try:
        org_url_full = get_devops_org_url()
        if not org_url_full:
            raise ValueError("Azure DevOps Org URL not configured.")
        organization_name = org_url_full.split('/')[-1]

        # Parse period
        if period.endswith('d'):
            days = int(period[:-1])
        else:
            days = 7
        now_utc = datetime.utcnow()
        start_utc = now_utc - timedelta(days=days)
        start_date_iso = start_utc.isoformat() + "Z"
        end_date_iso = now_utc.isoformat() + "Z"

        # Metrics
        pipeline_runs = get_pipeline_runs_count_for_project(organization_name, project_name, start_date_iso, end_date_iso)
        app.logger.info(f"[METRIC] {project_name} pipeline_runs: {pipeline_runs}")
        deployments_list = get_all_deployments_for_project(organization_name, project_name, start_date_iso, end_date_iso)
        releases_count = len(deployments_list)
        app.logger.info(f"[METRIC] {project_name} releases_count: {releases_count}")
        commits_count = get_commits_count_for_project(organization_name, project_name, start_date_iso, end_date_iso)
        app.logger.info(f"[METRIC] {project_name} commits_count: {commits_count}")
        repos = get_repos_data(project_name)
        repository_count = len(repos)
        app.logger.info(f"[METRIC] {project_name} repository_count: {repository_count}")

        # Dashboard için toplam sayılar (adetler)
        pipelines = get_pipelines_data(project_name)
        releases = get_releases_data(project_name)
        repos = get_repos_data(project_name)

        pipeline_count = len(pipelines)
        release_count = len(releases)
        repository_count = len(repos)

        # Son 7 gün için commit sayısı
        org_url_full = get_devops_org_url()
        organization_name = org_url_full.split('/')[-1]
        now_utc = datetime.utcnow()
        if period.endswith('d'):
            days = int(period[:-1])
        else:
            days = 7
        start_utc = now_utc - timedelta(days=days)
        start_date_iso = start_utc.isoformat() + "Z"
        end_date_iso = now_utc.isoformat() + "Z"
        commit_count = get_commits_count_for_project(organization_name, project_name, start_date_iso, end_date_iso)

        # Calculate averages
        pipeline_run_avg_7d = round(pipeline_runs / days, 2) if days > 0 else pipeline_runs
        release_avg_7d = round(releases_count / days, 2) if days > 0 else releases_count

        # Fetch builds for the period
        api_version = '7.0'
        org_url_base = get_devops_org_url()
        builds_url = f"{org_url_base}/{project_name}/_apis/build/builds"
        builds_params = {
            'api-version': api_version,
            'minTime': start_date_iso,
            'maxTime': end_date_iso,
            'queryOrder': 'finishTimeDescending',
            '$top': 1000  # reasonable upper limit for 7 days
        }
        builds = []
        next_url = f"{builds_url}?{urlencode(builds_params)}"
        while next_url:
            resp = requests.get(next_url, headers=get_headers())
            resp.raise_for_status()
            data = resp.json()
            builds.extend(data.get('value', []))
            if 'x-ms-continuationtoken' in resp.headers:
                builds_params['continuationToken'] = resp.headers['x-ms-continuationtoken']
                next_url = f"{builds_url}?{urlencode(builds_params)}"
            else:
                next_url = None

        # 1. En Aktif Kullanıcılar (Commit sayısına göre, Son 7 gün)
        # Get all commits for the period
        commits_by_author = {}
        repos = get_repos_data(project_name)
        for repo in repos:
            repo_id = repo['id']
            repo_name = repo.get('name', 'UnknownRepo')
            commits = get_commits_data(organization_name, project_name, repo_id, start_date_iso, end_date_iso, repository_name=repo_name)
            for commit in commits:
                author = commit.get('author', {}).get('name', 'Unknown')
                if author:
                    commits_by_author[author] = commits_by_author.get(author, 0) + 1
        top_committers = sorted(commits_by_author.items(), key=lambda x: x[1], reverse=True)[:5]
        top_committers = [{"name": name, "commit_count": count} for name, count in top_committers]

        # 2. Release Success Rate (Son 7 gün)
        # deployments_list already fetched
        total_releases = len(deployments_list)
        successful_releases = sum(1 for d in deployments_list if d.get('deploymentStatus', '').lower() == 'succeeded')
        release_success_rate = (successful_releases / total_releases * 100) if total_releases > 0 else None

        # 3. Ortalama Build Süresi (Son 7 gün)
        build_durations = []
        for build in builds:
            start = build.get('startTime')
            finish = build.get('finishTime')
            if start and finish:
                try:
                    start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    finish_dt = datetime.fromisoformat(finish.replace('Z', '+00:00'))
                    duration = (finish_dt - start_dt).total_seconds()
                    if duration > 0:
                        build_durations.append(duration)
                except Exception:
                    continue
        avg_build_duration = round(sum(build_durations) / len(build_durations), 2) if build_durations else None

        # 4. Başarılı Build Oranı (Son 7 gün)
        total_builds = len(builds)
        successful_builds = sum(1 for b in builds if b.get('result', '').lower() == 'succeeded')
        build_success_rate = (successful_builds / total_builds * 100) if total_builds > 0 else None
        # Eksik olan metrik: toplam build sayısı (Son 7 gün)
        total_build_count_7d = total_builds

        result = {
            "project_name": project_name,
            "pipeline_count": pipeline_count,
            "release_count": release_count,
            "repository_count": repository_count,
            "commit_count": commit_count,
            "pipeline_run_avg_7d": pipeline_run_avg_7d,
            "release_avg_7d": release_avg_7d,
            # New metrics:
            "top_committers": top_committers,
            "release_success_rate": release_success_rate,
            "total_build_count_7d": total_build_count_7d,
            "build_success_rate": build_success_rate
        }
        # 3. Hem in-memory hem SQLite cache güncelle
        metrics_cache[cache_key] = {'data': result, 'time': now}
        set_cache(cache_key, json.dumps(result))
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error in get_project_metrics for {project_name}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/projects/<project_name>/recent-commits', methods=['GET'])
def get_project_recent_commits(project_name):
    app.logger.info(f"Fetching recent commits for project: {project_name}")
    try:
        organization_name = get_devops_org_url().split('/')[-1]
        repos = get_repos_data(project_name)
        all_commits = []
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        start_date_str = start_date.isoformat() + "Z"
        end_date_str = end_date.isoformat() + "Z"
        for repo in repos:
            repo_id = repo.get('id')
            repo_name = repo.get('name')
            if repo_id:
                try:
                    commits = get_commits_data(organization_name, project_name, repo_id, start_date_str, end_date_str, repository_name=repo_name)
                    all_commits.extend(commits)
                except requests.exceptions.HTTPError as e:
                    app.logger.error(f"Failed to fetch commits for repo {repo_name} ({repo_id}): {e}")
                    if e.response is not None and e.response.status_code == 404:
                        app.logger.info(f"Repo {repo_name} might be empty or recently created.")
                except Exception as e:
                    app.logger.error(f"An unexpected error occurred fetching commits for repo {repo_name} ({repo_id}): {e}")
        all_commits.sort(key=lambda c: c.get('author', {}).get('date'), reverse=True)
        limit = int(request.args.get('limit', 10))
        return jsonify(all_commits[:limit])
    except ValueError as e:
        app.logger.error(f"Configuration error for recent commits: {e}")
        return jsonify({"error": str(e)}), 500
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Azure DevOps API request error for recent commits: {e}")
        error_detail = str(e)
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
            except ValueError:
                error_detail = e.response.text
        return jsonify({"error": "Failed to connect to Azure DevOps", "details": error_detail}), 503
    except Exception as e:
        app.logger.error(f"Unexpected error fetching recent commits: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/api/devops-info', methods=['GET'])
def get_devops_info():
    app.logger.info("Endpoint /api/devops-info called.")
    cache_key = 'devops-info-v1'
    cache_data, cache_time = get_cache(cache_key)
    # 1 saatten eskiyse güncelle
    max_age_sec = 3600
    if cache_data:
        from datetime import datetime, timedelta
        from dateutil import parser as dtparser
        cache_dt = dtparser.parse(cache_time)
        if (datetime.utcnow() - cache_dt).total_seconds() < max_age_sec:
            app.logger.info(f"Returning cached devops-info (age: {(datetime.utcnow() - cache_dt).total_seconds()}s)")
            import json
            return jsonify(json.loads(cache_data))

    # Cache yoksa veya eskiyse canlı çek
    if not AZURE_DEVOPS_ORG_URL or not AZURE_DEVOPS_PAT:
        app.logger.error("AZURE_DEVOPS_ORG_URL or AZURE_DEVOPS_PAT is not set in environment variables.")
        return jsonify({"error": "Azure DevOps Organization URL or Personal Access Token is not configured on the server."}), 500

    app.logger.info(f"Attempting to connect to Azure DevOps. Org URL starts with: {AZURE_DEVOPS_ORG_URL[:30] if AZURE_DEVOPS_ORG_URL else 'N/A'}")
    app.logger.info(f"PAT is {'set' if AZURE_DEVOPS_PAT else 'NOT SET'}.")

    try:
        credentials = BasicAuthentication('', AZURE_DEVOPS_PAT)
        connection = Connection(base_url=AZURE_DEVOPS_ORG_URL, creds=credentials)
        app.logger.info("Successfully created Azure DevOps connection object.")

        core_client = connection.clients.get_core_client()
        git_client = connection.clients.get_git_client()
        release_client = connection.clients.get_release_client()
        build_client = connection.clients.get_build_client()
        app.logger.info("Successfully obtained Azure DevOps API clients.")

        projects = core_client.get_projects()
        app.logger.info(f"Successfully fetched {len(projects)} projects.")
        
        projects_data = []
        for project in projects:
            app.logger.info(f"Processing project: {project.name} (ID: {project.id})")
            project_info = {
                "project_id": project.id,
                "project_name": project.name,
                "repositories": [],
                "build_pipelines": [],
                "release_pipelines": []
            }

            try:
                repos = git_client.get_repositories(project=project.id)
                project_info["repositories"] = [repo.name for repo in repos]
                app.logger.info(f"Fetched {len(project_info['repositories'])} repositories for project '{project.name}'.")
            except Exception as e_repo:
                app.logger.error(f"Error fetching repositories for project '{project.name}': {str(e_repo)}")
                project_info["repositories"].append(f"Error fetching repositories: {str(e_repo)}")

            try:
                build_definitions = build_client.get_definitions(project=project.id)
                project_info["build_pipelines"] = [definition.name for definition in build_definitions]
                app.logger.info(f"Fetched {len(project_info['build_pipelines'])} build pipelines for project '{project.name}'.")
            except Exception as e_build:
                app.logger.error(f"Error fetching build pipelines for project '{project.name}': {str(e_build)}")
                project_info["build_pipelines"].append(f"Error fetching build pipelines: {str(e_build)}")

            try:
                release_definitions = release_client.get_release_definitions(project=project.id)
                project_info["release_pipelines"] = [definition.name for definition in release_definitions]
                app.logger.info(f"Fetched {len(project_info['release_pipelines'])} release pipelines for project '{project.name}'.")
            except Exception as e_release:
                app.logger.error(f"Error fetching release pipelines for project '{project.name}': {str(e_release)}")
                project_info["release_pipelines"].append(f"Error fetching release pipelines: {str(e_release)}")
            
            projects_data.append(project_info)
        
        app.logger.info("Successfully processed all projects and their details.")
        import json
        set_cache(cache_key, json.dumps(projects_data))
        return jsonify(projects_data)

    except Exception as e:
        app.logger.error(f"A general error occurred in /api/devops-info: {str(e)}", exc_info=True)
        return jsonify({"error": f"An error occurred while communicating with Azure DevOps API. Check server logs for details. Error type: {type(e).__name__}"}), 500

@app.route('/api/projects/<project_name>/repos', methods=['GET'])
def get_project_repos(project_name):
    """
    Returns repositories for a given project, with SQLite caching (10dk).
    """
    import json
    cache_key = f"repos-{project_name}"
    cache_data, cache_time = get_cache(cache_key)
    max_age_sec = 600  # 10 dakika
    from datetime import datetime
    from dateutil import parser as dtparser
    if cache_data:
        cache_dt = dtparser.parse(cache_time)
        if (datetime.utcnow() - cache_dt).total_seconds() < max_age_sec:
            app.logger.info(f"Returning cached repos for {project_name} (age: {(datetime.utcnow() - cache_dt).total_seconds()}s)")
            return jsonify(json.loads(cache_data))
    try:
        repos = get_repos_data(project_name)
        set_cache(cache_key, json.dumps(repos))
        return jsonify(repos)
    except Exception as e:
        app.logger.error(f"Error fetching repos for {project_name}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/projects/<project_name>/pipelines', methods=['GET'])
def get_project_pipelines(project_name):
    """
    Returns pipelines for a given project, with SQLite caching (10dk).
    """
    import json
    cache_key = f"pipelines-{project_name}"
    cache_data, cache_time = get_cache(cache_key)
    max_age_sec = 600  # 10 dakika
    from datetime import datetime
    from dateutil import parser as dtparser
    if cache_data:
        cache_dt = dtparser.parse(cache_time)
        if (datetime.utcnow() - cache_dt).total_seconds() < max_age_sec:
            app.logger.info(f"Returning cached pipelines for {project_name} (age: {(datetime.utcnow() - cache_dt).total_seconds()}s)")
            return jsonify(json.loads(cache_data))
    try:
        pipelines = get_pipelines_data(project_name)
        set_cache(cache_key, json.dumps(pipelines))
        return jsonify(pipelines)
    except Exception as e:
        app.logger.error(f"Error fetching pipelines for {project_name}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/projects/<project_name>/releases', methods=['GET'])
def get_project_releases(project_name):
    """
    Returns release definitions for a given project, with SQLite caching (10dk).
    """
    import json
    cache_key = f"releases-{project_name}"
    cache_data, cache_time = get_cache(cache_key)
    max_age_sec = 600  # 10 dakika
    from datetime import datetime
    from dateutil import parser as dtparser
    if cache_data:
        cache_dt = dtparser.parse(cache_time)
        if (datetime.utcnow() - cache_dt).total_seconds() < max_age_sec:
            app.logger.info(f"Returning cached releases for {project_name} (age: {(datetime.utcnow() - cache_dt).total_seconds()}s)")
            return jsonify(json.loads(cache_data))
    try:
        releases = get_releases_data(project_name)
        set_cache(cache_key, json.dumps(releases))
        return jsonify(releases)
    except Exception as e:
        app.logger.error(f"Error fetching releases for {project_name}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/projects/<project_name>/teams', methods=['GET'])
def get_project_teams(project_name):
    """
    Returns teams for a given project, with SQLite caching (10dk).
    """
    import json
    cache_key = f"teams-{project_name}"
    cache_data, cache_time = get_cache(cache_key)
    max_age_sec = 600  # 10 dakika
    from datetime import datetime
    from dateutil import parser as dtparser
    if cache_data:
        cache_dt = dtparser.parse(cache_time)
        if (datetime.utcnow() - cache_dt).total_seconds() < max_age_sec:
            app.logger.info(f"Returning cached teams for {project_name} (age: {(datetime.utcnow() - cache_dt).total_seconds()}s)")
            return jsonify(json.loads(cache_data))
    try:
        # Azure DevOps REST API: https://dev.azure.com/{org}/{project}/_apis/teams?api-version=7.1-preview.3
        org_url = get_devops_org_url()
        api_version = '7.1-preview.3'
        url = f"{org_url}/{project_name}/_apis/teams?api-version={api_version}"
        response = requests.get(url, headers=get_headers())
        response.raise_for_status()
        teams = response.json().get('value', [])
        set_cache(cache_key, json.dumps(teams))
        return jsonify(teams)
    except Exception as e:
        app.logger.error(f"Error fetching teams for {project_name}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/projects/<project_name>/teams/<team_id>/members', methods=['GET'])
def get_team_members(project_name, team_id):
    """
    Returns members for a given team in a project, with SQLite caching (10dk).
    """
    import json
    cache_key = f"team-members-{project_name}-{team_id}"
    cache_data, cache_time = get_cache(cache_key)
    max_age_sec = 600  # 10 dakika
    from datetime import datetime
    from dateutil import parser as dtparser
    if cache_data:
        cache_dt = dtparser.parse(cache_time)
        if (datetime.utcnow() - cache_dt).total_seconds() < max_age_sec:
            app.logger.info(f"Returning cached team members for {project_name}/{team_id} (age: {(datetime.utcnow() - cache_dt).total_seconds()}s)")
            return jsonify(json.loads(cache_data))
    try:
        org_url = get_devops_org_url()
        api_version = '7.1-preview.1'
        url = f"{org_url}/{project_name}/_apis/teams/{team_id}/members?api-version={api_version}"
        response = requests.get(url, headers=get_headers())
        response.raise_for_status()
        members = response.json().get('value', [])
        set_cache(cache_key, json.dumps(members))
        return jsonify(members)
    except Exception as e:
        app.logger.error(f"Error fetching team members for {project_name}/{team_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/deployments-by-environment', methods=['GET'])
def deployments_by_environment():
    """
    Returns monthly deployment counts by environment (Test, Staging, Production) for each project.
    """
    from collections import defaultdict
    import json
    try:
        org_url_full = get_devops_org_url()
        organization_name = org_url_full.split('/')[-1]
        projects = get_projects_data()
        now_utc = datetime.utcnow()
        start_utc = now_utc - timedelta(days=30)
        start_date_iso = start_utc.isoformat() + "Z"
        end_date_iso = now_utc.isoformat() + "Z"
        result = []
        for project in projects:
            project_name = project.get('name')
            if not project_name:
                continue
            deployments = get_all_deployments_for_project(organization_name, project_name, start_date_iso, end_date_iso)
            env_counts = defaultdict(int)
            for dep in deployments:
                env_name = None
                # Try to get environment name from deployment
                if dep.get('releaseEnvironment', {}).get('name'):
                    env_name = dep['releaseEnvironment']['name']
                elif dep.get('release', {}).get('environmentName'):
                    env_name = dep['release']['environmentName']
                # Normalize environment name
                if env_name:
                    env_lower = env_name.lower()
                    if 'test' in env_lower:
                        env_counts['Test'] += 1
                    elif 'stag' in env_lower:
                        env_counts['Staging'] += 1
                    elif 'prod' in env_lower:
                        env_counts['Production'] += 1
                    else:
                        env_counts[env_name] += 1
                else:
                    env_counts['Unknown'] += 1
            result.append({
                'project': project_name,
                'Test': env_counts.get('Test', 0),
                'Staging': env_counts.get('Staging', 0),
                'Production': env_counts.get('Production', 0)
            })
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error in deployments_by_environment: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/projects/<project_name>/deployments-by-environment', methods=['GET'])
def project_deployments_by_environment(project_name):
    from collections import defaultdict
    import json
    from datetime import datetime
    from dateutil import parser as dtparser
    cache_key = f"deployments-env-{project_name}"
    now = time.time()
    # 1. In-memory cache kontrolü
    if cache_key in metrics_cache and now - metrics_cache[cache_key]['time'] < metrics_cache_expiry:
        app.logger.info(f'[CACHE] Returning in-memory cached deployments-env for {cache_key}')
        return jsonify(metrics_cache[cache_key]['data'])
    # 2. SQLite cache kontrolü
    cache_data, cache_time = get_cache(cache_key)
    if cache_data:
        cache_dt = dtparser.parse(cache_time)
        if (datetime.utcnow() - cache_dt).total_seconds() < metrics_cache_expiry:
            app.logger.info(f'[CACHE] Returning SQLite cached deployments-env for {cache_key}')
            metrics_cache[cache_key] = {'data': json.loads(cache_data), 'time': now}
            return jsonify(json.loads(cache_data))
    try:
        org_url_full = get_devops_org_url()
        organization_name = org_url_full.split('/')[-1]
        now_utc = datetime.utcnow()
        start_utc = now_utc - timedelta(days=30)
        start_date_iso = start_utc.isoformat() + "Z"
        end_date_iso = now_utc.isoformat() + "Z"
        deployments = get_all_deployments_for_project(organization_name, project_name, start_date_iso, end_date_iso)
        env_counts = defaultdict(int)
        for dep in deployments:
            env_name = None
            if dep.get('releaseEnvironment', {}).get('name'):
                env_name = dep['releaseEnvironment']['name']
            elif dep.get('release', {}).get('environmentName'):
                env_name = dep['release']['environmentName']
            if env_name:
                env_lower = env_name.lower()
                if 'test' in env_lower:
                    env_counts['Test'] += 1
                elif 'stag' in env_lower:
                    env_counts['Staging'] += 1
                elif 'prod' in env_lower:
                    env_counts['Production'] += 1
                else:
                    env_counts[env_name] += 1
            else:
                env_counts['Unknown'] += 1
        result = {
            'project': project_name,
            'Test': env_counts.get('Test', 0),
            'Staging': env_counts.get('Staging', 0),
            'Production': env_counts.get('Production', 0),
            'deployment_frequency': round(len(deployments) / 30, 2) if deployments else 0.0
        }
        # 3. Cache güncelle
        metrics_cache[cache_key] = {'data': result, 'time': now}
        set_cache(cache_key, json.dumps(result))
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error in project_deployments_by_environment: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # debug=True geliştirme sırasında daha fazla log ve otomatik yeniden yükleme sağlar.
    # Üretimde Gunicorn gibi bir WSGI sunucusu kullanılmalıdır.
    app.run(host='0.0.0.0', port=5000, debug=True)