// The charts the AI assistant and the dashboards draw from a result: the ECharts option of a chart
// { type, x, y: [columns] } for a result { columns, rows } (rows as arrays in column order)

export const CHART_TYPES = [
  { id: 'bar', icon: 'bi bi-bar-chart' },
  { id: 'horizontalBar', icon: 'bi bi-bar-chart-steps' },
  { id: 'line', icon: 'bi bi-graph-up' },
  { id: 'area', icon: 'bi bi-graph-up-arrow' },
  { id: 'pie', icon: 'bi bi-pie-chart' },
  { id: 'scatter', icon: 'bi bi-dot' },
];
export const CHART_COLORS = ['#0d846f', '#f2a541', '#5c7cfa', '#e76f51', '#2fb594', '#c77dff', '#8d99ae', '#ffd166', '#4cc9f0', '#b5838d'];
// Slices of a pie chart: the rest are added up in one, named `others`
export const PIE_SLICES = 10;

export function chartOption(chart, result, { others = 'Others' } = {}) {
  const column = (name) => result.columns.indexOf(name);
  const x = column(chart.x);
  const ys = chart.y.map(column).filter((i) => i >= 0);
  const number = (value) => (value === '' || value == null ? null : Number(value));
  const base = { color: CHART_COLORS, animationDuration: 400, tooltip: { trigger: chart.type === 'pie' || chart.type === 'scatter' ? 'item' : 'axis' } };

  if (chart.type === 'pie') {
    const slices = result.rows.map((row) => ({ name: row[x], value: number(row[ys[0]]) || 0 }))
      .sort((a, b) => b.value - a.value);
    if (slices.length > PIE_SLICES) {
      const rest = slices.splice(PIE_SLICES - 1);
      slices.push({ name: others, value: rest.reduce((sum, s) => sum + s.value, 0) });
    }
    return {
      ...base,
      legend: { type: 'scroll', bottom: 0 },
      series: [{
        type: 'pie', radius: ['38%', '68%'], center: ['50%', '45%'], data: slices,
        itemStyle: { borderColor: '#fff', borderWidth: 2, borderRadius: 4 },
        label: { formatter: '{b}: {d}%' },
      }],
    };
  }

  const horizontal = chart.type === 'horizontalBar';
  const scatter = chart.type === 'scatter';
  const categories = result.rows.map((row) => row[x]);
  const categoryAxis = { type: 'category', data: categories, axisLabel: { hideOverlap: true } };
  const valueAxis = { type: 'value', scale: scatter };
  return {
    ...base,
    legend: ys.length > 1 ? { top: 0 } : undefined,
    grid: { left: 12, right: 16, top: ys.length > 1 ? 32 : 16, bottom: 8, containLabel: true },
    xAxis: scatter ? { type: 'value', scale: true, name: chart.x } : horizontal ? valueAxis : categoryAxis,
    yAxis: horizontal ? { ...categoryAxis, inverse: true } : valueAxis,
    series: ys.map((i) => ({
      name: result.columns[i],
      type: scatter ? 'scatter' : horizontal ? 'bar' : chart.type === 'area' ? 'line' : chart.type,
      data: scatter ? result.rows.map((row) => [number(row[x]), number(row[i])]) : result.rows.map((row) => number(row[i])),
      smooth: chart.type === 'area',
      areaStyle: chart.type === 'area' ? { opacity: 0.18 } : undefined,
      itemStyle: chart.type === 'bar' || horizontal ? { borderRadius: horizontal ? [0, 4, 4, 0] : [4, 4, 0, 0] } : undefined,
    })),
  };
}
