# Local Development Setup

This guide explains how to run the application locally without ngrok.

## Configuration

For local development, the frontend connects directly to the backend API.

### Setup Steps

1. **Configure Frontend for Local Development**

   Edit `docker-compose.yml` and ensure the frontend has:
   ```yaml
   environment:
     - VITE_API_URL=http://localhost:8000
   ```

   Or create `frontend/.env.local`:
   ```
   VITE_API_URL=http://localhost:8000
   ```

2. **Start Services**

   ```bash
   docker compose up
   ```

3. **Access the Application**

   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## How It Works

- Frontend makes API calls directly to `http://localhost:8000`
- No proxy needed
- Works only on your local machine
- Cannot be accessed from other devices on your network

## Troubleshooting

- **API calls failing**: Check that backend is running on port 8000
- **CORS errors**: Backend CORS is configured to allow `http://localhost:3000`
- **Port conflicts**: Make sure ports 3000 and 8000 are not in use

