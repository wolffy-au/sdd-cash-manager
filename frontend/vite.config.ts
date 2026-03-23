import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { join } from 'node:path';

export default defineConfig({
  root: '.',
  plugins: [react()],
  server: {
    port: 4173,
    strictPort: true,
    open: true
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      input: join(__dirname, 'index.html')
    }
  },
  resolve: {
    alias: {
      '@': join(__dirname, 'src')
    }
  }
});
