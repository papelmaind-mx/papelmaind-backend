import { defineConfig } from 'vite';

// F27: bundle prod sin Babel (teclado virtual 3-modos como JS estático)
export default defineConfig({
  build: { target: 'es2020', minify: true, outDir: 'dist-kiosco' },
});
