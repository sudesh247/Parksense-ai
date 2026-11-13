/**
 * API fetch wrappers for ParkSense AI backend endpoints
 * with automatic interactive fallback for GitHub Pages & static previews.
 */

// Initial mock dataset for standalone static web hosting (GitHub Pages)
const MockStore = {
  slots: Array.from({ length: 45 }, (_, i) => {
    const floor = Math.floor(i / 15) + 1;
    const num = (i % 15) + 1;
    const slotNumber = `P-${floor}0${num < 10 ? '0' + num : num}`;
    const status = i % 3 === 0 ? 'occupied' : (i % 7 === 0 ? 'reserved' : 'available');
    return {
      id: i + 1,
      slot_number: slotNumber,
      floor: floor,
      status: status,
      vehicle_type: i % 4 === 0 ? 'ev' : (i % 5 === 0 ? 'motorcycle' : (i % 6 === 0 ? 'suv' : 'car')),
      is_ev: i % 4 === 0 ? 1 : 0,
      is_disabled_friendly: i % 8 === 0 ? 1 : 0,
      near_exit: i % 5 === 0 ? 1 : 0,
      price_per_hour: i % 4 === 0 ? 50 : 30
    };
  }),

  bookings: [
    { id: 101, slot_id: 1, slot_number: 'P-1001', floor: 1, vehicle_number: 'KA-01-AB-1234', vehicle_type: 'car', driver_name: 'Rahul Sharma', entry_time: new Date(Date.now() - 3600000 * 2).toISOString(), exit_time: null, amount: null, status: 'active' },
    { id: 102, slot_id: 4, slot_number: 'P-1004', floor: 1, vehicle_number: 'KA-05-MH-9988', vehicle_type: 'ev', driver_name: 'Priya Nair', entry_time: new Date(Date.now() - 3600000 * 4).toISOString(), exit_time: new Date().toISOString(), amount: 200, status: 'completed' },
    { id: 103, slot_id: 16, slot_number: 'P-2001', floor: 2, vehicle_number: 'DL-03-CC-4455', vehicle_type: 'suv', driver_name: 'Amit Patel', entry_time: new Date(Date.now() - 3600000 * 1.5).toISOString(), exit_time: null, amount: null, status: 'active' }
  ],

  getStats() {
    const total = this.slots.length;
    const occupied = this.slots.filter(s => s.status === 'occupied').length;
    const reserved = this.slots.filter(s => s.status === 'reserved').length;
    const available = total - occupied - reserved;
    const evTotal = this.slots.filter(s => s.is_ev).length;
    const evAvailable = this.slots.filter(s => s.is_ev && s.status === 'available').length;

    const floors = [1, 2, 3].map(f => {
      const fSlots = this.slots.filter(s => s.floor === f);
      const fTotal = fSlots.length;
      const fOcc = fSlots.filter(s => s.status === 'occupied').length;
      const fRes = fSlots.filter(s => s.status === 'reserved').length;
      const fAvail = fTotal - fOcc - fRes;
      return {
        floor: f,
        total_slots: fTotal,
        available_slots: fAvail,
        occupied_slots: fOcc,
        reserved_slots: fRes,
        occupancy_percentage: Math.round((fOcc / fTotal) * 100)
      };
    });

    return {
      total_slots: total,
      occupied_slots: occupied,
      reserved_slots: reserved,
      available_slots: available,
      overall_occupancy_percentage: Math.round((occupied / total) * 100),
      today_revenue: 3450,
      average_ticket_value: 45.0,
      currently_active_vehicles: occupied,
      ev_slots: { total: evTotal, available: evAvailable },
      today_bookings_count: 18,
      occupancy_by_floor: floors,
      revenue_trend: [
        { date: 'Mon', revenue: 2100 },
        { date: 'Tue', revenue: 2800 },
        { date: 'Wed', revenue: 3100 },
        { date: 'Thu', revenue: 2900 },
        { date: 'Fri', revenue: 4200 },
        { date: 'Sat', revenue: 4800 },
        { date: 'Sun', revenue: 3450 }
      ],
      vehicle_movement: [
        { label: '08:00', entries: 12, exits: 3 },
        { label: '10:00', entries: 25, exits: 8 },
        { label: '12:00', entries: 18, exits: 15 },
        { label: '14:00', entries: 14, exits: 20 },
        { label: '16:00', entries: 22, exits: 10 },
        { label: '18:00', entries: 30, exits: 25 }
      ]
    };
  }
};

