<template>
  <div class="container" v-if="filtersList && filtersList.length > 0">
    <h3> <i class="bi bi-funnel"></i>  Active filters:</h3>
    <ul class="list-unstyled d-flex flex-wrap">
      <li v-for="filter in filtersList" :key="filter.id">
        <button class="btn btn-primary m-1 opcion-style" @click="resetChart(filter.chart)">
           <i class="bi bi-x-octagon"></i>
          {{ filter.chart.replace("#chart-","") }}: {{ filter.filters }}
        </button>
      </li>
    </ul>
  </div>

  <div class="container">
    <button type="button" class="btn btn-danger" id="reset-all" >Reset All Filters</button>
  </div>


  <div class="section">
    <div class="container" >
      <div  class="row" id="charts-container" >
        <!-- Charts will be generated here with col-md-6 -->
      </div>
    </div>
  </div>

</template>

<script setup>
import { onMounted, ref, watch } from 'vue';
import { csvParse } from 'd3-dsv';

const props = defineProps({
  dataStr: String,
  chartConfig: Object,
  key: Number,
});

const filtersList = ref([]);

onMounted(() => {
  initializeDashboard(props.chartConfig);
  updateFiltersSummary();
});

watch(() => props.key, () => {
  initializeDashboard(props.chartConfig);
  updateFiltersSummary();
});

function createChartContainer(title, identifier, index, type) {
  var elementId = 'chart-' + (Array.isArray(identifier) ? identifier.join('-') : identifier);
  var container = document.createElement('div');
  container.className = 'chart-container col-md-6';
  container.id = elementId;

  var header = document.createElement('header');
  header.className = 'card-header';
  var titleElement = document.createElement('p');
  titleElement.className = 'card-header-title';
  titleElement.innerText = title;
  header.appendChild(titleElement);
  container.appendChild(header);

  if (type === 'numerical') {
    var rangeContainer = document.createElement('div');
    rangeContainer.className = 'range-container';

    var minInput = document.createElement('input');
    minInput.type = 'number';
    minInput.className = 'input is-small';
    minInput.placeholder = 'Min';
    minInput.onchange = () => { setChartDomain(elementId, 'min', minInput.value); };

    var maxInput = document.createElement('input');
    maxInput.type = 'number';
    maxInput.className = 'input is-small';
    maxInput.placeholder = 'Max';
    maxInput.onchange = () => { setChartDomain(elementId, 'max', maxInput.value); };

    rangeContainer.appendChild(minInput);
    rangeContainer.appendChild(maxInput);
    container.appendChild(rangeContainer);
  }

  if (index % 2 === 0) {
    var row = document.createElement('div');
    row.className = 'row';
    row.id = 'row-' + Math.floor(index / 2);
    document.getElementById('charts-container').appendChild(row);
  }

  var rowContainer = document.getElementById('row-' + Math.floor(index / 2));
  rowContainer.appendChild(container);

  return elementId;
}

function setChartDomain(chartId, type, value) {
  var chart = dc.chartRegistry.list().filter(c => c.anchor() === '#' + chartId)[0];
  if (!chart) return;

  var domain = chart.x().domain();
  var newValue = parseFloat(value);

  if (isNaN(newValue)) return;

  if (type === 'min' && newValue < domain[1]) {
    chart.x().domain([newValue, domain[1]]);
  } else if (type === 'max' && newValue > domain[0]) {
    chart.x().domain([domain[0], newValue]);
  } else {
    return;
  }

  chart.rescale();
  chart.redraw();
}

