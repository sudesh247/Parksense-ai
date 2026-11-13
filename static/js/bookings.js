/**
 * Bookings module for table rendering, release, and cancellation actions.
 */

const BookingsModule = {
  async load() {
    const statusFilter = document.getElementById('booking-status-filter')?.value || '';
    try {
      const bookings = await API.getBookings(statusFilter);
      this.renderTable(bookings);
    } catch (err) {
      UI.showToast(err.message, 'error');
    }
  },

  renderTable(bookings) {
    const tbody = document.getElementById('bookings-tbody');
    if (!tbody) return;

    if (!bookings || bookings.length === 0) {
      tbody.innerHTML = '<tr><td colspan="10" class="text-muted" style="text-align: center; padding: 24px;">No bookings found.</td></tr>';
      return;
    }

    tbody.innerHTML = bookings.map(b => {
      const isActive = b.status === 'active';
      return `
        <tr>
          <td class="mono">#${b.id}</td>
          <td><strong class="mono">${b.slot_number}</strong> (F${b.floor})</td>
          <td class="mono">${b.vehicle_number}</td>
          <td><span class="tag-icon">${b.vehicle_type.toUpperCase()}</span></td>
          <td>${b.driver_name || '<span class="text-dim">N/A</span>'}</td>
          <td class="mono">${UI.formatDateTime(b.entry_time)}</td>
          <td class="mono">${b.exit_time ? UI.formatDateTime(b.exit_time) : '<span class="text-dim">Active</span>'}</td>
          <td class="mono">${b.amount !== null && b.amount !== undefined ? UI.formatCurrency(b.amount) : '<span class="text-dim">Pending</span>'}</td>
          <td><span class="badge badge-${b.status}">${b.status}</span></td>
          <td>
            ${isActive ? `
              <button class="btn btn-sm btn-primary" onclick="BookingsModule.handleRelease(${b.id}, '${b.slot_number}')">Release</button>
              <button class="btn btn-sm btn-danger" onclick="BookingsModule.handleCancel(${b.id})">Cancel</button>
            ` : '<span class="text-dim">None</span>'}
          </td>
        </tr>
      `;
    }).join('');
  },

  async handleRelease(bookingId, slotNumber) {
    if (!confirm(`Are you sure you want to end booking #${bookingId} for slot ${slotNumber}?`)) return;
    try {
      const released = await API.releaseBooking(bookingId);
      UI.showToast(`Booking #${bookingId} released! Total Fee: ${UI.formatCurrency(released.amount)}`, 'success');
      this.load();
      DashboardModule.load();
    } catch (err) {
      UI.showToast(err.message, 'error');
    }
  },

  async handleCancel(bookingId) {
    if (!confirm(`Are you sure you want to cancel active booking #${bookingId}?`)) return;
    try {
      await API.cancelBooking(bookingId);
      UI.showToast(`Booking #${bookingId} cancelled. Slot released.`, 'success');
      this.load();
      DashboardModule.load();
    } catch (err) {
      UI.showToast(err.message, 'error');
    }
  },

  initEvents() {
    document.getElementById('booking-status-filter')?.addEventListener('change', () => this.load());
  }
};

document.addEventListener('DOMContentLoaded', () => {
  BookingsModule.initEvents();
});
