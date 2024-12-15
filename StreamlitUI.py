import streamlit as st
import requests
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()

# Define the base URL for the Falcon API
BASE_URL = os.getenv("BASE_URL")

st.title("Delivery Assignment System")

# Tabs for different functionalities
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
    "Initial upload",
    "Worker Check-In",
    "Order Allocation",
    "Agents Info",
    "Agent Orders",
    "Orders Left",
    "Worker Check-Out",
    "Orders Upload",
    "Manual Agent checkin",
    "Upload Order manually"
])

with tab1:
    st.header("Initial data upload for agent and warehouse table use only once")

    # Button to trigger the upload initialization
    if st.button("upload warehouse and agent init data"):
        with st.spinner("uploading"):
            try:
                response = requests.post(f"{BASE_URL}/init_upload")
                if response.status_code == 200:
                    st.success(response.json().get("message", "Data upload initialized successfully!"))
                else:
                    st.error(f"Failed to initialize data upload: {response.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"Error connecting to the API: {e}")

# Worker Check-In
with tab2:
    st.header("Worker Check-In")
    if st.button("Randomly Mark Agents as Checked-In"):
        with st.spinner("Marking agents as checked-in..."):
            response = requests.post(f"{BASE_URL}/auto-checkin/")
            if response.status_code == 200:
                st.success(response.json().get("message", "Agents successfully checked-in!"))
            else:
                st.error(f"Failed to check in agents: {response.text}")

# Order Allocation
with tab3:
    st.header("Order Allocation")
    if st.button("Trigger Order Allocation"):
        with st.spinner("Allocating orders..."):
            response = requests.post(f"{BASE_URL}/allocate-all-orders")
            if response.status_code == 200:
                st.success(response.json().get("message", "Orders successfully allocated!"))
            else:
                st.error(f"Failed to trigger order allocation: {response.text}")

# Agents Info
with tab4:
    st.header("Agents Info")
    if st.button("Get Agents Info"):
        with st.spinner("Fetching agents info..."):
            response = requests.get(f"{BASE_URL}/agents-day-summary")
            if response.status_code == 200:
                agents_info = response.json().get("agents", [])
                df = pd.DataFrame(agents_info)
                
                st.write("### Agents Info:")
                st.dataframe(df)
                
                total_no_orders = response.json().get("total_no_of_orders", 0)
                cost_per_order = response.json().get("cost_per_order", 0)
                
                if total_no_orders > 0:
                    st.write(f"## Total number of orders this day: {total_no_orders}")
                    st.write(f"## Cost per order: {cost_per_order}")
                else:
                    st.write("## No orders allocated!")    
            else:
                st.error(f"Failed to fetch agents info: {response.text}")

# Agent Orders
with tab5:
    st.header("Agent Orders")
    agent_id = st.number_input("Enter Agent ID", min_value=1, step=1)
    if st.button("Get Orders for Agent"):
        with st.spinner("Fetching agent's orders..."):
            response = requests.get(f"{BASE_URL}/assigned-orders/{agent_id}")
            if response.status_code == 200:
                orders = response.json().get("orders", [])
                if orders:
                    orders_df = pd.DataFrame(orders)
                    st.write(f"### Orders for Agent {agent_id}:")
                    st.dataframe(orders_df)
                else:
                    st.info(f"No orders found for agent {agent_id}.")
            else:
                st.error(f"Failed to fetch orders for the agent: {response.text}")

# Orders Left
with tab6:
    st.header("Undelivered Orders")
    
    try:
        # Fetch data from the `/orders_left/` endpoint
        response = requests.get(f"{BASE_URL}/orders-left/")
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Process JSON data
        orders_info = response.json().get("orders", [])  # Assuming your API returns JSON
        
        if orders_info:
            # Convert the data into a DataFrame for display
            df = pd.DataFrame(orders_info)
            
            # Display the DataFrame as a table
            st.subheader("Undelivered Orders Table")
            st.dataframe(df)  # Interactive table
            
        else:
            st.info("No undelivered orders found.")

    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data: {e}")
    except ValueError as e:
        st.error(f"Error processing data: {e}")

# Worker Check-Out
with tab7:
    st.header("Worker Check-Out")
    if st.button("Mark All Agents as Checked-Out"):
        with st.spinner("Marking agents as checked-out..."):
            response = requests.post(f"{BASE_URL}/checkout/")
            if response.status_code == 200:
                st.success(response.json().get("message", "Agents successfully checked-out!"))
            else:
                st.error(f"Failed to check out agents: {response.text}")

# Orders Upload
with tab8:
    st.title("Random Upload Orders to Database")

    # Create a button to trigger the order upload
    if st.button("Upload Orders"):
        try:
            # Make a POST request to the /upload_orders endpoint
            response = requests.post(f"{BASE_URL}/upload-orders/")
            
            # Parse the response
            if response.status_code == 200:
                st.success(response.json().get("message", "Orders uploaded successfully!"))
            else:
                st.error(response.json().get("message", "Failed to upload orders."))
        except Exception as e:
            # Handle connection or unexpected errors
            st.error(f"An error occurred: {e}")

#Manual agent checkin
with tab9:
    st.header("Manual Agent Check-In")

    # Input fields for warehouse_id and percent
    warehouse_id = st.number_input("Enter Warehouse ID", min_value=0, max_value=10, step=1)
    percent = st.number_input("Enter Percent (%)", min_value=0, max_value=100, step=5)

    # Button to trigger the check-in
    if st.button("Mark Agents as Checked-In for Warehouse"):
        if warehouse_id and percent is not None:
            with st.spinner("Processing warehouse check-in..."):
                try:
                    response = requests.post(f"{BASE_URL}/checkin/{warehouse_id}/{percent}")
                    if response.status_code == 200:
                        st.success(response.json().get("message", "Agents successfully checked-in!"))
                    else:
                        st.error(f"Failed to check in agents: {response.text}")
                except requests.exceptions.RequestException as e:
                    st.error(f"Error connecting to the API: {e}")
        else:
            st.warning("Please provide both Warehouse ID and Percent.")

with tab10:
    st.header("Upload Single Order")

    # Input fields for order details
    x_coord = st.number_input("X Coord")
    y_coord = st.number_input("Y Coord")
    warehouse_id = st.text_input("Enter Warehouse ID")

    # Button to trigger the order upload
    if st.button("Upload Single Order"):
        if x_coord and y_coord and warehouse_id :
            try:
                # Parse order details as JSON
                order_data = {
                    "warehouse_id": warehouse_id,
                    "x_coord": x_coord,
                    "y_coord": y_coord
                }
                with st.spinner("Uploading single order..."):
                    response = requests.post(f"{BASE_URL}/upload-single-order/", json=order_data)
                    if response.status_code == 200:
                        st.success(response.json().get("message", "Order uploaded successfully!"))
                    else:
                        st.error(f"Failed to upload order: {response.text}")
            except ValueError as e:
                st.error(f"Invalid JSON format in Order Details: {e}")
            except requests.exceptions.RequestException as e:
                st.error(f"Error connecting to the API: {e}")
        else:
            st.warning("Please provide all required fields: Order ID, Warehouse ID, and Order Details.")


