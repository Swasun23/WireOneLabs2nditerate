# Project Setup and Usage Guide

## Prerequisites
Ensure that you have `postgres` installed and running on your system.

## Setting Up the Environment

### For Linux

1. **Create a Python Virtual Environment**:
   ```bash
   python3 -m venv Myenv
   ```

2. **Activate the Virtual Environment**:
   ```bash
   source Myenv/bin/activate
   ```

3. **Install the Requirements**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Create a .env file in the project folder with the following variables**
```env
BASE_URL = "http://localhost:8000"

DATABASE_URL = "postgresql://<username>:<password>@localhost:<port>/<database_name>"
```
## Running the Application with the webui

### 1. **Run the Server**:
   ```bash
   python3 main.py
   ```

### 2. **Run the Streamlit UI**:
   Launch the Streamlit user interface by running:
   ```bash
   streamlit run StreamlitUI.py
   ```
   Access the link you get in the terminal to access the page

### 3. **Upload initial warehouse and agent info**:
On the initial upload tab, click run the initial upload  
**Please use this tab only for the first setup to upload the db with warehouse and agents**

### 4. **Use the other tabs to play with the other options**

## Setting up the automated setup
- I have used the **prefect** library in python to automate the flow

- Execute all the commands from inside the project folder

### 1. **Run the Server**: 
   ```bash
   python3 main.py
   ```
### 2. **Run the prefect server**: (run in parallel terminal)
   ```bash 
   prefect server start
   ```
### 3. **set environment variable**
   ```bash
   prefect config set PREFECT_API_URL=http://127.0.0.1:4200/api
   ```    
   specify the port you are using, by default it is 4200
### 3. **Start a prefect workpool**:(run in parallel terminal)
   ```bash
   prefect worker start -p my-work-pool
   ```
### 4. **Initialise deployment**: (run in parallel terminal)
   ```bash
   cd prefect
   python3 flows.py
   ```
   open the link you get, you will be taken the prefect ui, which lists the info about the deployments, you can click run->quick run to initiate a manual trigger or it will be triggered everyday 9:00 AM


