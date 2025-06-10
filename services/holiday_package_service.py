from datetime import date
from typing import List, Optional
from models.holiday_package import HolidayPackage
from models.flight import Flight
from models.hotel import Hotel
from models.activity import Activity
from models.price import Price
import uuid
import logging

logger = logging.getLogger(__name__)

class HolidayPackageService:
    def __init__(self):
        self.packages: dict[str, HolidayPackage] = {}

    def create_package(
        self,
        name: str,
        description: str,
        outbound_flight: Flight,
        inbound_flight: Flight,
        hotel: Hotel,
        activities: List[Activity],
        start_date: date,
        end_date: date,
        number_of_guests: int,
        number_of_rooms: int,
        package_type: str
    ) -> HolidayPackage:
        """Create a new holiday package"""
        try:
            package = HolidayPackage(
                id=str(uuid.uuid4()),
                name=name,
                description=description,
                outbound_flight=outbound_flight,
                inbound_flight=inbound_flight,
                hotel=hotel,
                activities=activities,
                start_date=start_date,
                end_date=end_date,
                number_of_guests=number_of_guests,
                number_of_rooms=number_of_rooms,
                package_type=package_type,
                status="Draft",
                created_at=date.today(),
                updated_at=date.today()
            )

            # Calculate total price
            package.total_price = package.calculate_total_price()

            # Validate package
            if not package.validate_package():
                raise ValueError("Invalid package configuration")

            # Store package
            self.packages[package.id] = package
            logger.info(f"Created new holiday package: {package.id}")
            return package

        except Exception as e:
            logger.error(f"Error creating holiday package: {str(e)}")
            raise

    def get_package(self, package_id: str) -> Optional[HolidayPackage]:
        """Retrieve a holiday package by ID"""
        return self.packages.get(package_id)

    def update_package_status(self, package_id: str, new_status: str) -> Optional[HolidayPackage]:
        """Update the status of a holiday package"""
        package = self.get_package(package_id)
        if package:
            package.status = new_status
            package.updated_at = date.today()
            logger.info(f"Updated package {package_id} status to {new_status}")
            return package
        return None

    def update_package_activities(
        self,
        package_id: str,
        activities: List[Activity]
    ) -> Optional[HolidayPackage]:
        """Update the activities in a holiday package"""
        package = self.get_package(package_id)
        if package:
            package.activities = activities
            package.total_price = package.calculate_total_price()
            package.updated_at = date.today()
            logger.info(f"Updated activities for package {package_id}")
            return package
        return None

    def update_package_hotel(
        self,
        package_id: str,
        hotel: Hotel
    ) -> Optional[HolidayPackage]:
        """Update the hotel in a holiday package"""
        package = self.get_package(package_id)
        if package:
            package.hotel = hotel
            package.total_price = package.calculate_total_price()
            package.updated_at = date.today()
            logger.info(f"Updated hotel for package {package_id}")
            return package
        return None

    def update_package_flights(
        self,
        package_id: str,
        outbound_flight: Flight,
        inbound_flight: Flight
    ) -> Optional[HolidayPackage]:
        """Update the flights in a holiday package"""
        package = self.get_package(package_id)
        if package:
            package.outbound_flight = outbound_flight
            package.inbound_flight = inbound_flight
            package.total_price = package.calculate_total_price()
            package.updated_at = date.today()
            logger.info(f"Updated flights for package {package_id}")
            return package
        return None

    def delete_package(self, package_id: str) -> bool:
        """Delete a holiday package"""
        if package_id in self.packages:
            del self.packages[package_id]
            logger.info(f"Deleted package {package_id}")
            return True
        return False

    def get_package_itinerary(self, package_id: str) -> Optional[str]:
        """Generate an itinerary for a holiday package"""
        package = self.get_package(package_id)
        if package:
            return package.generate_itinerary()
        return None

    def list_packages(
        self,
        status: Optional[str] = None,
        package_type: Optional[str] = None
    ) -> List[HolidayPackage]:
        """List all packages with optional filtering"""
        packages = list(self.packages.values())
        
        if status:
            packages = [p for p in packages if p.status == status]
        
        if package_type:
            packages = [p for p in packages if p.package_type == package_type]
            
        return packages
