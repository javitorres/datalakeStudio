<template>
  <div class="color-scale">
    <div class="scale-ramp">
      <label class="swatch" :style="{ background: colorLow }" :title="t('MapH3.lowColor')">
        <input type="color" :value="colorLow" :aria-label="t('MapH3.lowColor')"
          @change="emit('update:colorLow', $event.target.value); emit('change')">
      </label>
      <div class="scale-track">
        <!-- The histogram of the values, colored as the map colors them -->
        <svg class="scale-histogram" viewBox="0 0 100 28" preserveAspectRatio="none" aria-hidden="true">
          <defs>
            <linearGradient :id="gradientId" gradientUnits="userSpaceOnUse" :x1="lowPercent" :x2="highPercent" y1="0" y2="0">
              <stop offset="0" :stop-color="colorLow" />
              <stop offset="1" :stop-color="colorHigh" />
            </linearGradient>
          </defs>
          <rect v-for="bar in bars" :key="bar.x" :x="bar.x" :y="28 - bar.height" width="0.8" :height="bar.height"
            :fill="`url(#${gradientId})`" :opacity="bar.inside ? 1 : 0.3" />
        </svg>
        <div class="dual-range">
          <input type="range" step="any" :min="min" :max="max" :value="low" :disabled="disabled" :aria-label="t('MapH3.from')"
            @input="setLow($event.target.value)" @change="emit('change')">
          <input type="range" step="any" :min="min" :max="max" :value="high" :disabled="disabled" :aria-label="t('MapH3.to')"
            @input="setHigh($event.target.value)" @change="emit('change')">
        </div>
      </div>
      <label class="swatch" :style="{ background: colorHigh }" :title="t('MapH3.highColor')">
        <input type="color" :value="colorHigh" :aria-label="t('MapH3.highColor')"
          @change="emit('update:colorHigh', $event.target.value); emit('change')">
      </label>
    </div>
    <div class="scale-values">
      <input type="number" step="any" :value="low" :disabled="disabled" :aria-label="t('MapH3.from')"
        @change="setLow($event.target.value); emit('change')">
      <button type="button" class="scale-reset" :disabled="disabled" :title="t('MapH3.resetRangeHelp')" @click="emit('reset')">
        {{ t('MapH3.resetRange') }}
      </button>
      <input type="number" step="any" :value="high" :disabled="disabled" :aria-label="t('MapH3.to')"
        @change="setHigh($event.target.value); emit('change')">
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';

// The color ramp of a map layer and the range of values it spans, over the histogram of the values
const props = defineProps({
  min: { type: Number, default: 0 },
  max: { type: Number, default: 1 },
  low: { type: Number, default: 0 },
  high: { type: Number, default: 1 },
  histogram: { type: Array, default: () => [] },
  colorLow: { type: String, default: '#ffffff' },
  colorHigh: { type: String, default: '#000000' },
  disabled: { type: Boolean, default: false },
});
const emit = defineEmits(['update:low', 'update:high', 'update:colorLow', 'update:colorHigh', 'change', 'reset']);
const { t } = useI18n();

// Unique per instance: two layers can show their scales at once
const gradientId = `scale-gradient-${Math.random().toString(36).slice(2, 10)}`;

// Where a value falls on the track, in percent
function percent(value) {
  const span = props.max - props.min;
  if (!Number.isFinite(span) || span <= 0) return 0;
  return Math.max(0, Math.min(100, ((value - props.min) / span) * 100));
}
const lowPercent = computed(() => percent(props.low));
// A zero-width gradient draws nothing: give it at least a hair
const highPercent = computed(() => Math.max(percent(props.high), lowPercent.value + 0.01));

const bars = computed(() => {
  const counts = props.histogram || [];
  const top = Math.max(1, ...counts);
  const width = 100 / Math.max(1, counts.length);
  return counts.map((count, index) => {
    const x = index * width;
    return {
      x,
      // Even one value shows: sqrt keeps the small bins visible next to a tall one
      height: count ? Math.max(2, Math.sqrt(count / top) * 28) : 0,
      inside: x + width >= lowPercent.value && x <= highPercent.value,
    };
  });
});

function setLow(value) {
  emit('update:low', Math.min(Number(value), props.high));
}

function setHigh(value) {
  emit('update:high', Math.max(Number(value), props.low));
}
</script>

<style scoped>
.color-scale { display: grid; gap: 6px; }
.scale-ramp { display: grid; grid-template-columns: 22px 1fr 22px; align-items: end; gap: 8px; }
.swatch { position: relative; width: 22px; height: 22px; margin: 0 0 3px; border: 2px solid #fff; border-radius: 50%; box-shadow: 0 0 0 1px var(--ds-line); cursor: pointer; }
.swatch input { position: absolute; inset: 0; width: 100%; height: 100%; opacity: 0; cursor: pointer; }
.scale-track { position: relative; height: 46px; }
.scale-histogram { position: absolute; left: 0; right: 0; top: 0; width: 100%; height: 28px; }
.dual-range { position: absolute; left: 0; right: 0; bottom: 0; height: 18px; }
.dual-range::before { content: ''; position: absolute; left: 0; right: 0; top: 8px; height: 2px; border-radius: 2px; background: var(--ds-line); }
.dual-range input { position: absolute; inset: 0; width: 100%; margin: 0; background: transparent; pointer-events: none; appearance: none; -webkit-appearance: none; }
.dual-range input::-webkit-slider-runnable-track { height: 18px; background: transparent; }
.dual-range input::-moz-range-track { background: transparent; }
.dual-range input::-webkit-slider-thumb { -webkit-appearance: none; width: 14px; height: 14px; margin-top: 2px; border: 2px solid var(--ds-teal); border-radius: 50%; background: #fff; pointer-events: auto; cursor: ew-resize; }
.dual-range input::-moz-range-thumb { width: 10px; height: 10px; border: 2px solid var(--ds-teal); border-radius: 50%; background: #fff; pointer-events: auto; cursor: ew-resize; }
.scale-values { display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; gap: 6px; padding: 0 30px; }
.scale-values input { width: 100%; min-width: 0; padding: 3px 6px; border: 1px solid var(--ds-line); border-radius: 6px; font-size: 12px; font-variant-numeric: tabular-nums; }
.scale-values input:last-child { text-align: right; }
.scale-reset { padding: 2px 8px; border: 0; border-radius: 6px; background: transparent; color: var(--ds-teal-dark); font-size: 11px; font-weight: 700; }
.scale-reset:hover:not(:disabled) { background: var(--ds-mint); }
</style>
