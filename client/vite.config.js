import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// The public build runs only in the browser and promises that nothing leaves it: it drops the
// index.html tags that load scripts, styles and fonts from other sites
function noThirdPartyTags() {
  return {
    name: 'no-third-party-tags',
    transformIndexHtml(html) {
      return html.replace(/[ \t]*<(script|link)\b[^>]*\b(src|href)="https?:\/\/[^"]*"[^>]*>(<\/script>)?\n?/g, '')
    }
  }
}

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  plugins: [
    vue(),
    ...(mode === 'public' ? [noThirdPartyTags()] : []),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  // DuckDB-WASM loads its worker and .wasm files by URL: pre-bundling it breaks those paths
  optimizeDeps: {
    exclude: ['@duckdb/duckdb-wasm']
  }
}))
