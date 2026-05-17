# Render Deployment Guide

This guide will help you deploy the Django Community application to Render.com.

## Prerequisites

- A Render.com account (free tier available)
- Git repository with your code
- Render CLI (optional, but recommended)

## Deployment Steps

### 1. Push Code to GitHub

Make sure your code is pushed to a GitHub repository that Render can access.

```bash
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

### 2. Create Render Account

1. Go to [render.com](https://render.com)
2. Sign up or log in
3. Connect your GitHub account

### 3. Deploy Using render.yaml

The easiest way to deploy is using the `render.yaml` file included in the project:

1. In Render dashboard, click "New +"
2. Select "Blueprint"
3. Connect your GitHub repository
4. Select the repository containing the `render.yaml` file
5. Click "Apply"

Render will automatically create:
- Web service for the Django application
- Redis instance for channel layers
- Environment variables

### 4. Manual Deployment (Alternative)

If you prefer manual deployment:

#### Web Service

1. Click "New +"
2. Select "Web Service"
3. Connect your GitHub repository
4. Configure:

**Name:** community-app

**Environment:** Python

**Build Command:**
```
pip install -r requirements.txt
python manage.py collectstatic --noinput
```

**Start Command:**
```
gunicorn community.wsgi:application
```

**Environment Variables:**
```
DEBUG=False
DJANGO_SECRET_KEY=<generate-a-secure-key>
ALLOWED_HOSTS=your-app-name.onrender.com
REDIS_URL=<will-be-provided-by-redis-service>
```

#### Redis Service

1. Click "New +"
2. Select "Redis"
3. Name it: redis
4. Select free plan
5. Click "Create Redis"

6. Go back to your web service settings
7. Add environment variable: `REDIS_URL`
8. Set it to connect to the Redis service (Render will provide the connection string)

### 5. Configure Environment Variables

Update the following environment variables in your Render web service:

- `DEBUG=False` - Required for production
- `DJANGO_SECRET_KEY` - Generate a secure key using:
  ```bash
  python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
  ```
- `ALLOWED_HOSTS` - Your Render URL (e.g., `your-app-name.onrender.com`)
- `REDIS_URL` - Provided by Render Redis service

### 6. Database Setup

The application uses SQLite by default. For production on Render, you have two options:

**Option 1: Keep SQLite (Free tier)**
- SQLite works fine for small applications
- Files are stored in Render's ephemeral filesystem
- Data may be lost on redeploy

**Option 2: Use PostgreSQL (Recommended for production)**
1. Create a PostgreSQL service in Render
2. Update `settings.py` to use PostgreSQL:
```python
import dj_database_url

DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///db.sqlite3',
        conn_max_age=600,
        conn_health_checks=True
    )
}
```
3. Add `dj-database-url` to requirements.txt
4. Add `DATABASE_URL` environment variable from PostgreSQL service

### 7. Static Files

Static files are automatically collected during deployment. Render serves them from the `/staticfiles` directory.

### 8. Media Files

For user uploads (profile pictures, cover pictures), you should use a cloud storage service:

**Option 1: Render Disk (Free tier)**
- Limited storage
- Data may be lost on redeploy

**Option 2: AWS S3 (Recommended)**
1. Create an AWS S3 bucket
2. Install `django-storages` and `boto3`
3. Configure in settings.py:
```python
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = 'us-east-1'
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
AWS_DEFAULT_ACL = 'public-read'
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}
```

### 9. Deploy

Click "Deploy" in Render. The deployment process will:
1. Install dependencies
2. Collect static files
3. Start the Gunicorn server
4. Connect to Redis

### 10. Access Your Application

Once deployed, Render will provide a URL like:
```
https://your-app-name.onrender.com
```

## Troubleshooting

### Build Fails

Check the deployment logs in Render dashboard for specific errors.

### Database Migration Issues

Add migration command to build command:
```
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

### Static Files Not Loading

Ensure `STATIC_ROOT` is set correctly in settings.py:
```python
STATIC_ROOT = BASE_DIR / "staticfiles"
```

### Redis Connection Issues

Verify `REDIS_URL` environment variable is set correctly and Redis service is running.

### Allowed Hosts Error

Make sure your Render URL is in `ALLOWED_HOSTS` environment variable.

## Post-Deployment Checklist

- [ ] Application loads successfully
- [ ] User registration works
- [ ] User login works
- [ ] Profile editing works
- [ ] Image uploads work
- [ ] Chat functionality works
- [ ] Posts work
- [ ] Navigation works correctly
- [ ] Static files load
- [ ] No console errors

## Monitoring

Render provides:
- Real-time logs
- Metrics (CPU, memory, response time)
- Error tracking
- Deployment history

Monitor these regularly to ensure your application is running smoothly.

## Scaling

If your application grows, you can:
- Upgrade to paid Render plans
- Add more web service instances
- Use PostgreSQL instead of SQLite
- Implement caching
- Add a CDN for static files
