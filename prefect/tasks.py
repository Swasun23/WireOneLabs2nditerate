from prefect import task
import requests
from prefect.artifacts import create_table_artifact,create_markdown_artifact
from dotenv import load_dotenv
import os

load_dotenv()

BASE_URL = os.getenv("BASE_URL")

@task
def upload_orders():
    response = requests.post(f"{BASE_URL}/upload-orders/")
    print(f"{BASE_URL}/upload_orders/")
    return response.json()

@task
def agent_checkin():
    response = requests.post(f"{BASE_URL}/auto-checkin/")
    return response.json()

@task
def order_allocation():
    response = requests.post(f"{BASE_URL}/allocate-all-orders")
    return response.json()

from prefect.artifacts import create_table_artifact

@task
def show_agent_day_info():
    response = requests.get(f"{BASE_URL}/agents-day-summary")
    agent_info = response.json()
    
    rows = [
        {
            "Agent ID": agent["id"],
            "no_of_orders": agent["no_of_orders"],
            "total_distance": agent["total_distance"],
            "total_earnings": agent["total_earnings"],
            "is_checked_in": agent["is_checked_in"]
        }
        for agent in agent_info.get("agents", [])
    ]

    create_table_artifact(
        key="agents-daily-summary",
        table=rows,
        description="Agents daily summary"
    )

    total_orders = agent_info.get("total_no_of_orders",0)
    cost_per_order = agent_info.get("cost_per_order",0)

    summary_markdown = f"""
    ## Daily Summary
    - **Total Orders:** {total_orders}
    - **Cost per Order Ratio:** {cost_per_order:.2f} rupees
    """
    create_markdown_artifact(
        key="daily-summary",
        markdown=summary_markdown,
        description="Daily summary of agent activity"
    )

    return agent_info

@task
def show_orders_by_agent(agent_id):
    try:
        response = requests.get(f"{BASE_URL}/assigned-orders/{agent_id}")
        orders_info = response.json()
        rows = [
            {
                "id": order["id"],
                "x_coord": order["x_coord"],
                "y_coord": order["y_coord"]
            }
            for order in orders_info.get("orders", [])
        ]

        create_table_artifact(
            key=f"agent-{agent_id}-orders",
            table=rows,
            description=f"List of orders for agent-{agent_id}"
        )
        return 1
    except Exception as e:
        return 0 

@task
def orders_left():
    response = requests.get(f"{BASE_URL}/orders-left/")
    orders_info = response.json()

    rows = [
            {
                "warehouse_id": order["warehouse_id"],
                "no_of_orders":order["no_of_orders"]
            }
            for order in orders_info.get("orders", [])
        ]
    create_table_artifact(
            key=f"orders-left-in-warehouse",
            table=rows,
            description=f"Orders yet to be delivered"
        )
    
    return orders_info


@task
def agent_checkout():
    response = requests.post(f"{BASE_URL}/checkout/")
    return response.json()