import requests
import base64

GITHUB_API_BASE_URL = "https://api.github.com"


def create_github_repo(access_token: str, repo_name: str, private: bool = False) -> str:
    """
    Creates a GitHub repository with the given name.

    :param access_token: GitHub personal access token.
    :param repo_name: Name of the repository.
    :param private: Whether the repo should be private (default: False).
    :return: Repository URL.
    :raises: Exception if repository creation fails.
    """
    url = f"{GITHUB_API_BASE_URL}/user/repos"
    headers = {"Authorization": f"token {access_token}"}
    data = {"name": repo_name, "private": private}

    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 201:
        return response.json()["html_url"]
    else:
        raise Exception(f"GitHub repository creation failed: {response.json()}")


def upload_file_to_github(
    access_token: str, repo_name: str, file_path: str, content: str
) -> str:
    """
    Uploads a file to a GitHub repository.

    :param access_token: GitHub personal access token.
    :param repo_name: Name of the repository.
    :param file_path: Path inside the repo (e.g., "docs/roadmap.md").
    :param content: File content to upload.
    :return: Success message.
    :raises: Exception if file upload fails.
    """
    # Get GitHub username from the access token
    headers = {"Authorization": f"token {access_token}"}
    user_response = requests.get(f"{GITHUB_API_BASE_URL}/user", headers=headers)

    if user_response.status_code != 200:
        raise Exception("Failed to fetch GitHub user details")

    username = user_response.json().get("login")

    # Construct file upload URL
    url = f"{GITHUB_API_BASE_URL}/repos/{username}/{repo_name}/contents/{file_path}"

    file_content = base64.b64encode(content.encode()).decode()
    data = {"message": f"Added {file_path}", "content": file_content, "branch": "main"}

    response = requests.put(url, json=data, headers=headers)

    if response.status_code == 201:
        return f"{file_path} uploaded successfully"
    else:
        raise Exception(f"Failed to upload file: {response.json()}")


def get_github_access_token(code: str):
    url = "https://github.com/login/oauth/access_token"
    headers = {"Accept": "application/json"}
    data = {
        "client_id": GITHUB_CLIENT_ID,
        "client_secret": GITHUB_CLIENT_SECRET,
        "code": code,
        "redirect_uri": GITHUB_REDIRECT_URI,
    }

    response = requests.post(url, headers=headers, data=data)
    return response.json().get("access_token")
