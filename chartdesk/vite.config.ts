import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { viteSingleFile } from 'vite-plugin-singlefile';

const single = process.env.SINGLE === '1';

/**
 * vite-plugin-singlefile keeps `type="module"` on the inlined script. On a
 * phone the app is opened straight from storage (file://), where module scripts
 * are rejected as cross-origin. Rollup already emits an IIFE here, so dropping
 * the attribute makes the file openable with no server at all.
 */
function classicInlineScript() {
  return {
    name: 'chartdesk-classic-inline-script',
    enforce: 'post' as const,
    transformIndexHtml(html: string) {
      // also move it to the end of <body>: a classic script in <head> runs
      // before #root exists, which would mount nothing at all.
      const scripts: string[] = [];
      const withoutScripts = html.replace(/<script[^>]*>[\s\S]*?<\/script>/g, (match) => {
        scripts.push(match.replace(/<script type="module"([^>]*)>/, '<script$1>'));
        return '';
      });
      const payload = scripts.join('\n');
      return withoutScripts.replace('</body>', `${payload}\n</body>`);
    },
  };
}

export default defineConfig({
  // relative base so the same build works at /, /chartdesk/ or from a phone's file system
  base: './',
  plugins: [
    react(),
    ...(single ? [viteSingleFile({ removeViteModuleLoader: true }), classicInlineScript()] : []),
  ],
  server: { host: '0.0.0.0', port: 5173, strictPort: true, allowedHosts: true },
  preview: { host: '0.0.0.0', port: 4173, strictPort: true, allowedHosts: true },
  build: {
    target: single ? 'es2019' : 'es2022',
    chunkSizeWarningLimit: 2000,
    outDir: single ? 'standalone' : 'web',
    emptyOutDir: true,
    assetsInlineLimit: single ? 100_000_000 : 4096,
    // A classic IIFE keeps the single-file build runnable straight from file://
    // on a phone, where module scripts are blocked by the opaque origin.
    rollupOptions: single
      ? { output: { format: 'iife' as const, inlineDynamicImports: true, entryFileNames: 'app.js' } }
      : {},
  },
});
