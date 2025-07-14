# 🚀 SoundCloud Tracklist Extractor - Deployment Guide

This guide will help you deploy the SoundCloud Tracklist Extractor web application for **FREE** using various cloud platforms.

## 📋 Prerequisites

1. **ACRCloud Account** (Free tier available)
   - Sign up at [https://www.acrcloud.com/](https://www.acrcloud.com/)
   - Create a new project and get your API credentials
   - Free tier includes 1,000 recognitions per month

2. **Git Repository**
   - Fork or clone this repository
   - Push your code to GitHub/GitLab

## 🔧 Setup Instructions

### 1. Environment Variables Setup

Create a `.env` file in your project root with your ACRCloud credentials:

```bash
ACR_HOST=identify-eu-west-1.acrcloud.com
ACR_KEY=your_acr_access_key_here
ACR_SECRET=your_acr_secret_here
SECRET_KEY=your-secret-key-change-in-production
FLASK_ENV=production
```

### 2. File Structure

Ensure your project has this structure:

```
your-project/
├── app.py
├── downloader.py
├── splitter.py
├── recognizer.py
├── youtube_search.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env
├── .env.example
├── templates/
│   └── index.html
└── output/
    └── soundcloudtracks/
```

## 🌟 Free Deployment Options

### Option 1: Railway (Recommended - Easiest)

Railway offers $5 free credits monthly and easy deployment.

1. **Sign up at [Railway](https://railway.app/)**
2. **Connect your GitHub repository**
3. **Deploy:**
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Railway will auto-detect the Dockerfile

4. **Set Environment Variables:**
   - Go to your project → Variables tab
   - Add your ACR credentials:
     ```
     ACR_HOST=identify-eu-west-1.acrcloud.com
     ACR_KEY=your_acr_access_key_here
     ACR_SECRET=your_acr_secret_here
     SECRET_KEY=your-secret-key-change-in-production
     PORT=5000
     ```

5. **Deploy:**
   - Railway will automatically build and deploy
   - You'll get a public URL like `https://your-app.railway.app`

### Option 2: Render (Free Tier)

Render offers free hosting with some limitations.

1. **Sign up at [Render](https://render.com/)**
2. **Create a new Web Service:**
   - Connect your GitHub repository
   - Choose "Docker" as the environment
   - Set build command: `docker build -t app .`
   - Set start command: `docker run -p 10000:5000 app`

3. **Environment Variables:**
   - Add the same variables as above
   - Set `PORT=10000` (Render requirement)

4. **Deploy:**
   - Render will build and deploy automatically
   - Free tier includes 750 hours per month

### Option 3: Heroku (Free Tier Discontinued - Use Alternatives)

**Note:** Heroku discontinued free tier. Use Railway or Render instead.

### Option 4: Google Cloud Run (Free Tier)

Google Cloud Run offers 2 million requests per month for free.

1. **Install Google Cloud SDK**
2. **Build and push to Google Container Registry:**
   ```bash
   # Set your project ID
   export PROJECT_ID=your-project-id
   
   # Build and tag the image
   docker build -t gcr.io/$PROJECT_ID/soundcloud-extractor .
   
   # Push to registry
   docker push gcr.io/$PROJECT_ID/soundcloud-extractor
   ```

3. **Deploy to Cloud Run:**
   ```bash
   gcloud run deploy soundcloud-extractor \
     --image gcr.io/$PROJECT_ID/soundcloud-extractor \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars ACR_HOST=identify-eu-west-1.acrcloud.com \
     --set-env-vars ACR_KEY=your_acr_access_key_here \
     --set-env-vars ACR_SECRET=your_acr_secret_here \
     --set-env-vars SECRET_KEY=your-secret-key
   ```

### Option 5: Azure Container Instances (Free Credits)

Azure offers $200 free credits for new accounts.

1. **Create Azure Container Registry:**
   ```bash
   az acr create --resource-group myResourceGroup --name myRegistry --sku Basic
   ```

2. **Build and push:**
   ```bash
   az acr build --registry myRegistry --image soundcloud-extractor .
   ```

3. **Deploy to Container Instances:**
   ```bash
   az container create \
     --resource-group myResourceGroup \
     --name soundcloud-extractor \
     --image myRegistry.azurecr.io/soundcloud-extractor:latest \
     --dns-name-label soundcloud-extractor \
     --ports 5000 \
     --environment-variables \
       ACR_HOST=identify-eu-west-1.acrcloud.com \
       ACR_KEY=your_acr_access_key_here \
       ACR_SECRET=your_acr_secret_here \
       SECRET_KEY=your-secret-key
   ```

## 🛠️ Local Development

### Using Docker Compose

1. **Clone the repository:**
   ```bash
   git clone your-repo-url
   cd soundcloud-tracklist-extractor
   ```

2. **Create `.env` file with your credentials**

3. **Run with Docker Compose:**
   ```bash
   docker-compose up --build
   ```

4. **Access the application at `http://localhost:5000`**

### Manual Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install system dependencies:**
   ```bash
   # On Ubuntu/Debian
   sudo apt-get install ffmpeg
   
   # On macOS
   brew install ffmpeg
   
   # Install scdl
   npm install -g scdl
   ```

3. **Create directories:**
   ```bash
   mkdir -p output/soundcloudtracks
   mkdir -p templates
   ```

4. **Run the application:**
   ```bash
   python app.py
   ```

## 🔒 Security Considerations

1. **Never commit `.env` file to version control**
2. **Use strong SECRET_KEY in production**
3. **Enable HTTPS in production**
4. **Consider rate limiting for public deployments**
5. **Monitor ACRCloud usage to avoid quota exceeded**

## 📝 Environment Variables Reference

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `ACR_HOST` | ACRCloud API host | Yes | identify-eu-west-1.acrcloud.com |
| `ACR_KEY` | ACRCloud access key | Yes | - |
| `ACR_SECRET` | ACRCloud secret key | Yes | - |
| `SECRET_KEY` | Flask secret key | Yes | - |
| `FLASK_ENV` | Flask environment | No | production |
| `PORT` | Port number | No | 5000 |
| `YOUTUBE_API_KEY` | YouTube Data API key | No | - |

## 🐛 Troubleshooting

### Common Issues

1. **"No module named 'scdl'" error:**
   - Install scdl globally: `npm install -g scdl`
   - Ensure Node.js is installed

2. **ACRCloud authentication errors:**
   - Verify your credentials are correct
   - Check if you've exceeded your monthly quota

3. **Docker build fails:**
   - Ensure Docker has enough memory allocated
   - Check internet connection for package downloads

4. **YouTube search not working:**
   - This is expected behavior due to scraping limitations
   - Consider implementing YouTube Data API for better reliability

### Performance Tips

1. **Use smaller chunk durations (5-8 seconds) for better accuracy**
2. **Monitor ACRCloud quota usage**
3. **Consider caching YouTube search results**
4. **Use CDN for static assets in production**

## 📊 Cost Estimation

### Free Tier Limits

- **ACRCloud:** 1,000 recognitions/month
- **Railway:** $5 credit monthly (~750 hours)
- **Render:** 750 hours/month
- **Google Cloud Run:** 2M requests/month
- **Azure:** $200 credit for new accounts

### Usage Calculation

For a 60-minute mix with 10-second chunks:
- Chunks: 360 (60 minutes × 6 chunks per minute)
- ACRCloud requests: 360
- Monthly capacity: ~2-3 mixes with free tier

## 🚀 Going to Production

### Scaling Considerations

1. **Use a proper database** (PostgreSQL, MySQL) for storing results
2. **Implement user authentication** and rate limiting
3. **Add caching** (Redis) for YouTube searches
4. **Use a proper message queue** (Celery, RQ) for background processing
5. **Add monitoring** and logging
6. **Implement file cleanup** for temporary audio files

### Recommended Architecture

```
User → Load Balancer → Web App → Message Queue → Worker Processes
                                      ↓
                               Database + File Storage
```

## 📞 Support

If you encounter issues:

1. Check the logs in your deployment platform
2. Verify environment variables are set correctly
3. Test ACRCloud credentials separately
4. Ensure all dependencies are installed

## 🎉 Success!

Your SoundCloud Tracklist Extractor should now be running! Users can:

1. Paste SoundCloud URLs
2. Watch real-time progress
3. View extracted tracklists
4. Click YouTube links to listen to identified tracks

Enjoy your new DJ tool! 🎵