import axios from 'axios';

const api = axios.create({
  // In development, VITE_API_URL will be empty, so Axios will use relative paths (e.g. '/api/...')
  // which Vite will proxy to localhost:8000.
  // In production (Vercel), VITE_API_URL will be set to the Render backend URL.
  baseURL: import.meta.env.VITE_API_URL || '',
});

export default api;
