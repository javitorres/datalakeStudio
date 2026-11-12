const escapeHtml = (s) => s.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);

// The AI writes in Markdown: paragraphs, lists, bold and code. The text is escaped before any tag is added.
export function renderMarkdown(text) {
  const inline = (s) => escapeHtml(s)
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/(^|[^*])\*([^*\n]+)\*/g, '$1<em>$2</em>');
  const html = [];
  let list = null;
  const closeList = () => { if (list) { html.push(`</${list}>`); list = null; } };
  for (const block of text.replace(/\r/g, '').split(/\n{2,}/)) {
    const lines = block.split('\n');
    if (lines.every((l) => /^\s*([-*]|\d+[.)])\s+/.test(l))) {
      const kind = /^\s*\d/.test(lines[0]) ? 'ol' : 'ul';
      if (list !== kind) { closeList(); html.push(`<${kind}>`); list = kind; }
      lines.forEach((l) => html.push(`<li>${inline(l.replace(/^\s*([-*]|\d+[.)])\s+/, ''))}</li>`));
    } else {
      closeList();
      const heading = block.match(/^#{1,6}\s+(.*)$/);
      html.push(heading ? `<p><strong>${inline(heading[1])}</strong></p>` : `<p>${lines.map(inline).join('<br>')}</p>`);
    }
  }
  closeList();
  return html.join('');
}
