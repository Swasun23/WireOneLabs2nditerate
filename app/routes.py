import falcon
from .resources.Agent import AutoAgentCheckIn,AgentCheckOut,WarehouseAgentCheckIn,AgentsDaySummary
from .resources.order_allocation import AllocateAllOrdersResource,AllocateOrdersResource
from .resources.HealthCheck import HealthCheckResource
from .resources.Orders import UploadRandomOrders,OrdersLeft,UploadWarehouseOrders,AgentOrders
from .resources.initial_upload import LoadDataResource
from database.db import get_db

# Create Falcon app
app = falcon.App()

# Add routes
app.add_route("/auto-checkin/",AutoAgentCheckIn(get_db))
app.add_route("/checkin/{warehouse_id}/{percent}",WarehouseAgentCheckIn(get_db))
app.add_route("/upload-orders/",UploadRandomOrders(get_db))
app.add_route("/upload-single-order/",UploadWarehouseOrders(get_db))
app.add_route("/allocate-orders/{warehouse_id}", AllocateOrdersResource(get_db))
app.add_route("/allocate-all-orders", AllocateAllOrdersResource(get_db))
app.add_route("/agents-day-summary",AgentsDaySummary(get_db))
app.add_route("/assigned-orders/{agent_id}",AgentOrders(get_db))
app.add_route("/orders-left/",OrdersLeft(get_db))
app.add_route("/checkout/",AgentCheckOut(get_db))
app.add_route("/upload-orders/",UploadRandomOrders(get_db))
app.add_route("/health", HealthCheckResource())
app.add_route("/init_upload",LoadDataResource())