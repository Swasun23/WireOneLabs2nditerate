from database.models import Warehouse,OrdersBigPic
from random import randint,uniform

def generate_random_orders(session):
    try:
        warehouse_info = session.query(Warehouse).all()
        for warehouse in warehouse_info:
            no_of_orders = randint(600,1200)
            for i in range(no_of_orders):
                wh_id = warehouse.id
                wh_x = warehouse.x_coord
                wh_y = warehouse.y_coord
                x = round(uniform(wh_x-20,wh_x+20),2)
                y = round(uniform(wh_y-20,wh_y+20),2)
                order_dict = {"warehouse_id":wh_id,"x_coord":x,"y_coord":y}
                order_ob = OrdersBigPic(**order_dict)
                session.add(order_ob)
            session.commit()
        return 1
    except Exception as e:
        session.rollback()  
        print(f"Error generating orders: {e}")  
        return 0  

def upload_warehouse_orders(session,order_dict):
    try:
        orders_ob = OrdersBigPic(**order_dict)
        session.add(orders_ob)
        session.commit()
        return 1
    except Exception as e:
        session.rollback()  
        print(f"Error generating orders: {e}")  
        return 0  