<script setup lang="ts">
// Authors list
const authors = [
  'Jeyapiragash Jeyapalan',
  'Benoit Schick',
  'Daryl Warpelin',
  'Robin Zweifel'
]
</script>

<template>
  <div class="about-page">
    <header class="page-header">
      <h1 class="page-title">About OceanPulse</h1>
    </header>

    <section class="section">
      <h2 class="section-title">An HES-SO and University of Bern/BFH master academical project</h2>
      <p class="section-content">
        This platform was created as part of the PI MONIT project of the HES-SO Master.
        This aims to present the data collected by a marine animal monitoring device.
        As part of this project, we chose to focus on sea turtles which have behavior
        that is easier to monitor than other species.
      </p>

      <figure class="image-figure">
        <!-- Placeholder - user will provide image -->
        <div class="image-placeholder">
          <img src="@/assets/turtle.png" alt="Sea turtle illustration" />
        </div>
        <figcaption>
          The sea turtle has an easier behaviour to monitor (often at the surface, max. meters dive, etc.)
        </figcaption>
      </figure>
    </section>

    <section class="section">
      <h2 class="section-title">Authors</h2>
      <p class="section-content">
        {{ authors.join(', ') }}
      </p>
    </section>

    <section class="section">
      <h2 class="section-title">Data</h2>
      <p class="section-content">
        Data are aimed to be shared through an open data process to be used by scientists.
        Please follow the "Open Data" link.
      </p>
    </section>
  </div>
</template>

<style scoped>
.about-page {
  max-width: 900px;
}

.page-header {
  margin-bottom: var(--spacing-2xl);
}

.page-title {
  font-size: var(--font-size-4xl);
  font-weight: 700;
  color: var(--color-text-primary);
}

.section {
  margin-bottom: var(--spacing-2xl);
}

.section-title {
  font-size: var(--font-size-2xl);
  font-weight: 600;
  margin-bottom: var(--spacing-md);
  color: var(--color-text-primary);
}

.section-content {
  font-size: var(--font-size-base);
  line-height: 1.7;
  color: var(--color-text-secondary);
}

.image-figure {
  margin: var(--spacing-xl) 0;
}

.image-placeholder {
  width: 100%;
  max-width: 600px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted);
  font-style: italic;
}

.image-figure figcaption {
  margin-top: var(--spacing-sm);
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  font-style: italic;
}
</style>
