from prefect import flow
from tasks import upload_orders, agent_checkin, order_allocation, agent_checkout,show_agent_day_info,show_orders_by_agent,orders_left

@flow
def daily_process_flow():
    try:
        orders = upload_orders()
        print("Orders Uploaded!", orders)

        checking_resp = agent_checkin()
        print("Agent Checked-in!", checking_resp)

        order_resp = order_allocation()
        print("Order Allocation done!", order_resp)

        show_agent_day_info()

        for agent_id in range(1,201,1):
            status = show_orders_by_agent(agent_id)
            if status!=1:
                print(f"No artifact created for agent-{agent_id}")

        orders_left()

    except Exception as e:
        print("An error occurred:", e)
    finally:
        agent_resp = agent_checkout()
        print("Agents Checked-out!", agent_resp)
    

if __name__ == "__main__":
    daily_process_flow.serve(name="Daily order allocation", cron="30 3 * * *") #in UTC runs at everyday 9 AM ist

