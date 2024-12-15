import falcon
from database.db import get_db
from database.models import Warehouse
from warehouse_order_allocation.Order_allocator import OrderAllocator

class AllocateOrdersResource:
    def __init__(self, get_db):
        """
        Initialize the resource with a database session provider.

        Args:
            get_db (function): Function to provide a database session.
        """
        self.get_db = get_db

    def on_post(self, req, resp, warehouse_id):
        """
        Endpoint to allocate orders for a specific warehouse.

        Args:
            warehouse_id (int): ID of the warehouse to allocate orders for.

        Returns:
            JSON: Success message with details about the allocation process.
        """
        # Get a database session
        with self.get_db() as db:
            # Fetch the warehouse by ID
            warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()

            if not warehouse:
                raise falcon.HTTPNotFound(description=f"Warehouse with ID {warehouse_id} not found")

            # Perform order allocation
            order_allocator = OrderAllocator(db, warehouse)
            order_allocator.allocate_orders()

            resp.media = {"message": f"Order allocation completed for warehouse ID {warehouse_id}"}
            resp.status = falcon.HTTP_200


class AllocateAllOrdersResource:
    def __init__(self, get_db):
        """
        Initialize the resource with a database session provider.

        Args:
            get_db (function): Function to provide a database session.
        """
        self.get_db = get_db

    def on_post(self, req, resp):
        """
        Endpoint to allocate orders for all warehouses.

        Returns:
            JSON: Success message with details about the allocation process for all warehouses.
        """
        # Get a database session
        with self.get_db() as db:
            # Fetch all warehouses
            warehouses = db.query(Warehouse).all()

            if not warehouses:
                raise falcon.HTTPNotFound(description="No warehouses found")

            # Perform order allocation for each warehouse
            for warehouse in warehouses:
                order_allocator = OrderAllocator(db, warehouse)
                order_allocator.allocate_orders()

            resp.media = {"message": "Order allocation completed for all warehouses"}
            resp.status = falcon.HTTP_200