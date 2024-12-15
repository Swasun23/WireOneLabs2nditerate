import json
import falcon
from sqlalchemy.orm import Session
from database.db import get_db
from database.models import Warehouse, AgentsBigPic
import os

class LoadDataResource:
    def __init__(self):
        # Hardcoded file paths
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))  # Go up to the project root
        self.warehouse_file_path = os.path.join(base_dir, "data", "wareHouse_info.json")
        self.agent_file_path = os.path.join(base_dir, "data", "warehouse_based_agents.json")

    def load_json_data(self, file_path):
        try:
            with open(file_path, 'r') as file:
                return json.load(file)
        except Exception as e:
            raise falcon.HTTPBadRequest(
                title="File Error",
                description=f"Failed to load file: {file_path}. Error: {e}"
            )

    def on_post(self, req, resp):
        # Load JSON data from hardcoded files
        try:
            warehouse_data = self.load_json_data(self.warehouse_file_path)
            agent_data = self.load_json_data(self.agent_file_path)
        except falcon.HTTPBadRequest as e:
            raise e

        # Insert data into the database
        try:
            with get_db() as session:
                # Add warehouses
                for warehouse in warehouse_data:
                    warehouse_ob = Warehouse(**warehouse)
                    session.add(warehouse_ob)
                session.commit()
                print("Warehouses added successfully!")

        except Exception as e:
            raise falcon.HTTPInternalServerError(
                title="Database Error",
                description=f"Failed to add warehouse data. Error: {e}"
            )

        try:
            with get_db() as session:
                # Add agents
                for agent in agent_data:
                    agent_ob = AgentsBigPic(**agent)
                    session.add(agent_ob)
                session.commit()
                print("Agents added successfully!")

        except Exception as e:
            raise falcon.HTTPInternalServerError(
                title="Database Error",
                description=f"Failed to add agent data. Error: {e}"
            )

        # Response
        resp.status = falcon.HTTP_200
        resp.media = {"message": "Data loaded successfully!"}
