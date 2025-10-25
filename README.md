# LinkedIn Headshot Generator

FastAPI + React + Vertex AI Imagen. Generates 4 professional headshot variants from LinkedIn profile pictures.

## Prerequisites

**GCP:**
- Enable: Vertex AI API, Cloud Run API, Cloud Build API
- Configure ADC

**LinkedIn OAuth:**
- Create app at https://www.linkedin.com/developers/
- Scopes: `openid`, `profile`, `email`, `w_member_social`
- Redirect URI: `https://your-app-url.run.app/auth/callback`

## Local Setup

```bash
# Environment
cp .env.example .env
# Edit .env with credentials

# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python main.py

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
# Visit http://localhost:5173
```

## Deploy to Cloud Run

**Cloud Build:**
```bash
gcloud config set project YOUR_PROJECT_ID
gcloud builds submit --config cloudbuild.yaml

# Set env vars
gcloud run services update linkedin-headshot-generator \
  --region=us-central1 \
  --set-env-vars="LINKEDIN_CLIENT_ID=x,LINKEDIN_CLIENT_SECRET=x,LINKEDIN_REDIRECT_URI=https://x.run.app/auth/callback,SESSION_SECRET=x,GCP_PROJECT_ID=x,GCP_LOCATION=us-central1"
```

**Manual:**
```bash
docker build -t gcr.io/PROJECT_ID/linkedin-headshot-generator .
docker push gcr.io/PROJECT_ID/linkedin-headshot-generator
gcloud run deploy linkedin-headshot-generator \
  --image gcr.io/PROJECT_ID/linkedin-headshot-generator \
  --platform managed --region us-central1 --allow-unauthenticated \
  --set-env-vars="LINKEDIN_CLIENT_ID=x,LINKEDIN_CLIENT_SECRET=x,..."
```

**Post-deploy:**
- Get URL: `gcloud run services describe linkedin-headshot-generator --region=us-central1 --format='value(status.url)'`
- Update LinkedIn app redirect URI

## API Endpoints

```
GET  /auth/login                        - LinkedIn OAuth
GET  /auth/callback                     - OAuth callback
GET  /api/profile?session={id}          - User profile
POST /api/generate-headshots            - Generate images
GET  /api/image/{image_id}?session={id} - Download PNG
```

## Troubleshooting

**OAuth errors:** Check LinkedIn credentials, redirect URI exact match
**Generation fails:** Enable Vertex AI API, verify ADC, check service account permissions
**View logs:** `gcloud run logs read linkedin-headshot-generator --region=us-central1`
