import falcon
from database.db import get_db
from database.models import OrdersBigPic,Warehouse,AgentsBigPic
from sqlalchemy import and_
from orders_upload.upload_orders import generate_random_orders,upload_warehouse_orders

class UploadRandomOrders:
    def __init__(self, get_db):
        """
        Initialize the resource with a database session provider.

        Args:
            get_db (function): Function to provide a database session.
        """
        self.get_db = get_db

    def on_post(self,req,resp):
        with self.get_db() as db:

            result = generate_random_orders(db)

            if result == 1:  # If orders were successfully generated
                resp.status = falcon.HTTP_200
                resp.media = {"message": "Orders successfully generated and uploaded."}
            else:  # If there was an error during order generation
                resp.status = falcon.HTTP_500
                resp.media = {"message": "Failed to generate orders due to an error."}

class UploadWarehouseOrders:
    def __init__(self, get_db):
        """
        Initialize the resource with a database session provider.

        Args:
            get_db (function): Function to provide a database session.
        """
        self.get_db = get_db

    def on_post(self,req,resp):
        order_dict = req.media
        with self.get_db() as db:

            result = upload_warehouse_orders(db,order_dict)

            if result == 1:  # If orders were successfully generated
                resp.status = falcon.HTTP_200
                resp.media = {"message": "Order successfully uploaded."}
            else:  # If there was an error during order generation
                resp.status = falcon.HTTP_500
                resp.media = {"message": "Failed to generate orders due to an error."}

class OrdersLeft:
    def __init__(self, get_db):
        """
        Initialize the resource with a database session provider.

        Args:
            get_db (function): Function to provide a database session.
        """
        self.get_db = get_db

    def on_get(self,req,resp,):
        with self.get_db() as db:

            warehouses_ids = [warehouse.id for warehouse in db.query(Warehouse).all()]

            orders_info = []
            for warehouse_id in warehouses_ids:
                orders = db.query(OrdersBigPic).filter(and_(OrdersBigPic.is_delivered==False,OrdersBigPic.warehouse_id==warehouse_id)).all()
                no_of_orders = len(orders)
                orders_info.append({
                        "warehouse_id": warehouse_id,
                        "no_of_orders": no_of_orders
                    })
        

            resp.status = falcon.HTTP_200
            resp.media = {"orders": orders_info}

class AgentOrders:
    def __init__(self, get_db):
        """
        Initialize the resource with a database session provider.

        Args:
            get_db (function): Function to provide a database session.
        """
        self.get_db = get_db

    def on_get(self, req, resp, agent_id):
        """Get agent's info for the day"""

        # Get a database session
        with self.get_db() as db:

            # Fetch all orders assigned to the agent
            orders = db.query(OrdersBigPic).filter(OrdersBigPic.assigned_agent_id == agent_id).all()

            # Create a dictionary for quick lookup by order ID
            orders_info_dict = {
                order.id: {
                    "id": order.id,
                    "x_coord": order.x_coord,
                    "y_coord": order.y_coord,
                }
                for order in orders
            }

            # Fetch agent information
            agent_info = db.query(AgentsBigPic).filter(AgentsBigPic.id == agent_id).first()
            if not agent_info:
                raise falcon.HTTPNotFound(description=f"Agent with ID {agent_id} not found")

            # Ensure order_route is not None
            order_route = agent_info.orders or []

            # Create the response list in the order of order_route
            ordered_orders_info = [
                orders_info_dict[order_id] for order_id in order_route if order_id in orders_info_dict
            ]

            resp.status = falcon.HTTP_200
            resp.media = {"orders": ordered_orders_info}