function generateChart(crossFilterData, chartConfig, index, data) {
  var elementId = createChartContainer(chartConfig.title, chartConfig.fields, index, chartConfig.type);
  var chart;

  let dimension = crossFilterData.dimension(dc.pluck(chartConfig.fields));
  let group = crossFilterData.dimension(dc.pluck(chartConfig.fields)).group().reduceCount();

  var reasonableMaxValue = d3.max(group.all(), d => d.key);

  switch (chartConfig.type) {
    case 'numerical':
      chart = dc.barChart('#' + elementId)
        .dimension(dimension)
        .group(group)
        .x(d3.scaleLinear().domain([0, reasonableMaxValue]))
        .elasticY(true);
      break;
    case 'categorical':
      chart = dc.pieChart('#' + elementId)
        .dimension(dimension)
        .innerRadius(40)
        .slicesCap(4)
        .group(group)
        .legend(dc.legend().highlightSelected(true));
      break;
    case 'date':
      chart = dc.lineChart('#' + elementId)
        .dimension(dimension)
        .group(group)
        .x(d3.scaleTime().domain(d3.extent(group.all(), d => d.key)))
        .elasticY(true);
      break;
    case 'scatter':
      if (!Array.isArray(chartConfig.fields)) {
        console.error("Error: 'fields' should be an array", chartConfig.fields);
        return;
      }
      dimension = crossFilterData.dimension(d => [d[chartConfig.fields[0]], d[chartConfig.fields[1]]]);
      group = dimension.group();

      chart = dc.scatterPlot('#' + elementId)
        .dimension(dimension)
        .group(group)
        .x(d3.scaleLinear().domain([0, d3.max(data, d => d[chartConfig.fields[0]])]))
        .y(d3.scaleLinear().domain([0, d3.max(data, d => d[chartConfig.fields[1]])]))
        .elasticX(true)
        .elasticY(true);
      break;
    case 'bubble':
      chart = dc.bubbleChart('#' + elementId);

      if (chartConfig.fields.length < 3) {
        console.error("Bubble chart necesita al menos 3 campos en 'fields': x, y, y tamaño de la burbuja");
        return;
      }

      dimension = crossFilterData.dimension(function (d) {
        return [d[chartConfig.fields[0]], d[chartConfig.fields[1]], d[chartConfig.fields[2]]];
      });

      group = dimension.group().reduce(
        function (p, v) {
          p.count++;
          p.size += v[chartConfig.fields[2]];
          return p;
        },
        function (p, v) {
          p.count--;
          p.size -= v[chartConfig.fields[2]];
          return p;
        },
        function () {
          return { count: 0, size: 0 };
        }
      );

      var maxBubbleSize = d3.max(data, d => d[chartConfig.fields[2]]);
      var minBubbleSize = d3.min(data, d => d[chartConfig.fields[2]]);
      var bubbleScale = d3.scaleSqrt().domain([minBubbleSize, maxBubbleSize]).range([0, chartConfig.maxBubbleSize]);

      chart
        .dimension(dimension)
        .group(group)
        .keyAccessor(d => d.key[0])
        .valueAccessor(d => d.key[1])
        .radiusValueAccessor(d => bubbleScale(d.value.size))
        .x(d3.scaleLinear().domain(d3.extent(data, d => d[chartConfig.fields[0]])))
        .y(d3.scaleLinear().domain(d3.extent(data, d => d[chartConfig.fields[1]])))
        .r(d3.scaleLinear().domain([0, d3.max(data, d => d[chartConfig.fields[2]])]))
        .elasticX(true)
        .elasticY(true);
      break;
    default:
      throw new Error('Type ' + chartConfig.type + ' not supported');
  }

  var resetLink = document.createElement('a');
  resetLink.className = 'reset-link button is-small';
  resetLink.innerText = 'Reset';
  resetLink.addEventListener('click', () => resetChart(elementId));
  document.getElementById(elementId).appendChild(resetLink);

  chart.on('renderlet', function (chart) {
    resetLink.style.display = chart.filters().length > 0 ? 'block' : 'none';
  });

  chart.on('filtered', () => {
    updateFiltersSummary();
  });

  return chart;
}

function updateFiltersSummary() {
  filtersList.value = dc.chartRegistry.list().reduce(function (acc, chart) {
    var filters = chart.filters();
    if (filters.length > 0) {
      acc.push({ chart: chart.anchor(), filters: filters });
    }
    return acc;
  }, []);
}

function resetChart(elementId) {
  if (elementId.startsWith('#')) {
    elementId = elementId.slice(1);
  }
  var chart = dc.chartRegistry.list().find(c => c.anchor() === '#' + elementId);
  if (chart) {
    chart.filterAll();
    dc.redrawAll();
  }
}

function initializeDashboard(config) {
  let data = csvParse(props.dataStr);

  dc.chartRegistry.clear();

  data.forEach(function (d) {
    config.charts.forEach(function (chartConfig) {
      if (chartConfig.type === 'date') {
        d[chartConfig.fields] = new Date(d[chartConfig.fields]);
      } else if (chartConfig.type === 'numerical') {
        d[chartConfig.fields] = +d[chartConfig.fields];
      }
    });
  });

  var crossFilterData = crossfilter(data);
  config.charts.map((chartConfig, index) => {
    return generateChart(crossFilterData, chartConfig, index, data);
  });

  dc.renderAll();

  document.getElementById('reset-all').addEventListener('click', function () {
    dc.filterAll();
    dc.redrawAll();
  });
}
</script>
