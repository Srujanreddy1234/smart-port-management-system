const ChartFactory = {
  defaults: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: {
          color: '#8b92a5',
          font: { family: "'Poppins', sans-serif", size: 12 },
          padding: 16
        }
      },
      tooltip: {
        backgroundColor: '#1a1d29',
        titleColor: '#e4e7f1',
        bodyColor: '#8b92a5',
        borderColor: '#2a2e3f',
        borderWidth: 1,
        cornerRadius: 8,
        padding: 12,
        titleFont: { family: "'Poppins', sans-serif", weight: 600 },
        bodyFont: { family: "'Poppins', sans-serif" }
      }
    },
    scales: {
      x: {
        grid: { color: 'rgba(42,46,63,0.5)', drawBorder: false },
        ticks: { color: '#5f6680', font: { family: "'Poppins', sans-serif", size: 11 } }
      },
      y: {
        grid: { color: 'rgba(42,46,63,0.5)', drawBorder: false },
        ticks: { color: '#5f6680', font: { family: "'Poppins', sans-serif", size: 11 } }
      }
    }
  },

  colors: {
    primary: 'rgba(13,110,253,0.8)',
    primaryBg: 'rgba(13,110,253,0.1)',
    success: 'rgba(25,135,84,0.8)',
    successBg: 'rgba(25,135,84,0.1)',
    danger: 'rgba(220,53,69,0.8)',
    dangerBg: 'rgba(220,53,69,0.1)',
    warning: 'rgba(255,193,7,0.8)',
    warningBg: 'rgba(255,193,7,0.1)',
    info: 'rgba(13,202,240,0.8)',
    infoBg: 'rgba(13,202,240,0.1)',
    purple: 'rgba(102,16,242,0.8)',
    purpleBg: 'rgba(102,16,242,0.1)',
    teal: 'rgba(32,201,151,0.8)',
    tealBg: 'rgba(32,201,151,0.1)',
    gradient1: (ctx) => {
      const g = ctx.chart.ctx.createLinearGradient(0, 0, 0, 300);
      g.addColorStop(0, 'rgba(13,110,253,0.3)');
      g.addColorStop(1, 'rgba(13,110,253,0.0)');
      return g;
    },
    gradient2: (ctx) => {
      const g = ctx.chart.ctx.createLinearGradient(0, 0, 0, 300);
      g.addColorStop(0, 'rgba(25,135,84,0.3)');
      g.addColorStop(1, 'rgba(25,135,84,0.0)');
      return g;
    }
  },

  create(canvasId, type, data, customOptions = {}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;
    const options = this.mergeOptions(type, customOptions);
    return new Chart(canvas.getContext('2d'), { type, data, options });
  },

  mergeOptions(type, custom) {
    const base = JSON.parse(JSON.stringify(this.defaults));
    if (type === 'doughnut' || type === 'pie') {
      delete base.scales;
    }
    return this.deepMerge(base, custom);
  },

  deepMerge(target, source) {
    const output = Object.assign({}, target);
    for (const key in source) {
      if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
        output[key] = this.deepMerge(output[key] || {}, source[key]);
      } else {
        output[key] = source[key];
      }
    }
    return output;
  },

  createLineChart(canvasId, labels, datasets, options = {}) {
    const data = {
      labels,
      datasets: datasets.map((ds, i) => ({
        label: ds.label,
        data: ds.data,
        borderColor: Object.values(this.colors)[i * 2],
        backgroundColor: ds.fill ? this.colors.gradient1({ chart: { ctx: document.getElementById(canvasId)?.getContext('2d') } }) : 'transparent',
        borderWidth: 2,
        tension: 0.4,
        fill: ds.fill || false,
        pointRadius: ds.pointRadius ?? 3,
        pointHoverRadius: 5,
        ...ds
      }))
    };
    return this.create(canvasId, 'line', data, options);
  },

  createBarChart(canvasId, labels, datasets, options = {}) {
    const colorKeys = ['primary', 'success', 'warning', 'danger', 'info', 'purple', 'teal'];
    const data = {
      labels,
      datasets: datasets.map((ds, i) => ({
        backgroundColor: this.colors[colorKeys[i % colorKeys.length]],
        borderRadius: 6,
        borderSkipped: false,
        ...ds
      }))
    };
    return this.create(canvasId, 'bar', data, options);
  },

  createDoughnutChart(canvasId, labels, dataValues, colors) {
    const colorKeys = colors || ['primary', 'success', 'warning', 'danger', 'info', 'purple'];
    const data = {
      labels,
      datasets: [{
        data: dataValues,
        backgroundColor: colorKeys.map(c => this.colors[c]),
        borderWidth: 0,
        hoverOffset: 8
      }]
    };
    return this.create(canvasId, 'doughnut', data, {
      cutout: '70%',
      plugins: {
        legend: { position: 'bottom' }
      }
    });
  },

  createAreaChart(canvasId, labels, datasets, options = {}) {
    const colorKeys = ['primary', 'success', 'info', 'warning'];
    const ctx = document.getElementById(canvasId)?.getContext('2d');
    const data = {
      labels,
      datasets: datasets.map((ds, i) => ({
        borderColor: this.colors[colorKeys[i % colorKeys.length]],
        backgroundColor: this.colors.gradient1({ chart: { ctx } }),
        borderWidth: 2,
        tension: 0.4,
        fill: true,
        pointRadius: 0,
        ...ds
      }))
    };
    return this.create(canvasId, 'line', data, options);
  }
};
