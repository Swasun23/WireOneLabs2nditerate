from ..database.db import get_db
from ..database.models import AgentsBigPic,Warehouse
import json

def load_json_data(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

warehouse_file_path = "wareHouse_info.json"
agent_file_path = "warehouse_based_agents.json"
session = next(get_db())

warehouse_data = load_json_data(warehouse_file_path)
agent_data = load_json_data(agent_file_path)

try:
    with get_db() as session:
        for warehouse in warehouse_data:
            warehouse_ob = Warehouse(**warehouse)
            session.add(warehouse_ob)
        session.commit()
        print("warehouses added successfully!")
except Exception as e:
    print(f"Error occured: {e}")

try:
    with get_db() as session:
        for agent in agent_data:
            agent_ob = AgentsBigPic(**agent)
            session.add(agent_ob)
        session.commit()
        print("warehouses added successfully!")
except Exception as e:
    print(f"Error occured: {e}")