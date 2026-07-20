module.exports = {
  root: true,
  env: {
    browser: true,
    node: true,
    es2022: true
  },
  extends: ['plugin:vue/vue3-essential'],
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module'
  },
  ignorePatterns: ['dist/**', 'node_modules/**'],
  rules: {
    // Unused vars often hide dead code or typos; surface them without failing CI.
    'no-unused-vars': 'warn',
    'vue/multi-word-component-names': 'off',
    // Correctness rules: these catch real bugs, so they must fail the build.
    'vue/require-v-for-key': 'error',
    'vue/no-parsing-error': 'error',
    'vue/no-use-v-if-with-v-for': 'error',
    'vue/no-textarea-mustache': 'off',
    'vue/no-reserved-props': 'off'
  },
  overrides: [
    {
      files: ['src/**/*.spec.js', 'src/test/**/*.js'],
      globals: {
        describe: 'readonly',
        it: 'readonly',
        expect: 'readonly',
        vi: 'readonly',
        beforeAll: 'readonly',
        beforeEach: 'readonly',
        afterAll: 'readonly',
        afterEach: 'readonly'
      }
    }
  ]
}
