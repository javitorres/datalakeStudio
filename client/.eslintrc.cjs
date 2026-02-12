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
    'no-unused-vars': 'off',
    'vue/multi-word-component-names': 'off',
    'vue/require-v-for-key': 'off',
    'vue/no-parsing-error': 'off',
    'vue/no-textarea-mustache': 'off',
    'vue/no-reserved-props': 'off',
    'vue/no-use-v-if-with-v-for': 'off'
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
