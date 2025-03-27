from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from fastapi.responses import ORJSONResponse
from app.database import get_db
from app.utils.user import get_current_user, get_user, require_auth
from app.settings import settings
from app.models import GenerateRoadmapSchema, User, Roadmap
from app.utils.google import is_google_token_active, is_google_token_valid
from mistralai import Mistral
from openai import OpenAI
from fastapi import HTTPException
import requests
import base64


router = APIRouter(prefix="/roadmaps", tags=["Roadmaps"])


@router.post("/generate")
@require_auth
def generate_roadmap(
    roadmap_request: GenerateRoadmapSchema,
    request: Request,
    db: Session = Depends(get_db),
):
    roadmap_prompt = f"""
        Generate a structured course roadmap based on the following criteria:
        - **Topic:** {roadmap_request.topic} Roadmap
        - **Level:** {roadmap_request.level}
        - **Format:** Strictly Markdown format with bullet points and bold headers.
        - **Structure:**
            - Course title (in bold)
            - Modules (in bold) with key topics as bullet points.
        - **Formatting Rules:**
            - Each module must have a title in `**bold**`
            - Key topics within modules must be in `- ` bullet points.
            - No introduction, explanation, or additional text.
            - Output should **only** contain the structured roadmap.
            - No title, subtitles, or descriptions beyond the roadmap itself.

        ### **Example Format:**
            # Course Title
            - ## Module 1: Name
                - [ ] Topic 1 
                - [ ] Topic 2

            - ## Module 2: Name
                - [ ] Topic 1
                - [ ]Topic 2

    """
    try:
        user = request.state.user
        if not user:
            raise HTTPException(status_code=401, detail="Authentication required")

        client = get_client()
        model = (
            settings.MISTRAL_AI_MODEL if settings.USE_OPENAI else settings.OPENAI_MODEL
        )
        chat_response = client.chat.complete(
            model=model, messages=[{"role": "user", "content": roadmap_prompt}]
        )
        roadmap_content = chat_response.choices[0].message.content
        roadmap = Roadmap(
            title=f"{roadmap_request.topic} {roadmap_request.level} Roadmap",
            content=roadmap_content,
            user_id=user.id,
        )
        db.add(roadmap)
        db.commit()
        db.refresh(roadmap)
        data = {"message": "Success", "roadmap": roadmap.id}
        return ORJSONResponse(content=data, status_code=200)
    except Exception as e:
        return {"error": str(e)}, 400


def get_client():
    if settings.USE_OPENAI:
        client = Mistral(api_key=settings.MISTRAL_API_KEY)
    else:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return client


@router.get("/{roadmap_id}")
@require_auth
def get_roadmap(roadmap_id: int, request: Request, db: Session = Depends(get_db)):
    try:
        user = request.state.user
        if not user:
            raise HTTPException(status_code=401, detail="Authentication required")

        roadmap = (
            db.query(Roadmap)
            .filter(Roadmap.id == roadmap_id, User.id == user.id)
            .first()
        )

        if not roadmap:
            raise HTTPException(status_code=404, detail="Roadmap not found")
        data = {"roadmap": RoadmapResponseSchema.from_orm(roadmap).model_dump()}
        return ORJSONResponse(content=data, status_code=200)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{roadmap_id}/save-to-github")
