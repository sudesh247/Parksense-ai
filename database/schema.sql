-- Schema definition for ParkSense AI

CREATE TABLE IF NOT EXISTS slots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slot_number TEXT UNIQUE NOT NULL,
    floor INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('available', 'occupied', 'reserved')),
    price_per_hour REAL NOT NULL,
    vehicle_type TEXT NOT NULL CHECK (vehicle_type IN ('car', 'bike', 'suv')),
    is_ev INTEGER NOT NULL CHECK (is_ev IN (0, 1)),
    near_exit INTEGER NOT NULL CHECK (near_exit IN (0, 1)),
    is_reserved INTEGER NOT NULL CHECK (is_reserved IN (0, 1)),
    is_disabled_friendly INTEGER NOT NULL CHECK (is_disabled_friendly IN (0, 1))
);

CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slot_id INTEGER NOT NULL,
    vehicle_number TEXT NOT NULL,
    vehicle_type TEXT NOT NULL,
    driver_name TEXT,
    entry_time TEXT NOT NULL,
    exit_time TEXT,
    amount REAL,
    status TEXT NOT NULL CHECK (status IN ('active', 'completed', 'cancelled')),
    FOREIGN KEY (slot_id) REFERENCES slots (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_slots_floor ON slots(floor);
CREATE INDEX IF NOT EXISTS idx_slots_status ON slots(status);
CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings(status);
CREATE INDEX IF NOT EXISTS idx_bookings_entry_time ON bookings(entry_time);
