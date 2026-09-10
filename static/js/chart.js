/**
 * chart.js - Lightweight Canvas Chart Engine
 * Zero dependencies - renders line, bar, and gauge charts on Canvas
 */

class FatigueChart {
  constructor(canvasId, options = {}) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');
    this.dpr = window.devicePixelRatio || 1;
    this.options = {
      bgColor: 'transparent',
      gridColor: 'rgba(99, 102, 241, 0.08)',
      textColor: '#6B7280',
      lineColor: '#6366F1',
      fillColor: 'rgba(99, 102, 241, 0.1)',
      pointColor: '#6366F1',
      pointBorderColor: '#ffffff',
      fontFamily: "'Inter', sans-serif",
      ...options
    };
    this.data = [];
    this.labels = [];
    this._resize();
  }

  _resize() {
    const rect = this.canvas.getBoundingClientRect();
    this.canvas.width = rect.width * this.dpr;
    this.canvas.height = rect.height * this.dpr;
    this.ctx.scale(this.dpr, this.dpr);
    this.width = rect.width;
    this.height = rect.height;
  }

  setData(data, labels) {
    this.data = data;
    this.labels = labels || data.map((_, i) => i.toString());
    this._resize();
    this.render();
  }

  addPoint(value, label = '') {
    this.data.push(value);
    this.labels.push(label || (this.data.length).toString());
    this.render();
  }

  clear() {
    this.data = [];
    this.labels = [];
    this.render();
  }

  render() {
    const ctx = this.ctx;
    const { width, height } = this;
    const pad = { top: 20, right: 20, bottom: 30, left: 40 };
    const chartW = width - pad.left - pad.right;
    const chartH = height - pad.top - pad.bottom;

    ctx.clearRect(0, 0, width, height);

    if (this.data.length === 0) {
      ctx.fillStyle = this.options.textColor;
      ctx.font = `14px ${this.options.fontFamily}`;
      ctx.textAlign = 'center';
      ctx.fillText('No data collected yet', width / 2, height / 2);
      return;
    }

    const min = Math.min(...this.data) * 0.9;
    const max = Math.max(...this.data) * 1.1 || 1;
    const range = max - min || 1;

    // Grid lines
    ctx.strokeStyle = this.options.gridColor;
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const y = pad.top + (chartH * i) / 4;
      ctx.beginPath();
      ctx.moveTo(pad.left, y);
      ctx.lineTo(pad.left + chartW, y);
      ctx.stroke();

      const val = max - (range * i) / 4;
      ctx.fillStyle = this.options.textColor;
      ctx.font = `11px ${this.options.fontFamily}`;
      ctx.textAlign = 'right';
      ctx.fillText(val.toFixed(1), pad.left - 8, y + 4);
    }

    // Draw line + fill
    const stepX = chartW / Math.max(this.data.length - 1, 1);
    
    // Fill area
    ctx.beginPath();
    ctx.moveTo(pad.left, pad.top + chartH);
    this.data.forEach((val, i) => {
      const x = pad.left + i * stepX;
      const y = pad.top + chartH - ((val - min) / range) * chartH;
      ctx.lineTo(x, y);
    });
    ctx.lineTo(pad.left + (this.data.length - 1) * stepX, pad.top + chartH);
    ctx.closePath();
    ctx.fillStyle = this.options.fillColor;
    ctx.fill();

    // Line
    ctx.beginPath();
    this.data.forEach((val, i) => {
      const x = pad.left + i * stepX;
      const y = pad.top + chartH - ((val - min) / range) * chartH;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.strokeStyle = this.options.lineColor;
    ctx.lineWidth = 2.5;
    ctx.lineJoin = 'round';
    ctx.stroke();

    // Points
    this.data.forEach((val, i) => {
      const x = pad.left + i * stepX;
      const y = pad.top + chartH - ((val - min) / range) * chartH;
      
      ctx.beginPath();
      ctx.arc(x, y, 4, 0, Math.PI * 2);
      ctx.fillStyle = this.options.pointColor;
      ctx.fill();
      
      ctx.beginPath();
      ctx.arc(x, y, 2, 0, Math.PI * 2);
      ctx.fillStyle = this.options.pointBorderColor;
      ctx.fill();
    });

    // X-axis labels (show first, middle, last)
    if (this.labels.length > 1) {
      const indices = [0, Math.floor(this.labels.length / 2), this.labels.length - 1];
      indices.forEach(i => {
        const x = pad.left + i * stepX;
        ctx.fillStyle = this.options.textColor;
        ctx.font = `10px ${this.options.fontFamily}`;
        ctx.textAlign = 'center';
        ctx.fillText(this.labels[i], x, height - 5);
      });
    }
  }
}

