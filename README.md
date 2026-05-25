# Dreamy Downloader - Multi-Platform Video Downloader

A sleek, modern web application built with **Django** that allows you to download videos from popular social media platforms including YouTube, TikTok, Instagram, and Twitter/X. The application features a beautiful, responsive UI with gradient styling, real-time format detection, and quality selection.

Check it out here: https://videodownloader-xc24.onrender.com

---

## Project Overview

**Dreamy Downloader** is a Django-based web application that serves as a frontend to the powerful `yt-dlp` library, extended to support multiple video platforms. Unlike simple YouTube download tools, this application:

- Provides a user-friendly interface for non-technical users
- Supports multiple video platforms with a single application
- Implements intelligent format selection based on user preference
- Handles errors gracefully with informative messages
- Can be easily deployed to production environments

The application consists of:
- **Backend**: Django web server handling video processing
- **Frontend**: HTML/CSS/JavaScript for user interaction
- **Video Processing**: FFmpeg and yt-dlp integration for download/conversion
- **Storage**: SQLite database (local) with support for persistent storage in production

---

## Technology Stack

### Core Framework
- **Django 6.0.3** - Web framework and request handling
- **Python 3.12** - Programming language (slim Docker image)

### Video Processing
- **yt-dlp (2026.3.17)** - Advanced video downloader and metadata extractor
- **imageio-ffmpeg** - FFmpeg wrapper for video processing and merging
- **FFmpeg** - Professional multimedia framework (system dependency)

### Server & Deployment
- **Gunicorn 25.3.0** - WSGI HTTP server (production)
- **Uvicorn 0.44.0** - ASGI server (alternative)
- **WhiteNoise 6.12.0** - Static file serving in production
- **Docker & Docker Compose** - Containerization

### Database
- **SQLite 3** - Local development database
- **SQLparse 0.5.5** - SQL parsing utilities

### Frontend
- **HTML5** - Semantic markup
- **CSS3** - Modern styling with gradients and animations
- **JavaScript (Vanilla)** - Client-side interactions
- **Google Fonts** - Typography (Playfair Display, Nunito)

---

## System Requirements

### Minimum Requirements
- **OS**: Linux, macOS, or Windows
- **CPU**: 2 cores recommended
- **RAM**: 2 GB minimum, 4 GB recommended
- **Storage**: 5 GB for application + buffer for video files

### Required Software
- **Python 3.12+** - Required for running the Django application
- **FFmpeg** - Required for video processing and merging
  - **Linux**: `sudo apt-get install ffmpeg`
  - **macOS**: `brew install ffmpeg`
  - **Windows**: Download from https://www.ffmpeg.org/download.html
- **Git** - For version control (optional)
- **Docker & Docker Compose** - For containerized deployment (optional)

### For Production Deployment
- **Server**: Any Linux-based server (Ubuntu 20.04+ recommended)
- **Port**: 8000 (or configurable)
- **Persistent Storage**: For downloaded videos and database
- **SSL Certificate**: For HTTPS (recommended for Render deployment)

---

## Installation & Setup

### Option 1: Local Development Setup (Recommended for Development)

#### Step 1: Clone Repository
```bash
git clone https://github.com/Oredelight/Video-Downloader
cd videodownloader
```

#### Step 2: Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### Step 3: Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 4: Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
- Download FFmpeg from https://www.ffmpeg.org/download.html
- Add FFmpeg to your PATH environment variable

#### Step 5: Run Migrations
```bash
cd videodownloader
python manage.py migrate
```

#### Step 6: Create Superuser (Optional, for Admin Panel)
```bash
python manage.py createsuperuser
```

#### Step 7: Collect Static Files
```bash
python manage.py collectstatic --noinput
```

#### Step 8: Start Development Server
```bash
python manage.py runserver
```

The application will be available at `http://localhost:8000/`

### Option 2: Docker Setup (Recommended for Production)