@require_auth
def save_to_github(
    roadmap_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Saves a roadmap to a GitHub repository"""
    current_user = request.state.user

    # Check user authentication
    if current_user["id"] != user_id:
        raise HTTPException(status_code=403, detail="Authentication required")

    # Fetch roadmap from DB
    roadmap = (
        db.query(Roadmap)
        .filter(Roadmap.id == roadmap_id, User.id == current_user["id"])
        .first()
    )

    if not roadmap:
        raise HTTPException(status_code=404, detail="Roadmap not found")

    access_token = user.github_token
    if not access_token:
        raise HTTPException(status_code=403, detail="GitHub not linked")

    # Get GitHub username
    headers = {
        "Authorization": f"token {access_token}",
        "Accept": "application/vnd.github.v3+json",
    }
    user_response = requests.get("https://api.github.com/user", headers=headers)
    if user_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch GitHub user")

    github_username = user_response.json()["login"]

    repo_name = (
        f"{roadmap.title.replace(' ', '-').lower()}-roadmap"
        if roadmap.title
        else "ai-roadmap"
    )
    repo_url = "https://api.github.com/user/repos"

    repo_data = {
        "name": repo_name,
        "description": "AI-generated roadmap",
        "private": False,
    }
    repo_response = requests.post(repo_url, json=repo_data, headers=headers)

    if repo_response.status_code != 201 and repo_response.status_code != 422:
        raise HTTPException(status_code=400, detail="Failed to create repository")

    def get_file_sha(file_name: str):
        file_url = f"https://api.github.com/repos/{github_username}/{repo_name}/contents/{file_name}"
        response = requests.get(file_url, headers=headers)

        if response.status_code == 200:
            return response.json()["sha"]  # Return existing file SHA for updates
        return None  # File does not exist, so we can create a new one

    # Function to upload or update a file
    def upload_file(file_name: str, content: str):
        file_url = f"https://api.github.com/repos/{github_username}/{repo_name}/contents/{file_name}"
        file_content = base64.b64encode(content.encode()).decode()

        file_data = {
            "message": (
                f"Updated {file_name}"
                if get_file_sha(file_name)
                else f"Added {file_name}"
            ),
            "content": file_content,
            "branch": "main",
        }

        sha = get_file_sha(file_name)
        if sha:
            file_data["sha"] = sha  # Include SHA if updating an existing file

        file_response = requests.put(file_url, json=file_data, headers=headers)
        if file_response.status_code not in [200, 201]:
            raise HTTPException(status_code=400, detail=f"Failed to upload {file_name}")

    # Generate README.md content
    readme_content = f"""# {repo_name}\n\n## Roadmap\n\nSee [ROADMAP.md](./ROADMAP.md) for details. \n\nGenerated by AI Roadmap Generator\n"""

    # Upload README.md
    upload_file("README.md", readme_content)

    # Upload ROADMAP.md
    upload_file("ROADMAP.md", roadmap.content)
    data = {
        "message": "Roadmap saved to GitHub",
        "repo_url": f"https://github.com/{github_username}/{repo_name}",
    }
    return ORJSONResponse(content=data, status_code=200)


@router.delete("/{roadmap_id}")
@require_auth
def delete_roadmap(roadmap_id: int, request: Request, db: Session = Depends(get_db)):
    current_user = request.state.user

    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    roadmap = (
        db.query(Roadmap)
        .filter(Roadmap.id == roadmap_id, Roadmap.user_id == current_user["id"])
        .first()
    )
    if not roadmap:
        raise HTTPException(status_code=404, detail="Roadmap not found")

    db.delete(roadmap)
    db.commit()
    data = {"message": "Roadmap deleted"}
    return ORJSONResponse(content=data, status_code=200)


@router.post("/{roadmap_id}/upload-to-google-docs")
@require_auth
def save_google_docs(
    roadmap_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    user = request.state.user

    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")

    access_token = user.google_oauth_token
    if not access_token:
        raise HTTPException(status_code=401, detail="Google authentication required")

    if not is_google_token_active(access_token) or not is_google_token_valid(
        access_token
    ):
        return HTTPException(
            status_code=400, detail="Oauth token is invalid or expired"
        )

    roadmap = db.query(Roadmap).filter(Roadmap.id == roadmap_id).first()
    if not roadmap:
        raise HTTPException(status_code=404, detail="Roadmap not found")

    # TODO: Valid google access token

    url = "https://docs.googleapis.com/v1/documents"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    data = {"title": f"Roadmap: {roadmap.title if roadmap.title else 'AI Roadmap'}"}
    response = requests.post(url, headers=headers, json=data)

    if response.status_code != 200:
        error_detail = str(response.content)
        raise HTTPException(status_code=400, detail=error_detail)

    document_id = response.json().get("documentId")

    content_url = f"https://docs.googleapis.com/v1/documents/{document_id}:batchUpdate"
    data = format_roadmap_to_checklist(roadmap.content)
    content_response = requests.post(content_url, headers=headers, json=data)
    if content_response.status_code != 200:
        print("Google Docs API Error:", content_response.text)
        raise HTTPException(status_code=400, detail="Failed to insert roadmap content")
    return {"message": "Saved to Google Docs", "document_id": document_id}, 200


def format_roadmap_to_checklist(content: str):
    requests = []
    index = 1  # Start at index 1 for document positioning

    lines = content.split("\n")

    for line in lines:
        line = line.replace("*", "").replace("-", "").strip()

        if not line:
            continue

        start_index = index

        # print(line)
        if line.startswith("# "):
            text = line.replace("# ", "")
            requests.append(
                {"insertText": {"location": {"index": index}, "text": text + "\n\n"}}
            )
            requests.append(
                {
                    "updateParagraphStyle": {
                        "range": {
                            "startIndex": index,
                            "endIndex": start_index + len(text),
                        },
                        "paragraphStyle": {"namedStyleType": "TITLE"},
                        "fields": "namedStyleType",
                    }
                }
            )

        elif line.startswith("## "):
            text = line.replace("## ", "")
            requests.append(
                {"insertText": {"location": {"index": index}, "text": text + "\n\n"}}
            )
            requests.append(
                {
                    "updateParagraphStyle": {
                        "range": {
                            "startIndex": start_index,
                            "endIndex": start_index + len(text),
                        },
                        "paragraphStyle": {"namedStyleType": "HEADING_2"},
                        "fields": "namedStyleType",
                    }
                }
            )

        elif line.startswith("[ ]"):
            text = line.replace("[ ]", "")
            requests.append(
                {"insertText": {"location": {"index": index}, "text": text + "\n"}}
            )
            requests.append(
                {
                    "createParagraphBullets": {
                        "range": {
                            "startIndex": start_index,
                            "endIndex": start_index + len(text),
                        },
                        "bulletPreset": "BULLET_CHECKBOX",
                    }
                }
            )
        index += len(text) + 1
    return {"requests": requests}
