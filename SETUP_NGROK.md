# Ngrok Setup Guide

This guide explains how to configure the application for ngrok (public access).

## Configuration

For ngrok setup, the frontend uses relative URLs that go through Vite's proxy to the backend.

### Setup Steps

1. **Configure Frontend for Ngrok**

   Edit `docker-compose.yml` and **remove or comment out** `VITE_API_URL`:
   ```yaml
   frontend:
     environment:
       # For ngrok: leave VITE_API_URL unset
       # - VITE_API_URL=http://localhost:8000
   ```

   Or ensure `frontend/.env` does NOT have `VITE_API_URL` set.

2. **Restart Frontend**

   ```bash
   docker compose restart frontend
   ```

3. **Start Ngrok**

   ```bash
   ngrok http 3000
   ```

4. **Access the Application**

   - Use the ngrok HTTPS URL shown in the ngrok interface
   - Example: `https://abc123.ngrok-free.dev`

## How It Works

- Frontend uses relative URLs (`/api/...`) for API calls
- Vite proxy forwards `/api/*` requests to `http://backend:8000`
- All requests go through the single ngrok tunnel
- Works from anywhere on the internet

## Important Notes

- **Single Tunnel**: Only one ngrok tunnel is needed (frontend only)
- **Proxy Required**: The Vite proxy must be enabled for this to work
- **allowedHosts**: Set to `true` in `vite.config.ts` to allow ngrok domains
- **No Backend Tunnel**: Backend doesn't need its own ngrok tunnel

## Troubleshooting

- **"No sectors data available"**: Check that `VITE_API_URL` is NOT set
- **API calls failing**: Check Vite proxy is working: `curl http://localhost:3000/api/v1/sectors`
- **CORS errors**: Backend CORS allows all origins
- **Blank page**: Check browser console for errors

## Switching Back to Local

To switch back to local development:

1. Set `VITE_API_URL=http://localhost:8000` in `docker-compose.yml`
2. Restart frontend: `docker compose restart frontend`
3. Stop ngrok

