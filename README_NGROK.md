# Ngrok Setup Guide

This guide helps you expose your FundA application to the internet using ngrok, so you can share it with others.

## Prerequisites

1. **Install ngrok** (if not already installed):
   ```bash
   brew install ngrok/ngrok/ngrok
   ```
   Or download from: https://ngrok.com/download

2. **Get your ngrok authtoken**:
   - Sign up at https://dashboard.ngrok.com (free account works)
   - Get your authtoken from: https://dashboard.ngrok.com/get-started/your-authtoken
   - Configure it:
     ```bash
     ngrok config add-authtoken YOUR_TOKEN
     ```

## Quick Start

### Option 1: Simple Setup (Recommended)

This exposes only the frontend. You'll need to manually expose the backend separately.

```bash
./scripts/setup-ngrok-simple.sh
```

Then in another terminal:
```bash
ngrok http 8000
```

Copy the backend ngrok URL and update `frontend/.env`:
```bash
echo "VITE_API_URL=https://your-backend-ngrok-url.ngrok-free.app" > frontend/.env
docker compose restart frontend
```

### Option 2: Full Setup Script

```bash
./scripts/start-ngrok.sh
```

This script will:
- Start ngrok tunnels for both frontend and backend
- Display the public URLs
- Provide instructions for updating the frontend configuration

## Manual Setup

### Step 1: Expose Frontend

```bash
ngrok http 3000
```

This will give you a public URL like: `https://abc123.ngrok-free.app`

### Step 2: Expose Backend

In a **new terminal**, run:
```bash
ngrok http 8000
```

This will give you a backend URL like: `https://xyz789.ngrok-free.app`

### Step 3: Configure Frontend

Create or update `frontend/.env`:
```bash
echo "VITE_API_URL=https://xyz789.ngrok-free.app" > frontend/.env
```

### Step 4: Restart Frontend

```bash
docker compose restart frontend
```

### Step 5: Share the Frontend URL

Share the frontend ngrok URL (from Step 1) with your friend:
```
https://abc123.ngrok-free.app
```

## Important Notes

1. **Free ngrok URLs expire**: Free ngrok URLs change every time you restart ngrok. For a stable URL, consider ngrok's paid plans.

2. **CORS**: The backend should already be configured to allow requests from any origin. If you encounter CORS errors, check `backend/app/main.py`.

3. **HTTPS**: Ngrok provides HTTPS by default, which is required for many browser features.

4. **Ngrok Web Interface**: While ngrok is running, you can view requests and inspect traffic at:
   ```
   http://localhost:4040
   ```

5. **Stopping ngrok**: Press `Ctrl+C` in the terminal where ngrok is running.

## Troubleshooting

### Frontend can't connect to backend
- Make sure both ngrok tunnels are running
- Verify `VITE_API_URL` in `frontend/.env` matches the backend ngrok URL
- Restart the frontend container after updating `.env`

### Ngrok shows "ERR_NGROK_108"
- Your authtoken might be invalid or expired
- Re-authenticate: `ngrok config add-authtoken YOUR_TOKEN`

### Can't access ngrok URL
- Make sure your services are running: `docker compose ps`
- Check that ngrok is running: `curl http://localhost:4040`

## Example Workflow

```bash
# Terminal 1: Start frontend ngrok
ngrok http 3000

# Terminal 2: Start backend ngrok  
ngrok http 8000

# Terminal 3: Update frontend config
echo "VITE_API_URL=https://your-backend-url.ngrok-free.app" > frontend/.env
docker compose restart frontend

# Share the frontend URL from Terminal 1
```

## Security Note

⚠️ **Warning**: Exposing your local development server publicly can be a security risk. Only share ngrok URLs with trusted individuals, and consider using ngrok's authentication features for production use.

