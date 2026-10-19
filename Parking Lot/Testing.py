import time
from ParkingLot import ParkingLot
from ParkingSpot import ParkingSpot, SpotType
from Ticket import VehicleType

# Create parking spots
spots = [
    ParkingSpot("M1", SpotType.MOTORCYCLE),
    ParkingSpot("C1", SpotType.CAR),
    ParkingSpot("L1", SpotType.LARGE),
]

# Create parking lot: 500 cents = 5 currency units per hour
lot = ParkingLot(spots, hourly_rate_cents=500)

# Test 1: A car enters
ticket = lot.enter(VehicleType.CAR)
print("1. Car entered successfully")
print("   Ticket ID:", ticket.get_id())
print("   Spot ID:", ticket.get_spot_id())

# Wait so we can test the parking fee
time.sleep(2)

# Test 2: Car exits
fee = lot.exit(ticket.get_id())
print("2. Car exited successfully")
print("   Fee:", fee, "cents")

# Test 3: Reusing the same ticket should fail
try:
    lot.exit(ticket.get_id())
except Exception as e:
    print("3. Invalid exit handled:", e)

# Test 4: A motorcycle enters
bike_ticket = lot.enter(VehicleType.MOTORCYCLE)
print("4. Motorcycle entered successfully")
print("   Spot ID:", bike_ticket.get_spot_id())
