/**
 * Dashboard module for stat cards, Plotly charts, and floor overview table.
 */

const DashboardModule = {
  async load() {
    try {
      const data = await API.getStatistics();
      this.renderStatCards(data);
      this.renderFloorTable(data.occupancy_by_floor);
      this.renderRevenueTrendChart(data.revenue_trend);
      this.renderOccupancyFloorChart(data.occupancy_by_floor);
      this.renderVehicleMovementChart(data.vehicle_movement);
    } catch (err) {
      UI.showToast(err.message, 'error');
    }
  },

  renderStatCards(d) {
    document.getElementById('stat-occupancy').textContent = `${d.overall_occupancy_percentage}%`;
    document.getElementById('stat-occupancy-sub').textContent = `${d.occupied_slots} / ${d.total_slots} slots filled`;

    document.getElementById('stat-revenue').textContent = UI.formatCurrency(d.today_revenue);
    document.getElementById('stat-revenue-sub').textContent = `Avg ticket: ${UI.formatCurrency(d.average_ticket_value)}`;

    document.getElementById('stat-active-vehicles').textContent = d.currently_active_vehicles;
    document.getElementById('stat-available-slots').textContent = d.available_slots;

    document.getElementById('stat-ev-slots').textContent = `${d.ev_slots.available} / ${d.ev_slots.total}`;
    document.getElementById('stat-today-bookings').textContent = d.today_bookings_count;
  },

  renderFloorTable(floors) {
    const tbody = document.getElementById('floor-breakdown-tbody');
    if (!tbody) return;

    if (!floors || floors.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" class="text-muted">No floor data available</td></tr>';
      return;
    }

    tbody.innerHTML = floors.map(f => `
      <tr>
        <td><strong>Floor ${f.floor}</strong></td>
        <td class="mono">${f.total_slots}</td>
        <td class="mono text-success">${f.available_slots}</td>
        <td class="mono text-danger">${f.occupied_slots}</td>
        <td class="mono text-warning">${f.reserved_slots}</td>
        <td>
          <span class="badge ${f.occupancy_percentage > 75 ? 'badge-occupied' : 'badge-available'}">
            ${f.occupancy_percentage}%
          </span>
        </td>
      </tr>
    `).join('');
  },

  renderRevenueTrendChart(trend) {
    const container = document.getElementById('chart-revenue-trend');
    if (!container || !trend) return;

    const trace = {
      x: trend.map(t => t.date),
      y: trend.map(t => t.revenue),
      type: 'scatter',
      mode: 'lines+markers',
      line: { color: '#3b82f6', width: 3, shape: 'spline' },
      marker: { color: '#3b82f6', size: 6 },
      fill: 'tozeroy',
      fillcolor: 'rgba(59, 130, 246, 0.1)'
    };

    const layout = {
      margin: { t: 10, r: 20, l: 40, b: 40 },
      paper_bgcolor: 'transparent',
      plot_bgcolor: 'transparent',
      font: { color: '#94a3b8', family: 'Inter' },
      xaxis: { showgrid: false, color: '#64748b' },
      yaxis: { gridcolor: '#1e293b', color: '#64748b' }
    };

    Plotly.newPlot(container, [trace], layout, { responsive: true, displayModeBar: false });
  },

  renderOccupancyFloorChart(floors) {
    const container = document.getElementById('chart-occupancy-floor');
    if (!container || !floors) return;

    const trace = {
      x: floors.map(f => `Floor ${f.floor}`),
      y: floors.map(f => f.occupancy_percentage),
      type: 'bar',
      marker: { color: '#10b981', cornerradius: 4 }
    };

    const layout = {
      margin: { t: 10, r: 20, l: 40, b: 40 },
      paper_bgcolor: 'transparent',
      plot_bgcolor: 'transparent',
      font: { color: '#94a3b8', family: 'Inter' },
      xaxis: { showgrid: false },
      yaxis: { gridcolor: '#1e293b', range: [0, 100], suffix: '%' }
    };

    Plotly.newPlot(container, [trace], layout, { responsive: true, displayModeBar: false });
  },

  renderVehicleMovementChart(movement) {
    const container = document.getElementById('chart-vehicle-movement');
    if (!container || !movement) return;

    const entriesTrace = {
      x: movement.map(m => m.label),
      y: movement.map(m => m.entries),
      name: 'Entries',
      type: 'bar',
      marker: { color: '#3b82f6' }
    };

    const exitsTrace = {
      x: movement.map(m => m.label),
      y: movement.map(m => m.exits),
      name: 'Exits',
      type: 'bar',
      marker: { color: '#f59e0b' }
    };

    const layout = {
      barmode: 'group',
      margin: { t: 10, r: 20, l: 40, b: 40 },
      paper_bgcolor: 'transparent',
      plot_bgcolor: 'transparent',
      font: { color: '#94a3b8', family: 'Inter' },
      legend: { orientation: 'h', x: 0, y: 1.1 },
      xaxis: { showgrid: false },
      yaxis: { gridcolor: '#1e293b' }
    };

    Plotly.newPlot(container, [entriesTrace, exitsTrace], layout, { responsive: true, displayModeBar: false });
  }
};

document.addEventListener('DOMContentLoaded', () => {
  DashboardModule.load();
});
