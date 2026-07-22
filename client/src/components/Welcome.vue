<template>
  <section class="welcome-shell">
    <div class="welcome-card">
      <div class="welcome-copy">
        <span class="welcome-kicker"><i></i> LOCAL DATA WORKSPACE</span>
        <h2>Explore freely.<br><em>Ship confidently.</em></h2>
        <p>Bring your data into one fast workspace, ask better questions and turn the answers into something useful.</p>
        <a href="https://github.com/javitorres/datalakeStudio" target="_blank">Read the documentation <i class="bi bi-arrow-up-right"></i></a>
      </div>
      <div class="welcome-visual">
        <div class="visual-orbit orbit-one"></div><div class="visual-orbit orbit-two"></div>
        <img src="../assets/logo.svg" alt="Datalake Studio logo">
        <span class="node node-a"><i class="bi bi-database"></i> Connect</span>
        <span class="node node-b"><i class="bi bi-command"></i> Query</span>
        <span class="node node-c"><i class="bi bi-graph-up"></i> Visualize</span>
        <span class="node node-d"><i class="bi bi-braces"></i> Publish</span>
      </div>
    </div>
    <div class="welcome-grid">
      <article><span>01</span><i class="bi bi-cloud-arrow-down"></i><div><b>Load a source</b><small>Files, URLs, S3 or PostgreSQL</small></div></article>
      <article><span>02</span><i class="bi bi-filetype-sql"></i><div><b>Explore with SQL</b><small>DuckDB speed with AI assistance</small></div></article>
      <article><span>03</span><i class="bi bi-boxes"></i><div><b>Publish an API</b><small>Turn saved queries into endpoints</small></div></article>
    </div>
  </section>
</template>

<style scoped>
.welcome-shell{display:grid;gap:13px;min-height:calc(100vh - 110px)}
.welcome-card{min-height:480px;display:grid;grid-template-columns:1fr 1fr;align-items:center;overflow:hidden;position:relative;padding:clamp(35px,6vw,85px);border:1px solid var(--ds-line);border-radius:16px;background:radial-gradient(circle at 80% 20%,rgba(116,202,181,.25),transparent 28%),linear-gradient(135deg,#fff,#f1f8f5);box-shadow:var(--ds-shadow)}
.welcome-card::before{content:'';position:absolute;inset:0;opacity:.25;background-image:linear-gradient(#dce8e4 1px,transparent 1px),linear-gradient(90deg,#dce8e4 1px,transparent 1px);background-size:44px 44px;mask-image:linear-gradient(to right,transparent 30%,#000 80%)}
.welcome-copy,.welcome-visual{position:relative;z-index:1}.welcome-kicker{display:inline-flex;align-items:center;gap:8px;color:#4d625d;font-size:9px;font-weight:800;letter-spacing:.16em}.welcome-kicker i{width:7px;height:7px;border-radius:50%;background:var(--ds-teal);box-shadow:0 0 0 4px rgba(13,132,111,.1)}h2{margin:18px 0;font-size:clamp(2.7rem,5vw,5.4rem);line-height:.94;letter-spacing:-.065em;font-weight:680;color:var(--ds-ink)}h2 em{font:inherit;color:var(--ds-teal)}.welcome-copy p{max-width:530px;color:var(--ds-muted);font-size:15px;line-height:1.75}.welcome-copy a{display:inline-flex;align-items:center;gap:10px;margin-top:10px;padding:11px 15px;border-radius:8px;background:var(--ds-ink);color:#fff;font-size:11px;font-weight:700}.welcome-visual{min-height:320px;display:grid;place-items:center}.welcome-visual>img{width:100px;height:100px;padding:23px;border:1px solid #cce1db;border-radius:27px;background:#fff;box-shadow:0 20px 50px rgba(34,74,64,.16)}.visual-orbit{position:absolute;border:1px dashed #91bdb1;border-radius:50%}.orbit-one{width:250px;height:250px}.orbit-two{width:340px;height:340px;opacity:.55}.node{position:absolute;display:flex;align-items:center;gap:7px;padding:8px 11px;border:1px solid #d6e4e0;border-radius:8px;background:#fffffff2;box-shadow:0 8px 20px rgba(35,70,61,.1);color:#52635f;font-size:9px;font-weight:700}.node i{color:var(--ds-teal);font-size:12px}.node-a{top:8%;left:18%}.node-b{top:24%;right:8%}.node-c{bottom:13%;right:15%}.node-d{bottom:5%;left:12%}.welcome-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:13px}.welcome-grid article{display:flex;align-items:center;gap:12px;padding:16px;border:1px solid var(--ds-line);border-radius:12px;background:#fff}.welcome-grid article>span{align-self:flex-start;color:#9ca8a5;font-size:8px;font-weight:800}.welcome-grid article>i{width:37px;height:37px;display:grid;place-items:center;border-radius:9px;background:var(--ds-mint);color:var(--ds-teal);font-size:15px}.welcome-grid div{display:grid}.welcome-grid b{font-size:11px}.welcome-grid small{color:var(--ds-muted);font-size:9px}
@media(max-width:850px){.welcome-card{grid-template-columns:1fr}.welcome-visual{display:none}.welcome-grid{grid-template-columns:1fr}.welcome-card{min-height:430px}h2{font-size:clamp(2.8rem,13vw,4.4rem)}}
</style>