See [Docker Setup](#-docker-setup) section below.

---

## Configuration

### Django Settings

The main configuration file is located at `videodownloader/settings.py`. Key settings:

#### Debug Mode
```python
DEBUG = os.getenv('DEBUG', 'False') == 'True'  # Set to 'False' in production
```

#### Allowed Hosts
```python
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')
# Examples: 'localhost,127.0.0.1' or 'yourdomain.com'
```

#### Secret Key
```python
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')
# Always use a strong, random key in production!
```

#### Static Files Configuration
```python
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
```

#### Media Files Configuration
```python
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

---

## Project Structure

```
videodownloader/
│
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── Dockerfile                         # Docker image configuration
├── docker-compose.yml                 # Docker Compose configuration
├── db.sqlite3                         # SQLite database
├── manage.py                          # Django management script
├── render.yaml                        # Render deployment configuration
├── RENDER_DEPLOYMENT.md               # Render deployment guide
│
├── videodownloader/                   # Main Django project directory
│   ├── settings.py                    # Django settings
│   ├── urls.py                        # URL configuration and routing
│   ├── wsgi.py                        # WSGI entry point for servers
│   ├── asgi.py                        # ASGI entry point (async support)
│   └── __init__.py
│
├── downloader/                        # Django app for video downloading
│   ├── views.py                       # View functions and handlers
│   ├── models.py                      # Database models (currently empty)
│   ├── admin.py                       # Django admin configuration
│   ├── apps.py                        # App configuration
│   ├── tests.py                       # Unit tests
│   ├── __init__.py
│   │
│   ├── migrations/                    # Database migrations
│   │   └── __init__.py
│   │
│   └── templates/
│       └── home.html                  # Main template with UI
│
├── media/                             # Uploaded/downloaded files storage
│
└── staticfiles/                       # Collected static files (production)
```

---

## Usage Guide

### Web Interface

#### 1. Accessing the Application
Open your browser and navigate to:
- **Local**: `http://localhost:8000/`
- **Production**: `https://videodownloader-xc24.onrender.com`

#### 2. Download a Video

**Step 1: Enter URL**
- Paste the video URL in the input field
- Supported platforms: YouTube, TikTok, Instagram, Twitter/X

**Step 2: Preview Video**
- Click "Preview" or press Enter
- The app will fetch video metadata, thumbnail, and available formats
- You'll see:
  - Video title
  - Thumbnail image
  - Available quality options (in descending order)
  - Platform information

**Step 3: Select Quality**
- Choose your desired quality/resolution
- Higher resolutions = larger file size and longer download time
- Best quality combines best video and best audio streams

**Step 4: Download**
- Click the "Download" button
- Your browser will initiate the download
- The file will be named `[uuid].mp4` with sanitized title information

## API Endpoints

### 1. Home Page
- **Endpoint**: `GET /`
- **Name**: `home`
- **Description**: Serves the main HTML interface
- **Response**: HTML page with UI
- **Example**:
  ```
  GET / HTTP/1.1
  Host: localhost:8000
  ```

### 2. Preview Video
- **Endpoint**: `POST /preview/`
- **Name**: `preview`
- **Description**: Fetch video metadata and available formats without download
- **Parameters**:
  - `url` (required): Video URL
- **Returns**: Rendered HTML with video info
- **Response Fields**:
  - `title`: Video title
  - `thumbnail`: Thumbnail image URL
  - `formats`: List of available formats (quality, format_id)
  - `platform`: Detected platform (YouTube, TikTok, etc.)
- **Error Handling**:
  - Returns error if URL is invalid
  - Returns error if platform is not supported
  - Returns error if video is unavailable

### 3. Download Video
- **Endpoint**: `POST /download/`
- **Name**: `download`
- **Description**: Download video at specified quality
- **Parameters**:
  - `url` (required): Video URL
  - `quality` (required): Quality selection (e.g., "1080p", "720p")
- **Returns**: File stream (mp4)
- **Response Type**: `application/octet-stream`
- **Processing Steps**:
  1. Validates URL and quality
  2. Fetches fresh format list
  3. Selects best available format at or below requested height
  4. Downloads and merges streams
  5. Streams file to client
  6. Cleans up temporary files
- **Error Handling**:
  - Returns error if URL is invalid
  - Returns error if quality parameter is malformed
  - Returns error if download fails
---
**Happy Downloading!✨**
<img width="1919" height="1005" alt="Screenshot 2026-04-12 174552" src="https://github.com/user-attachments/assets/ac5dd416-5be8-4f4f-ad14-1d65f7da4669" />

PLEASE NOTE: Youtube stopped working after deployment because Youtube is blocking the Render's IP address


