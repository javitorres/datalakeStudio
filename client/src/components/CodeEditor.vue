<template>
  <!-- TODO: Complete this component with SQL code completion. But I get this error: Uncaught (in promise) Error: Unrecognized extension value in extension set ([object Object]). This sometimes happens because multiple instances of @codemirror/state are loaded, breaking instanceof checks. -->
  <codemirror
              v-model="query" 
              placeholder="SELECT * FROM ..."
              :style="{ height: '200px' }"
              :autofocus="true"
              :indent-with-tab="true"
              :tab-size="4"
              :extensions="extensions"
          />
</template>

<script>
import { Codemirror } from "vue-codemirror";
import { sql } from "@codemirror/lang-sql";
import { autocompletion, completionKeymap } from '@codemirror/autocomplete';

export default {
  name: 'CodeEditor',
  data() {
    return {
    };
  },

  components: {
    Codemirror,
  },

  setup() {
      function sqlHint(editor) {
        // Obtener el texto hasta la posición del cursor
        const cursor = editor.getCursor();
        const currentLine = editor.getLine(cursor.line);
        const start = cursor.ch;
        const end = cursor.ch;
        const currentWord = currentLine.slice(start, end);

        // Aquí defines tus sugerencias. Estas podrían venir de tu esquema de base de datos.
        const suggestions = [
          { text: 'iris', displayText: 'iris de s3' },
          { text: 'tableName2', displayText: 'Table Name 2' },
          // ... más sugerencias ...
        ];

        // Filtrar sugerencias basadas en la palabra actual
        const filteredSuggestions = suggestions.filter(s => s.text.startsWith(currentWord));

        return {
          list: filteredSuggestions,
          from: CodeMirror.Pos(cursor.line, start - currentWord.length),
          to: CodeMirror.Pos(cursor.line, end)
        };
      }

      const extensions = [sql(),
          autocompletion({ override: [sqlHint] }),
          completionKeymap]

      return { extensions }
  },

  methods: {  },
}
</script>
<style scoped></style>