class GaugeChart {
  constructor(canvasId, options = {}) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');
    this.dpr = window.devicePixelRatio || 1;
    this.value = 0;
    this.maxValue = 100;
    this.label = '';
    this.options = {
      arcColor: '#6366F1',
      trackColor: 'rgba(99, 102, 241, 0.1)',
      textColor: '#111827',
      subTextColor: '#6B7280',
      fontFamily: "'Inter', sans-serif",
      ...options
    };
    this._resize();
  }

  _resize() {
    const rect = this.canvas.getBoundingClientRect();
    this.canvas.width = rect.width * this.dpr;
    this.canvas.height = rect.height * this.dpr;
    this.ctx.scale(this.dpr, this.dpr);
    this.width = rect.width;
    this.height = rect.height;
  }

  setValue(val, maxVal = 100, label = '') {
    this.value = val;
    this.maxValue = maxVal || 100;
    this.label = label;
    this.render();
  }

  render() {
    const ctx = this.ctx;
    const { width, height } = this;
    const cx = width / 2;
    const cy = height * 0.6;
    const radius = Math.min(width, height * 1.2) * 0.35;
    const lineWidth = Math.max(8, radius * 0.15);
    const progress = Math.min(this.value / this.maxValue, 1);

    ctx.clearRect(0, 0, width, height);

    // Track arc
    ctx.beginPath();
    ctx.arc(cx, cy, radius, 0.75 * Math.PI, 2.25 * Math.PI);
    ctx.strokeStyle = this.options.trackColor;
    ctx.lineWidth = lineWidth;
    ctx.lineCap = 'round';
    ctx.stroke();

    // Value arc
    const endAngle = 0.75 * Math.PI + progress * 1.5 * Math.PI;
    ctx.beginPath();
    ctx.arc(cx, cy, radius, 0.75 * Math.PI, endAngle);
    ctx.strokeStyle = this.options.arcColor;
    ctx.lineWidth = lineWidth;
    ctx.lineCap = 'round';
    ctx.stroke();

    // Glow effect
    ctx.beginPath();
    ctx.arc(cx, cy, radius, 0.75 * Math.PI, endAngle);
    ctx.strokeStyle = this.options.arcColor.replace(')', ', 0.3)').replace('rgb', 'rgba');
    ctx.lineWidth = lineWidth + 6;
    ctx.lineCap = 'round';
    ctx.globalAlpha = 0.2;
    ctx.stroke();
    ctx.globalAlpha = 1;

    // Value text
    ctx.fillStyle = this.options.textColor;
    ctx.font = `bold ${radius * 0.5}px ${this.options.fontFamily}`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(Math.round(this.value) + '%', cx, cy - radius * 0.15);

    // Label
    if (this.label) {
      ctx.fillStyle = this.options.subTextColor;
      ctx.font = `${radius * 0.18}px ${this.options.fontFamily}`;
      ctx.fillText(this.label, cx, cy + radius * 0.35);
    }
  }
}

// Export for use in app.js
window.FatigueChart = FatigueChart;
window.GaugeChart = GaugeChart;
