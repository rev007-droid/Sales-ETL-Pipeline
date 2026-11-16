// import defineConfig
import { defineConfig } from 'vite';
// import react plugin
import react from '@vitejs/plugin-react';

// export vite config
export default defineConfig({
  plugins: [react()], // enable react
  server: {
    port: 5173, // dev port
    proxy: {
      '/api': {
        target: 'http://localhost:8000', // proxy backend
        changeOrigin: true, // change origin
        secure: false // allow localhost
      }
    }
  }
});