const API = {
  async getHealth() {
    try {
      const res = await fetch('/api/health');
      if (res.ok) return await res.json();
    } catch (e) {}
    return { status: 'healthy', mode: 'demo_static' };
  },

  async getStatistics() {
    try {
      const res = await fetch('/api/statistics');
      if (res.ok) return await res.json();
    } catch (e) {}
    return MockStore.getStats();
  },

  async getSlots(filters = {}) {
    try {
      const params = new URLSearchParams();
      if (filters.floor) params.append('floor', filters.floor);
      if (filters.status) params.append('status', filters.status);
      if (filters.vehicle_type) params.append('vehicle_type', filters.vehicle_type);
      if (filters.is_ev !== undefined && filters.is_ev !== '') params.append('is_ev', filters.is_ev);
      if (filters.is_disabled !== undefined && filters.is_disabled !== '') params.append('is_disabled_friendly', filters.is_disabled);
      if (filters.search) params.append('search', filters.search);

      const res = await fetch(`/api/slots?${params.toString()}`);
      if (res.ok) return await res.json();
    } catch (e) {}

    let slots = [...MockStore.slots];
    if (filters.floor) slots = slots.filter(s => s.floor === parseInt(filters.floor, 10));
    if (filters.status) slots = slots.filter(s => s.status === filters.status);
    if (filters.vehicle_type) slots = slots.filter(s => s.vehicle_type === filters.vehicle_type);
    if (filters.is_ev) slots = slots.filter(s => s.is_ev === 1);
    if (filters.is_disabled) slots = slots.filter(s => s.is_disabled_friendly === 1);
    if (filters.search) {
      const q = filters.search.toLowerCase();
      slots = slots.filter(s => s.slot_number.toLowerCase().includes(q));
    }
    return slots;
  },

  async getFloors() {
    try {
      const res = await fetch('/api/floors');
      if (res.ok) return await res.json();
    } catch (e) {}
    return [1, 2, 3];
  },

  async createBooking(bookingData) {
    try {
      const res = await fetch('/api/bookings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(bookingData)
      });
      if (res.ok) return await res.json();
    } catch (e) {}

    const slot = MockStore.slots.find(s => s.id === bookingData.slot_id);
    if (slot) slot.status = 'occupied';

    const newBooking = {
      id: MockStore.bookings.length + 101,
      slot_id: bookingData.slot_id,
      slot_number: slot ? slot.slot_number : `P-${bookingData.slot_id}`,
      floor: slot ? slot.floor : 1,
      vehicle_number: bookingData.vehicle_number || 'UNKNOWN',
      vehicle_type: bookingData.vehicle_type || 'car',
      driver_name: bookingData.driver_name || 'Driver',
      entry_time: new Date().toISOString(),
      exit_time: null,
      amount: null,
      status: 'active'
    };
    MockStore.bookings.unshift(newBooking);
    return newBooking;
  },

  async getBookings(status = '') {
    try {
      const url = status ? `/api/bookings?status=${encodeURIComponent(status)}` : '/api/bookings';
      const res = await fetch(url);
      if (res.ok) return await res.json();
    } catch (e) {}

    if (status) return MockStore.bookings.filter(b => b.status === status);
    return MockStore.bookings;
  },

  async releaseBooking(bookingId) {
    try {
      const res = await fetch(`/api/bookings/${bookingId}/release`, { method: 'PUT' });
      if (res.ok) return await res.json();
    } catch (e) {}

    const booking = MockStore.bookings.find(b => b.id === bookingId);
    if (booking) {
      booking.status = 'completed';
      booking.exit_time = new Date().toISOString();
      booking.amount = 120;
      const slot = MockStore.slots.find(s => s.id === booking.slot_id);
      if (slot) slot.status = 'available';
    }
    return booking || { amount: 120, status: 'completed' };
  },

  async cancelBooking(bookingId) {
    try {
      const res = await fetch(`/api/bookings/${bookingId}`, { method: 'DELETE' });
      if (res.ok) return await res.json();
    } catch (e) {}

    const booking = MockStore.bookings.find(b => b.id === bookingId);
    if (booking) {
      booking.status = 'cancelled';
      const slot = MockStore.slots.find(s => s.id === booking.slot_id);
      if (slot) slot.status = 'available';
    }
    return { detail: 'Booking cancelled' };
  },

  async sendChatMessage(question) {
    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question })
      });
      if (res.ok) return await res.json();
    } catch (e) {}

    // Smart fallback responses for static preview mode
    const q = question.toLowerCase();
    let answer = "ParkSense AI: Parking lot currently has 68% occupancy with 16 spots available. Floor 1 is best for EV charging.";
    let docs = ["parking_policy.md", "pricing_rules.json"];

    if (q.includes("rate") || q.includes("price") || q.includes("fee") || q.includes("cost")) {
      answer = "Standard parking rate is ₹30/hr for Cars/SUVs and Motorcycles. EV Charging slots are ₹50/hr including charging access.";
      docs = ["pricing_rules.json"];
    } else if (q.includes("ev") || q.includes("electric") || q.includes("charge")) {
      answer = "We have 10 dedicated EV charging slots across Floor 1 & Floor 2 equipped with 22kW fast chargers. 4 EV slots are currently free.";
      docs = ["ev_facilities.md"];
    } else if (q.includes("available") || q.includes("free") || q.includes("slot")) {
      answer = "There are 16 available parking spots right now: 4 on Floor 1, 5 on Floor 2, and 7 on Floor 3.";
      docs = ["realtime_occupancy.json"];
    } else if (q.includes("booking") || q.includes("reserve")) {
      answer = "You can instantly reserve any green available slot directly from the Slots tab on this dashboard! Just click on a green slot card to book.";
      docs = ["user_guide.md"];
    }

    return { answer, retrieved_docs: docs };
  }
};

