import falcon
from database.db import get_db
from database.models import Warehouse,AgentsBigPic
from agent_functions.AgentFunctions import mark_agent_check_in,mark_all_checked_out,mark_Warehouse_agent_check_in,calculate_earnings

class AutoAgentCheckIn:
    def __init__(self, get_db):
        """
        Initialize the resource with a database session provider.

        Args:
            get_db (function): Function to provide a database session.
        """
        self.get_db = get_db

    def on_post(self, req, resp):
        """Randomly mark agents as signed in!"""

        # Get a database session
        with self.get_db() as db:
            
            # Call the function to randomly mark 80% of agents as signed in
            no_present = mark_agent_check_in(db)

            # Respond with the number of agents marked as signed in
            resp.status = falcon.HTTP_200
            resp.media = {"message": f"{no_present} agents have been randomly marked as checked in."}

class WarehouseAgentCheckIn:
    def __init__(self, get_db):
        """
        Initialize the resource with a database session provider.

        Args:
            get_db (function): Function to provide a database session.
        """
        self.get_db = get_db

    def on_post(self, req, resp,warehouse_id,percent):
        """Randomly mark agents as signed in!"""

        # Get a database session
        with self.get_db() as db:
            
            no_present = mark_Warehouse_agent_check_in(db,warehouse_id,percent)

            # Respond with the number of agents marked as signed in
            resp.status = falcon.HTTP_200
            resp.media = {"message": f"{no_present} agents have been randomly marked as checked in."}


class AgentCheckOut:
    def __init__(self, get_db):
        """
        Initialize the resource with a database session provider.

        Args:
            get_db (function): Function to provide a database session.
        """
        self.get_db = get_db

    def on_post(self, req, resp):
        """Randomly mark agents as signed in!"""

        # Get a database session
        with self.get_db() as db:

            # Call the function to randomly mark 80% of agents as signed in
            mark_all_checked_out(db)

            # Respond with the number of agents marked as signed in
            resp.status = falcon.HTTP_200
            resp.media = {"message": f"agents have been marked checked out."}

class AgentsDaySummary:
    def __init__(self, get_db):
        """
        Initialize the resource with a database session provider.

        Args:
            get_db (function): Function to provide a database session.
        """
        self.get_db = get_db

    def on_get(self, req, resp):
        """get agents info for the day"""

        # Get a database session
        with self.get_db() as db:

            agents = db.query(AgentsBigPic).order_by(AgentsBigPic.id).all()

            total_orders = 0
            total_expense = 0
            agents_info = []
            for agent in agents:
                earnings = calculate_earnings(db,agent.id)
                total_expense+=earnings
                total_orders+= agent.no_of_orders
                agents_info.append({
                    "id": agent.id,
                    "no_of_orders": agent.no_of_orders,
                    "total_distance": agent.total_distance,
                    "total_earnings": earnings,
                    "is_checked_in": agent.is_checked_in,
                })
            if total_orders>0:
                cost_per_order = total_expense/total_orders
            else:
                cost_per_order = 0

            resp.status = falcon.HTTP_200
            resp.media = {"agents": agents_info,"total_no_of_orders": total_orders,"cost_per_order":cost_per_order}