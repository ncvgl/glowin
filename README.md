# LinkedIn Headshot Generator

A simple, single-flow web application that generates professional headshots from LinkedIn profile pictures using Google's Vertex AI Imagen.

## Features

- LinkedIn OAuth authentication
- Pull profile image automatically
- Generate 4 professional headshot variants:
  - Corporate Professional
  - Creative Professional
  - Executive
  - Approachable Professional
- 1:1 aspect ratio (square) headshots
- Download as PNG
- Slack-inspired modern UI

## Architecture

- **Backend**: FastAPI (Python)
- **Frontend**: React with Vite
- **AI**: Vertex AI Imagen for image generation
- **Deployment**: Google Cloud Run with Docker
- **Auth**: LinkedIn OAuth 2.0

## Prerequisites

1. **Google Cloud Project**
   - Enable Vertex AI API
   - Enable Cloud Run API
   - Enable Cloud Build API (for automated deployment)
   - Set up Application Default Credentials (ADC)

2. **LinkedIn Developer App**
   - Create an app at [LinkedIn Developers](https://www.linkedin.com/developers/)
   - Add OAuth 2.0 credentials
   - Set redirect URI: `https://your-app-url.run.app/auth/callback`
   - Required scopes: `openid`, `profile`, `email`, `w_member_social`

## Local Development

### 1. Clone and Setup

```bash
cd glowin
cp .env.example .env
```

### 2. Configure Environment Variables

Edit `.env` with your credentials:

```env
LINKEDIN_CLIENT_ID=your-linkedin-client-id
LINKEDIN_CLIENT_SECRET=your-linkedin-client-secret
LINKEDIN_REDIRECT_URI=http://localhost:8000/auth/callback
SESSION_SECRET=your-random-secret-key
GCP_PROJECT_ID=your-gcp-project-id
GCP_LOCATION=us-central1
PORT=8000
```

### 3. Install Backend Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Install Frontend Dependencies

```bash
cd ../frontend
npm install
```

### 5. Run Development Servers

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Visit `http://localhost:5173` (Vite dev server with proxy to backend)

## Cloud Run Deployment

### Option 1: Using Cloud Build (Recommended)

1. **Set your GCP project:**
```bash
gcloud config set project YOUR_PROJECT_ID
```

2. **Update `cloudbuild.yaml`** with your settings (region, env vars)

3. **Deploy using Cloud Build:**
```bash
gcloud builds submit --config cloudbuild.yaml
```

4. **Set environment variables in Cloud Run:**
```bash
gcloud run services update linkedin-headshot-generator \
  --region=us-central1 \
  --set-env-vars="LINKEDIN_CLIENT_ID=your-id" \
  --set-env-vars="LINKEDIN_CLIENT_SECRET=your-secret" \
  --set-env-vars="LINKEDIN_REDIRECT_URI=https://your-service-url.run.app/auth/callback" \
  --set-env-vars="SESSION_SECRET=your-secret" \
  --set-env-vars="GCP_PROJECT_ID=your-project-id" \
  --set-env-vars="GCP_LOCATION=us-central1"
```

### Option 2: Manual Docker Build and Deploy

1. **Build the Docker image:**
```bash
docker build -t gcr.io/YOUR_PROJECT_ID/linkedin-headshot-generator .
```

2. **Push to Google Container Registry:**
```bash
docker push gcr.io/YOUR_PROJECT_ID/linkedin-headshot-generator
```

3. **Deploy to Cloud Run:**
```bash
gcloud run deploy linkedin-headshot-generator \
  --image gcr.io/YOUR_PROJECT_ID/linkedin-headshot-generator \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="LINKEDIN_CLIENT_ID=your-id,LINKEDIN_CLIENT_SECRET=your-secret,LINKEDIN_REDIRECT_URI=https://your-service-url.run.app/auth/callback,SESSION_SECRET=your-secret,GCP_PROJECT_ID=your-project-id,GCP_LOCATION=us-central1"
```

### Post-Deployment

1. Get your Cloud Run service URL:
```bash
gcloud run services describe linkedin-headshot-generator \
  --region=us-central1 \
  --format='value(status.url)'
```

2. Update LinkedIn app redirect URI with your Cloud Run URL + `/auth/callback`

3. Update the `LINKEDIN_REDIRECT_URI` environment variable in Cloud Run

## Project Structure

```
glowin/
├── backend/
│   ├── main.py              # FastAPI application
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.jsx         # Main React component
│   │   ├── App.css         # Slack-inspired styles
│   │   ├── index.css       # Global styles
│   │   └── main.jsx        # React entry point
│   ├── index.html          # HTML template
│   ├── package.json        # Node dependencies
│   └── vite.config.js      # Vite configuration
├── Dockerfile              # Multi-stage Docker build
├── cloudbuild.yaml         # Cloud Build configuration
├── .env.example            # Environment template
└── README.md              # This file
```

## How It Works

1. **User Authentication**
   - User clicks "Sign in with LinkedIn"
   - OAuth flow redirects to LinkedIn
   - User authorizes the app
   - App receives access token and profile data

2. **Image Processing**
   - Profile picture is downloaded from LinkedIn
   - Image is cropped to 1:1 aspect ratio (1024x1024)
   - Original image is prepared for AI processing

3. **AI Generation**
   - Vertex AI Imagen model (`imagegeneration@006`) is used
   - 4 different professional style prompts are applied
   - Each variant is generated with unique parameters
   - Images are stored in ephemeral session storage

4. **Download**
   - User can view all 4 generated headshots
   - Click any image or download button to save as PNG
   - Files are named based on the style

## API Endpoints

### Authentication
- `GET /auth/login` - Initiate LinkedIn OAuth flow
- `GET /auth/callback` - Handle OAuth callback

### API
- `GET /api/profile?session={id}` - Get user profile data
- `POST /api/generate-headshots` - Generate professional headshots
- `GET /api/image/{image_id}?session={id}` - Download/view generated image

## Security Considerations

- Sessions are ephemeral (in-memory only)
- No persistent database
- Session IDs are UUIDs
- LinkedIn OAuth credentials should be kept secure
- Use HTTPS in production (Cloud Run provides this automatically)
- Consider adding rate limiting for production use

## Troubleshooting

### "Failed to get access token"
- Verify LinkedIn OAuth credentials
- Check redirect URI matches exactly (including protocol)
- Ensure LinkedIn app is not in development mode limits

### "Failed to generate headshots"
- Verify Vertex AI API is enabled
- Check ADC is configured correctly
- Ensure the service account has Vertex AI permissions
- Check Cloud Run logs: `gcloud run logs read linkedin-headshot-generator --region=us-central1`

### Image generation errors
- Imagen model requires the image to be appropriate for transformation
- Check if the LinkedIn profile picture is accessible
- Verify model name is correct (`imagegeneration@006`)

## Future Enhancements

- Add more style options
- Support for custom aspect ratios
- Batch processing
- Image history (with database)
- Better error handling and retry logic
- Progress indicators during generation
- A/B testing different prompts

## License

MIT

## Support

For issues and questions, please open an issue in the repository.
