from database.models import AgentsBigPic,OrdersBigPic
from sqlalchemy import delete
import random
from sqlalchemy.orm import Session

def mark_agent_check_in(session: Session):
    agents = session.query(AgentsBigPic).all()

    if not agents:
        return None

    
    attnd_percentage = random.randint(60,90)
    no_of_present_agents = int((attnd_percentage/100) * len(agents))

    selected_agents = random.sample(agents, no_of_present_agents)

    for agent in selected_agents:
        agent.is_checked_in = True 
    
    session.commit()

    return len(selected_agents)

def mark_Warehouse_agent_check_in(session: Session,warehouse_id,percent):
    agents = session.query(AgentsBigPic).filter(AgentsBigPic.warehouse_id == warehouse_id).all()

    if not agents:
        return None

    
    percent = int(percent)
    no_of_present_agents = int((percent/100) * len(agents))

    selected_agents = random.sample(agents, no_of_present_agents)

    for agent in selected_agents:
        agent.is_checked_in = True 
    
    session.commit()

    return len(selected_agents)

def mark_all_checked_out(session: Session):
    session.query(AgentsBigPic).update({AgentsBigPic.is_checked_in: False})
    session.commit()

    #pop all orders that were delivered
    session.execute(
        delete(OrdersBigPic).where(OrdersBigPic.is_delivered == True)
    )
    session.commit()

    session.query(AgentsBigPic).update({AgentsBigPic.orders: [],AgentsBigPic.no_of_orders:0,AgentsBigPic.total_distance:0})

    session.commit()

    return 1

def calculate_earnings(session,agent_id):
    agent = session.query(AgentsBigPic).filter(AgentsBigPic.id == agent_id).first()
    total_earnings = 0
    if agent.is_checked_in:
        total_earnings = 500
        if agent.no_of_orders > 50:
            total_earnings = 42 * agent.no_of_orders
        elif agent.no_of_orders > 25:
            total_earnings = 35 * agent.no_of_orders

    return total_earnings
