<template>
  <section class="welcome-shell">
    <a href="https://github.com/javitorres/datalakeStudio" target="_blank" class="welcome-link">
      <div class="welcome-brand">
        <img src="../assets/logo.svg" width="108" alt="Datalake Studio logo" />
        <h1 class="logo">DATALAKE STUDIO</h1>
      </div>
      <p class="lema">DATA TO API IN SECONDS</p>
      <p class="compact-muted">Open source toolkit for fast local data exploration and API publishing.</p>
    </a>
  </section>
</template>

<style scoped>
.welcome-shell {
  min-height: calc(100vh - 140px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.welcome-link,
.welcome-link:hover,
.welcome-link:active,
.welcome-link:visited {
  text-decoration: none;
}

.welcome-link {
  width: min(980px, 100%);
  text-align: center;
  background: #ffffff;
  border: 1px solid #e4e6ec;
  border-radius: 14px;
  padding: 24px 20px;
  box-shadow: 0 10px 32px rgba(45, 61, 90, 0.08);
}

.welcome-brand {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-bottom: 8px;
}

.logo {
  font-family: 'Orbitron', 'Segoe UI', sans-serif;
  color: #22242b;
  font-size: clamp(1.8rem, 4vw, 3.5rem);
  font-weight: 700;
  margin: 0;
  letter-spacing: 0.04em;
}

.lema {
  font-family: 'Lexend Peta', 'Segoe UI', sans-serif;
  color: #2f3440;
  font-size: clamp(0.88rem, 2.4vw, 1.4rem);
  font-weight: 500;
  margin: 6px 0 8px;
  letter-spacing: 0.03em;
}

@media (max-width: 768px) {
  .welcome-brand {
    flex-direction: column;
    gap: 8px;
  }
}
</style>
