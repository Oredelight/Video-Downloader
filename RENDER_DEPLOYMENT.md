# Render Deployment Guide

## Step 1: Prepare Your Repository
- Push all files (Dockerfile, docker-compose.yml, render.yaml) to GitHub
- Ensure your .gitignore excludes: `db.sqlite3`, `venv/`, `__pycache__/`, `.env`

## Step 2: Set Up on Render

### Option A: Using Blueprint (render.yaml) - RECOMMENDED
1. Go to https://dashboard.render.com/
2. Click "New" → "Blueprint"
3. Connect your GitHub repository
4. Render will read `render.yaml` automatically
5. Set environment variables (see Step 3)
6. Deploy

### Option B: Manual Setup
1. Go to https://dashboard.render.com/
2. Click "New" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: videodownloader
   - **Runtime**: Docker
   - **Build Command**: Leave empty (uses Dockerfile)
   - **Start Command**: Leave empty (uses Dockerfile)
   - **Plan**: Free (or Pro for better performance)
   - **Region**: Choose closest to your users

## Step 3: Environment Variables
In Render Dashboard → Settings → Environment Variables, add:

```
DEBUG=False
SECRET_KEY=your-very-secure-random-key-here
ALLOWED_HOSTS=videodownloader.onrender.com,localhost
RENDER=True
```

Generate a secure SECRET_KEY:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Step 4: Update Django Settings
Add the production settings from `render_settings_snippet.py` to your `settings.py`

## Step 5: Configure Persistent Data
1. In Render Dashboard → Settings → Disks
2. Add a persistent disk:
   - **Mount Path**: `/var/data`
   - **Size**: 1GB (free plan) or more

This directory persists between deployments for:
- Database (`db.sqlite3`)
- Media files (downloaded videos)
- Static files

## Step 6: First Deploy
1. Click "Deploy latest commit" or it deploys automatically
2. Check Logs tab for any errors
3. Wait for build to complete (~5-10 minutes)
4. Access your app at `https://videodownloader.onrender.com`

## Step 7: Run Migrations
Option A (Automatic): Add to render.yaml:
```yaml
preDeployCommand: "python manage.py migrate"
```

Option B (Manual): Via Render Shell
1. Click "Shell" tab
2. Run: `python manage.py migrate`
3. Run: `python manage.py createsuperuser` (optional)

## Important Considerations

### For Free Plan:
- ⏱️ Service spins down after 15 min of inactivity
- 📊 Limited resources (512MB RAM)
- 🔄 May take ~30 seconds to start up
- Suitable for low-traffic apps

### Database Notes:
- SQLite is fine for single instance
- For scalability, upgrade to PostgreSQL
- To add PostgreSQL: Render Dashboard → New → PostgreSQL

### Media Files:
- Downloaded videos stored in `/var/data/media`
- Persists between deployments
- Limited by disk size

### Static Files:
- Automatically collected to `/var/data/staticfiles`
- WhiteNoise serves them efficiently
- No need for separate CDN initially

## Deployment Checklist
- [ ] Push code to GitHub
- [ ] Create render.yaml
- [ ] Add environment variables
- [ ] Configure persistent disk at `/var/data`
- [ ] Update ALLOWED_HOSTS in settings
- [ ] Test migrations run successfully
- [ ] Verify app loads at HTTPS URL
- [ ] Test video download functionality

## Troubleshooting

### App keeps spinning down:
- Free plan has auto-sleep. Upgrade to Starter ($7/month) for always-on

### Static files not loading:
- Ensure STATIC_ROOT is set to `/var/data/staticfiles`
- Run: `python manage.py collectstatic --noinput`

### Database errors:
- SSH into Render Shell
- Run: `python manage.py migrate`
- Check if persistent disk is mounted

### Port issues:
- Render automatically uses port from `docker.io` 
- Ensure Dockerfile exposes correct port (8000)

## Cost Estimation
- **Free Plan**: $0 (with limitations)
- **Starter**: $7/month (always-on, 2GB RAM)
- **Standard**: $21/month (4GB RAM, better performance)
