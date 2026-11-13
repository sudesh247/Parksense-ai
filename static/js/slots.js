/**
 * Slots grid management module and booking modal controller.
 */

const SlotsModule = {
  async load() {
    const filters = this.getFilters();
    try {
      const slots = await API.getSlots(filters);
      this.renderGrid(slots);
    } catch (err) {
      UI.showToast(err.message, 'error');
    }
  },

  getFilters() {
    return {
      search: document.getElementById('slot-search')?.value || '',
      floor: document.getElementById('filter-floor')?.value || '',
      status: document.getElementById('filter-status')?.value || '',
      vehicle_type: document.getElementById('filter-vehicle-type')?.value || '',
      is_ev: document.getElementById('filter-ev')?.checked ? 1 : '',
      is_disabled: document.getElementById('filter-disabled')?.checked ? 1 : ''
    };
  },

  renderGrid(slots) {
    const container = document.getElementById('slots-grid');
    if (!container) return;

    if (!slots || slots.length === 0) {
      container.innerHTML = '<div class="text-muted" style="grid-column: 1/-1; padding: 32px; text-align: center;">No parking slots match your filter criteria.</div>';
      return;
    }

    container.innerHTML = slots.map(s => {
      const badgeClass = s.status === 'available' ? 'badge-available' : (s.status === 'occupied' ? 'badge-occupied' : 'badge-reserved');
      const isAvailable = s.status === 'available';

      return `
        <div class="slot-card ${s.status}" ${isAvailable ? `onclick="SlotsModule.openBookingModal(${s.id}, '${s.slot_number}', ${s.floor}, ${s.price_per_hour})"` : ''}>
          <div class="slot-top">
            <span class="slot-number">${s.slot_number}</span>
            <span class="badge ${badgeClass}">${s.status}</span>
          </div>
          <div class="slot-tags">
            ${s.is_ev ? '<span class="tag-icon" title="EV Charger">⚡ EV</span>' : ''}
            ${s.is_disabled_friendly ? '<span class="tag-icon" title="Accessible">♿ Accessible</span>' : ''}
            ${s.near_exit ? '<span class="tag-icon" title="Near Exit">🚪 Near Exit</span>' : ''}
            <span class="tag-icon">${s.vehicle_type.toUpperCase()}</span>
          </div>
          <div class="slot-price">₹${s.price_per_hour}/hr</div>
        </div>
      `;
    }).join('');
  },

  openBookingModal(slotId, slotNumber, floor, price) {
    document.getElementById('modal-slot-id').value = slotId;
    document.getElementById('modal-slot-number').textContent = slotNumber;
    document.getElementById('modal-floor').value = `Floor ${floor}`;
    document.getElementById('modal-price').value = `₹${price}/hr`;
    document.getElementById('modal-vehicle-number').value = '';
    document.getElementById('modal-driver-name').value = '';

    document.getElementById('booking-modal').classList.add('active');
  },

  closeBookingModal() {
    document.getElementById('booking-modal').classList.remove('active');
  },

  initEvents() {
    const inputs = ['slot-search', 'filter-floor', 'filter-status', 'filter-vehicle-type', 'filter-ev', 'filter-disabled'];
    inputs.forEach(id => {
      document.getElementById(id)?.addEventListener('change', () => this.load());
      document.getElementById(id)?.addEventListener('input', () => this.load());
    });

    document.getElementById('btn-clear-filters')?.addEventListener('click', () => {
      inputs.forEach(id => {
        const el = document.getElementById(id);
        if (el.type === 'checkbox') el.checked = false;
        else el.value = '';
      });
      this.load();
    });

    document.getElementById('btn-close-modal')?.addEventListener('click', () => this.closeBookingModal());
    document.getElementById('btn-cancel-modal')?.addEventListener('click', () => this.closeBookingModal());

    document.getElementById('form-create-booking')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const slotId = parseInt(document.getElementById('modal-slot-id').value, 10);
      const vehicleNumber = document.getElementById('modal-vehicle-number').value;
      const vehicleType = document.getElementById('modal-vehicle-type').value;
      const driverName = document.getElementById('modal-driver-name').value;

      try {
        await API.createBooking({ slot_id: slotId, vehicle_number: vehicleNumber, vehicle_type: vehicleType, driver_name: driverName });
        UI.showToast(`Booking created successfully for vehicle ${vehicleNumber}!`, 'success');
        this.closeBookingModal();
        this.load();
        DashboardModule.load();
      } catch (err) {
        UI.showToast(err.message, 'error');
      }
    });
  }
};

document.addEventListener('DOMContentLoaded', () => {
  SlotsModule.initEvents();
});
