import os
import uuid
import io
import base64
from typing import Dict, Optional
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import httpx
from PIL import Image
from vertexai.preview.vision_models import ImageGenerationModel
import vertexai

app = FastAPI(title="LinkedIn Headshot Generator")

# Session storage (ephemeral - in-memory)
sessions: Dict[str, Dict] = {}

# Configure session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET", "your-secret-key-change-in-production")
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# LinkedIn OAuth configuration
LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID", "your-linkedin-client-id")
LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET", "your-linkedin-client-secret")
LINKEDIN_REDIRECT_URI = os.getenv("LINKEDIN_REDIRECT_URI", "http://localhost:8000/auth/callback")

# Configure Vertex AI with ADC (Application Default Credentials)
# Project ID will be auto-detected from environment when running on Cloud Run
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "your-project-id")
LOCATION = os.getenv("GCP_LOCATION", "us-central1")

try:
    vertexai.init(project=PROJECT_ID, location=LOCATION)
except Exception as e:
    print(f"Warning: Vertex AI initialization failed: {e}")

# Professional headshot styles
HEADSHOT_STYLES = [
    {
        "name": "Corporate Professional",
        "prompt": "Transform this profile photo into a polished corporate headshot with professional studio lighting, neutral background, business attire, confident expression, high-resolution quality"
    },
    {
        "name": "Creative Professional",
        "prompt": "Transform this profile photo into a modern creative professional headshot with artistic lighting, contemporary background, smart casual look, approachable expression, high-resolution quality"
    },
    {
        "name": "Executive",
        "prompt": "Transform this profile photo into an executive-level headshot with premium studio lighting, sophisticated neutral background, formal business attire, authoritative yet friendly expression, ultra high-resolution quality"
    },
    {
        "name": "Approachable Professional",
        "prompt": "Transform this profile photo into a warm and approachable professional headshot with natural lighting, soft background, business casual attire, friendly smile, high-resolution quality"
    }
]


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "app": "LinkedIn Headshot Generator"}


@app.get("/auth/login")
async def login():
    """Initiate LinkedIn OAuth flow"""
    state = str(uuid.uuid4())
    sessions[state] = {"state": state}

    linkedin_auth_url = (
        f"https://www.linkedin.com/oauth/v2/authorization"
        f"?response_type=code"
        f"&client_id={LINKEDIN_CLIENT_ID}"
        f"&redirect_uri={LINKEDIN_REDIRECT_URI}"
        f"&state={state}"
        f"&scope=openid profile email w_member_social"
    )

    return {"auth_url": linkedin_auth_url, "state": state}


@app.get("/auth/callback")
async def auth_callback(code: str, state: str):
    """Handle LinkedIn OAuth callback"""
    if state not in sessions:
        raise HTTPException(status_code=400, detail="Invalid state")

    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://www.linkedin.com/oauth/v2/accessToken",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": LINKEDIN_REDIRECT_URI,
                "client_id": LINKEDIN_CLIENT_ID,
                "client_secret": LINKEDIN_CLIENT_SECRET,
            },
        )

        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get access token")

        token_data = token_response.json()
        access_token = token_data["access_token"]

        # Get user profile
        profile_response = await client.get(
            "https://api.linkedin.com/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if profile_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get user profile")

        profile_data = profile_response.json()

        # Store session data
        session_id = str(uuid.uuid4())
        sessions[session_id] = {
            "profile": profile_data,
            "profile_image_url": profile_data.get("picture"),
            "access_token": access_token
        }

    # Redirect to frontend with session ID
    return RedirectResponse(url=f"/?session={session_id}")


@app.get("/api/profile")
async def get_profile(session: str):
    """Get user profile data"""
    if session not in sessions:
        raise HTTPException(status_code=401, detail="Invalid session")

    session_data = sessions[session]
    return {
        "name": session_data["profile"].get("name"),
        "email": session_data["profile"].get("email"),
        "picture": session_data["profile"].get("picture")
    }


@app.post("/api/generate-headshots")
async def generate_headshots(request: Request):
    """Generate professional headshots using Vertex AI Imagen"""
    data = await request.json()
    session_id = data.get("session")

    if session_id not in sessions:
        raise HTTPException(status_code=401, detail="Invalid session")

    session_data = sessions[session_id]
    profile_image_url = session_data.get("profile_image_url")

    if not profile_image_url:
        raise HTTPException(status_code=400, detail="No profile image found")

    # Download the LinkedIn profile image
    async with httpx.AsyncClient() as client:
        img_response = await client.get(profile_image_url)
        if img_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to download profile image")

        # Load and prepare image
        original_image = Image.open(io.BytesIO(img_response.content))

        # Resize to square 1:1 aspect ratio if needed
        size = min(original_image.size)
        left = (original_image.width - size) // 2
        top = (original_image.height - size) // 2
        original_image = original_image.crop((left, top, left + size, top + size))
        original_image = original_image.resize((1024, 1024), Image.Resampling.LANCZOS)

    # Store original image bytes
    original_bytes = io.BytesIO()
    original_image.save(original_bytes, format='PNG')
    original_bytes.seek(0)

    # Generate headshots with Vertex AI Imagen
    model = ImageGenerationModel.from_pretrained("imagegeneration@006")
    generated_images = []

    for idx, style in enumerate(HEADSHOT_STYLES):
        try:
            # Generate image with Imagen using edit mode
            images = model.edit_image(
                base_image_bytes=original_bytes.getvalue(),
                prompt=style["prompt"],
                number_of_images=1,
                guidance_scale=15,
                seed=42 + idx  # Different seed for each style
            )

            if images and len(images) > 0:
                # Convert generated image to bytes
                img_byte_arr = io.BytesIO()
                images[0]._pil_image.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)

                image_id = str(uuid.uuid4())

                # Store image in session
                if "images" not in sessions[session_id]:
                    sessions[session_id]["images"] = {}

                sessions[session_id]["images"][image_id] = {
                    "data": img_byte_arr.getvalue(),
                    "style": style["name"]
                }

                generated_images.append({
                    "style": style["name"],
                    "status": "generated",
                    "image_id": image_id
                })
            else:
                generated_images.append({
                    "style": style["name"],
                    "status": "error",
                    "error": "No image generated"
                })

        except Exception as e:
            print(f"Error generating {style['name']}: {str(e)}")
            generated_images.append({
                "style": style["name"],
                "status": "error",
                "error": str(e)
            })

    return {"images": generated_images}


@app.get("/api/image/{image_id}")
async def get_image(image_id: str, session: str):
    """Get a generated headshot image"""
    if session not in sessions:
        raise HTTPException(status_code=401, detail="Invalid session")

    session_data = sessions[session]
    if "images" not in session_data or image_id not in session_data["images"]:
        raise HTTPException(status_code=404, detail="Image not found")

    image_data = session_data["images"][image_id]

    return StreamingResponse(
        io.BytesIO(image_data["data"]),
        media_type="image/png",
        headers={
            "Content-Disposition": f'attachment; filename="headshot_{image_data["style"].replace(" ", "_")}.png"'
        }
    )


# Mount static files for production (when static directory exists)
if os.path.exists("static"):
    app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str):
        """Serve frontend static files and SPA routing"""
        # Don't serve API or auth routes
        if full_path.startswith(("auth/", "api/")):
            raise HTTPException(status_code=404, detail="Not found")

        # Try to serve specific file
        file_path = os.path.join("static", full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)

        # Default to index.html for SPA routing
        return FileResponse("static/index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
