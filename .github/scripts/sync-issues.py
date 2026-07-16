import os
import json
import urllib.request
import urllib.parse

def make_request(url, method="GET", data=None, headers=None):
    if headers is None:
        headers = {}
    
    req_data = None
    if data is not None:
        req_data = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.read().decode('utf-8')}")
        return e.code, None
    except Exception as e:
        print(f"Request failed: {e}")
        return 500, None

def main():
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    
    if not token or not repo:
        print("Missing GITHUB_TOKEN or GITHUB_REPOSITORY environment variable.")
        return

    headers = {
        "Authorization": f"token {token}",
        "User-Agent": "GitHub-Issue-Sync-Action",
        "Accept": "application/vnd.github.v3+json"
    }

    # 1. Carica le issue locali
    issues_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "issues.json")
    if not os.path.exists(issues_file_path):
        print(f"File not found: {issues_file_path}")
        return
        
    with open(issues_file_path, "r", encoding="utf-8") as f:
        local_issues = json.load(f)

    # 2. Recupera le issue esistenti su GitHub
    issues_url = f"https://api.github.com/repos/{repo}/issues?state=all&per_page=100"
    status, gh_issues = make_request(issues_url, headers=headers)
    
    if status != 200 or gh_issues is None:
        print(f"Failed to fetch issues from GitHub. Status code: {status}")
        return

    # Mappa le issue di GitHub per titolo per una ricerca più rapida
    # Escludiamo le pull request (le PR sono considerate issue dall'API ma contengono la chiave 'pull_request')
    gh_issues_map = {
        issue["title"].strip(): issue 
        for issue in gh_issues 
        if "pull_request" not in issue
    }

    print(f"Found {len(gh_issues_map)} existing issues/PRs on GitHub.")

    for local in local_issues:
        title = local["title"].strip()
        description = local["description"]
        status = local["status"]
        
        print(f"\nProcessing issue: '{title}' (status: {status})")

        if title in gh_issues_map:
            gh_issue = gh_issues_map[title]
            issue_number = gh_issue["number"]
            gh_state = gh_issue["state"]
            
            print(f"Found match on GitHub: Issue #{issue_number} is '{gh_state}'")

            if status == "resolved" and gh_state == "open":
                print(f"Closing GitHub issue #{issue_number}...")
                update_url = f"https://api.github.com/repos/{repo}/issues/{issue_number}"
                make_request(update_url, method="PATCH", data={"state": "closed"}, headers=headers)
            elif status == "open" and gh_state == "closed":
                print(f"Reopening GitHub issue #{issue_number}...")
                update_url = f"https://api.github.com/repos/{repo}/issues/{issue_number}"
                make_request(update_url, method="PATCH", data={"state": "open"}, headers=headers)
            else:
                print("Issue is already in sync.")
        else:
            if status == "open":
                print("Creating new issue on GitHub...")
                create_url = f"https://api.github.com/repos/{repo}/issues"
                make_request(create_url, method="POST", data={"title": title, "body": description}, headers=headers)
            else:
                print("Issue is resolved locally and does not exist on GitHub. Skipping creation.")

if __name__ == "__main__":
    main()
