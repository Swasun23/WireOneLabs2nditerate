import numpy as np
from sqlalchemy.orm import Session
from database.models import OrdersBigPic,Warehouse
import gc

class OrderAllocator:
    def __init__(self, session, warehouse):
        """
        Initialize the OrderAllocator with the database session and warehouse object.

        Parameters:
        session (Session): SQLAlchemy session.
        warehouse (Warehouse): Warehouse object.
        """
        self.session = session
        self.warehouse = warehouse
        self.warehouse_coords = (warehouse.x_coord, warehouse.y_coord)

    def allocate_orders(self):
        """
        Allocate orders to agents iteratively using sector-based clustering for the first iteration
        and constrained k-means clustering for subsequent iterations.

        Parameters:
        session (Session): SQLAlchemy session.
        warehouse (Warehouse): Warehouse object.

        Returns:
        None
        """
        warehouse_coords = self.warehouse_coords
        i = 0
        while True:
            # Get undelivered orders
            orders = [
                (order.id, order.x_coord, order.y_coord)
                for order in self.warehouse.orders
                if not order.is_delivered
            ]
            print(f"No of undelivered orders {len(orders)}")
            n_undelivered_orders_before_allocation = len(orders)
            if len(orders) == 0:
                print("No undelivered orders remaining!")
                break

            orders = np.array(orders)
            order_ids = orders[:, 0].astype(int)
            order_coords = orders[:, 1:3].astype(float)

            available_agents = [agent for agent in self.warehouse.agents if agent.no_of_orders < 60 and agent.total_distance < 95 and agent.is_checked_in] # max distance limit might be 100 but since the area within warehouse limits is 80km2 we have to adjust the theshold to take the available agents
            n_available_agents = len(available_agents)
            print(f"Agents available {n_available_agents}")
            if n_available_agents == 0:
                print("No available agents remaining!")
                break

            if len(orders) < n_available_agents:
                print("Number of orders is less than the number of available agents so switching to round robin!")
                available_agents = [agent for agent in self.warehouse.agents if agent.no_of_orders < 60 and agent.total_distance < 100]
                allocated_count = self.round_robin_allocation(orders.tolist(), available_agents)
                print(f"Orders allocated with round robin {allocated_count}")
                break

            if i == 0:
                i+=1
                # Perform sector-based clustering for the first iteration
                print("Performing sector-based clustering for the first iteration.")
                sector_assignments = self.assign_points_to_sectors(order_coords, n_available_agents)
                sector_based_clusters = [[] for _ in range(n_available_agents)]
                for idx, sector in enumerate(sector_assignments):
                    sector_based_clusters[sector].append(idx)

                allocated_count = 0  # Track the number of orders allocated in this iteration

                for cluster_id, agent in enumerate(available_agents):
                    self.session.refresh(agent)

                    cluster_indices = sector_based_clusters[cluster_id]
                    cluster_orders = order_coords[cluster_indices]
                    cluster_order_ids = order_ids[cluster_indices]

                    if agent.orders is None:
                        agent.orders = []

                    if len(cluster_orders) > 1:
        
                        distance_matrix = self.compute_distance_matrix(cluster_orders)
                        self.greedy_tsp_with_agent(distance_matrix, agent, cluster_orders, cluster_order_ids)
                        allocated_count += self.session.query(OrdersBigPic).filter(
                            OrdersBigPic.id.in_(cluster_order_ids.tolist()),  # Convert to list of ints
                            OrdersBigPic.is_delivered == True
                        ).count()
                        
                        del distance_matrix
                        gc.collect()

                    elif len(cluster_orders) == 1:
                        single_order_id = int(cluster_order_ids[0])
                        single_order_coords = tuple(cluster_orders[0])
                        current_orders = list(agent.orders) if agent.orders else []

                        if(len(current_orders)):
                            last_delivered_order = current_orders[-1]
                            last_order_coords = self.session.query(OrdersBigPic.x_coord,OrdersBigPic.y_coord).filter(OrdersBigPic.id == last_delivered_order).first()
                        else:
                            last_order_coords = self.warehouse_coords

                        distance_to_add = np.linalg.norm(np.array(last_order_coords) - np.array(single_order_coords))

                        if agent.no_of_orders < 60 and agent.total_distance + distance_to_add < 100:
                            current_orders.append(single_order_id)
                            agent.no_of_orders += 1
                            agent.total_distance += distance_to_add
                            agent.total_distance = float(agent.total_distance)
                            agent.orders = current_orders

                            order = self.session.query(OrdersBigPic).filter(OrdersBigPic.id == single_order_id).first()
                            order.is_delivered = True
                            order.assigned_agent_id = agent.id
                            allocated_count += 1

            else:
                # Perform constrained k-means clustering
                clusters, centroids = self.constrained_kmeans(order_coords, n_available_agents)

                # Assign clusters to agents based on the nearest centroid to their last known location
                agent_to_centroid_mapping = []
                for agent in available_agents:
                    self.session.refresh(agent)
                    if agent.orders:
                        last_order_id = int(agent.orders[-1])
                        last_order = self.session.query(OrdersBigPic).filter(OrdersBigPic.id == last_order_id).first()
                        agent_coords = [last_order.x_coord, last_order.y_coord]
                    else:
                        agent_coords = warehouse_coords

                    distances_to_centroids = np.linalg.norm(centroids - np.array(agent_coords), axis=1)
                    closest_centroid = np.argmin(distances_to_centroids)
                    agent_to_centroid_mapping.append((agent, closest_centroid))

                # Ensure each centroid is assigned to one agent
                assigned_centroids = set()
                agent_to_cluster = {}
                for agent, centroid_idx in sorted(agent_to_centroid_mapping, key=lambda x: x[1]):
                    if centroid_idx not in assigned_centroids:
                        agent_to_cluster[agent] = centroid_idx
                        assigned_centroids.add(centroid_idx)

                # Allocate orders within clusters to assigned agents
                allocated_count = 0
                for agent, cluster_idx in agent_to_cluster.items():
                    self.session.refresh(agent)

                    cluster_indices = np.where(clusters == cluster_idx)[0]
                    cluster_orders = order_coords[cluster_indices]
                    cluster_order_ids = order_ids[cluster_indices]

                    if len(cluster_orders) > 1:
                        distance_matrix = self.compute_distance_matrix(cluster_orders)
                        self.greedy_tsp_with_agent(distance_matrix, agent, cluster_orders, cluster_order_ids)
                        allocated_count += self.session.query(OrdersBigPic).filter(
                            OrdersBigPic.id.in_(cluster_order_ids.tolist()),
                            OrdersBigPic.is_delivered == True
                        ).count()
                        del distance_matrix
                        gc.collect()
                    elif len(cluster_orders) == 1:
                        single_order_id = int(cluster_order_ids[0])
                        single_order_coords = tuple(cluster_orders[0])
                        current_orders = list(agent.orders) if agent.orders else []

                        if len(current_orders):
                            last_delivered_order = current_orders[-1]
                            last_order_coords = self.session.query(OrdersBigPic.x_coord, OrdersBigPic.y_coord).filter(OrdersBigPic.id == last_delivered_order).first()
                        else:
                            last_order_coords = warehouse_coords

                        distance_to_add = np.linalg.norm(np.array(last_order_coords) - np.array(single_order_coords))

                        if agent.no_of_orders < 60 and agent.total_distance + distance_to_add < 100:
                            current_orders.append(single_order_id)
                            agent.no_of_orders += 1
                            agent.total_distance += distance_to_add
                            agent.total_distance = float(agent.total_distance)
                            agent.orders = current_orders

                            order = self.session.query(OrdersBigPic).filter(OrdersBigPic.id == single_order_id).first()
                            order.is_delivered = True
                            order.assigned_agent_id = agent.id
                            allocated_count += 1
            
            self.session.commit()

            undelivered_orders_after_allocation = [
                (order.id, order.x_coord, order.y_coord)
                for order in self.warehouse.orders
                if not order.is_delivered
            ]
            n_undelivered_orders_after_allocation = len(undelivered_orders_after_allocation) 
            if n_undelivered_orders_before_allocation == n_undelivered_orders_after_allocation:
                print("No orders were allocated in this iteration. Exiting loop.")
                break

            
            print("Iteration complete. Re-clustering remaining orders.")

        print("Order allocation fully complete.")
        return


    def round_robin_allocation(self, undelivered_orders, agents, max_orders_per_agent=60, max_distance_per_agent=100):
        """
        Allocate orders to agents using a round-robin approach.

        Parameters:
        session (Session): SQLAlchemy session.
        undelivered_orders (list): List of undelivered orders as tuples (id, x_coord, y_coord).
        agents (list): List of available agents.
        max_orders_per_agent (int): Maximum number of orders an agent can take.
        max_distance_per_agent (float): Maximum total distance an agent can travel.

        Returns:
        int: Number of orders allocated.
        """
        allocated_count = 0
        exhausted_agents = set()

        def active_agent_cycle(agents, exhausted_agents):
            while True:
                for agent in agents:
                    if agent not in exhausted_agents:
                        yield agent

        agent_cycle = active_agent_cycle(agents, exhausted_agents)

        for order_data in undelivered_orders:
            order_id, order_x, order_y = order_data
            assigned = False
            failed_agents = 0

            while not assigned:
                if len(exhausted_agents) == len(agents):
                    self.session.commit()
                    return allocated_count

                agent = next(agent_cycle)
                self.session.refresh(agent)

                if agent.no_of_orders > 0:
                    last_order_id = agent.orders[-1]
                    last_order_coords = self.session.query(OrdersBigPic.x_coord, OrdersBigPic.y_coord).filter(OrdersBigPic.id == last_order_id).first()
                    if not last_order_coords:
                        continue
                    distance_to_add = np.linalg.norm(np.array([order_x, order_y]) - np.array(last_order_coords))
                else:
                    warehouse_coords = self.warehouse_coords
                    if not warehouse_coords:
                        continue
                    distance_to_add = np.linalg.norm(np.array([order_x, order_y]) - np.array(warehouse_coords))

                if agent.total_distance + distance_to_add > max_distance_per_agent:
                    failed_agents += 1
                    if failed_agents == len(agents) - len(exhausted_agents):
                        break
                    continue

                order = self.session.query(OrdersBigPic).filter(OrdersBigPic.id == order_id).first()
                order.is_delivered = True
                order.assigned_agent_id = agent.id
                
                current_orders = list(agent.orders) if agent.orders else []
                agent.no_of_orders += 1
                agent.total_distance += distance_to_add
                agent.total_distance = float(agent.total_distance)
                current_orders.append(order_id)
                agent.orders = current_orders

                self.session.commit()

                if agent.no_of_orders >= max_orders_per_agent or agent.total_distance >= max_distance_per_agent:
                    exhausted_agents.add(agent)

                allocated_count += 1
                assigned = True

        self.session.commit()  # Commit remaining changes
        return allocated_count


    def greedy_tsp_with_agent(self,distance_matrix, agent, cluster_orders, cluster_order_ids, max_distance=100, max_orders=60):
        """
        Solve a simplified TSP using a greedy algorithm.

        Parameters:
        distance_matrix (np.ndarray): Distance matrix.
        agent (AgentsBigPic): Agent object.
        cluster_orders (np.ndarray): Order coordinates.
        cluster_order_ids (np.ndarray): Order IDs.
        session (Session): SQLAlchemy session.
        max_distance (float): Maximum allowable distance.
        max_orders (int): Maximum number of orders.

        Returns:
        None
        """
        n_points = distance_matrix.shape[0]
        current_orders = list(agent.orders) if agent.orders else []

        # Determine agent's last location
        if agent.orders:
            last_order_id = agent.orders[-1]
            last_location = self.session.query(OrdersBigPic.x_coord, OrdersBigPic.y_coord).filter(
                OrdersBigPic.id == last_order_id
            ).first()
        else:
            last_location = self.warehouse_coords

        # Find starting point
        start_point = OrderAllocator.find_closest_point(last_location, cluster_orders)
        distance_to_add = distance_matrix[start_point].min()
        if agent.total_distance + distance_to_add > max_distance:
            return  # Exit early if initial point breaches threshold

        # Initialize visited array and route
        visited = np.zeros(n_points, dtype=bool)
        route = [start_point]
        visited[start_point] = True

        # Update agent and order for the starting point
        order_id = int(cluster_order_ids[start_point])
        current_orders.append(order_id)
        agent.no_of_orders += 1
        agent.total_distance += distance_to_add
        agent.total_distance = float(agent.total_distance)
        order = self.session.query(OrdersBigPic).filter(OrdersBigPic.id == order_id).first()
        order.is_delivered = True
        order.assigned_agent_id = agent.id
        current_point = start_point

        # Iterate over remaining points
        for _ in range(n_points - 1):
            if agent.no_of_orders >= max_orders:
                break

            # Find the closest unvisited point
            distances = distance_matrix[current_point]
            mask = np.where(visited, np.inf, 0)
            closest_point = np.argmin(distances + mask)
            distance_to_add = distances[closest_point]

            if agent.total_distance + distance_to_add > max_distance:
                break  # Stop if adding the point breaches the distance limit

            # Update agent and order for the selected point
            route.append(closest_point)
            visited[closest_point] = True
            order_id = int(cluster_order_ids[closest_point])
            current_orders.append(order_id)
            agent.no_of_orders += 1
            agent.total_distance += distance_to_add
            agent.total_distance = float(agent.total_distance)
            order = self.session.query(OrdersBigPic).filter(OrdersBigPic.id == order_id).first()
            order.is_delivered = True
            order.assigned_agent_id = agent.id
            current_point = closest_point

        agent.orders = current_orders
        self.session.commit()
        del distance_matrix
        gc.collect()

    @staticmethod
    def find_closest_point(last_location, cluster_orders):
        """
        Find the index of the point in cluster_orders closest to the given last location.

        Parameters:
        last_location (tuple): Last known location (x, y).
        cluster_orders (list): List of order coordinates (x, y).

        Returns:
        int: Index of the closest point.
        """
        points = np.array(cluster_orders)
        distances = np.linalg.norm(points - np.array(last_location), axis=1)
        return np.argmin(distances)

    @staticmethod
    def compute_distance_matrix(points):
        """
        Compute the pairwise Euclidean distance matrix for a set of points.

        Parameters:
        points (np.ndarray): Array of points.

        Returns:
        np.ndarray: Pairwise distance matrix.
        """
        sq_diff = np.sum(points**2, axis=1)[:, np.newaxis] + np.sum(points**2, axis=1) - 2 * np.dot(points, points.T)
        return np.sqrt(np.maximum(sq_diff, 0))
    
    @staticmethod
    def constrained_kmeans(X, n_clusters, centroids=None, max_iters=10, tol=1e-4):
        """
        Perform k-means clustering with constraints on the number of points per cluster.

        Parameters:
        X (np.ndarray): Input data points.
        n_clusters (int): Number of clusters.
        centroids (np.ndarray, optional): Initial centroids.
        max_iters (int): Maximum number of iterations.
        tol (float): Convergence tolerance.

        Returns:
        np.ndarray: Cluster labels for each point.
        """
        np.random.seed(42)
        n_samples = X.shape[0]
        points_per_cluster = n_samples // n_clusters
        extra_points = n_samples % n_clusters

        if centroids is None:
            centroids = OrderAllocator.kmeans_plus_plus_initialization(X, n_clusters)

        for _ in range(max_iters):
            distances = np.linalg.norm(X[:, np.newaxis] - centroids, axis=2)
            sorted_indices = np.argsort(distances, axis=1)

            cluster_counts = np.zeros(n_clusters, dtype=int)
            labels = -1 * np.ones(n_samples, dtype=int)

            for i in range(n_samples):
                for cluster_idx in sorted_indices[i]:
                    if cluster_counts[cluster_idx] < points_per_cluster:
                        labels[i] = cluster_idx
                        cluster_counts[cluster_idx] += 1
                        break

            if extra_points > 0:
                unassigned_points = np.where(labels == -1)[0]
                for point_idx in unassigned_points:
                    closest_cluster = np.argmin(distances[point_idx])
                    labels[point_idx] = closest_cluster
                    cluster_counts[closest_cluster] += 1

            new_centroids = np.array([
                X[labels == i].mean(axis=0) if np.any(labels == i) else centroids[i]
                for i in range(n_clusters)
            ])

            if np.linalg.norm(centroids - new_centroids) < tol:
                break

            centroids = new_centroids

        return labels,centroids

    def assign_points_to_sectors(self,X, n_sectors):
        """
        Assign points to angular sectors around a warehouse.

        Parameters:
        X (np.ndarray): Array of shape (n_samples, 2) with points' x and y coordinates.
        n_sectors (int): Number of sectors to divide the area into.
        warehouse_coords (tuple): Coordinates of the warehouse (wh_x, wh_y).

        Returns:
        np.ndarray: Array of sector assignments for each point.
        """
        wh_x, wh_y = self.warehouse_coords

        # Calculate angles of each point relative to the warehouse
        angles = np.degrees(np.arctan2(X[:, 1] - wh_y, X[:, 0] - wh_x)) % 360

        # Determine sector for each point based on angle
        sector_size = 360 / n_sectors
        sectors = np.floor(angles / sector_size).astype(int)

        return sectors
    
    @staticmethod
    def kmeans_plus_plus_initialization(X, n_clusters):
        centroids = [X[np.random.choice(range(X.shape[0]))]]
        for _ in range(1, n_clusters):
            distances = np.min([np.linalg.norm(X - c, axis=1)**2 for c in centroids], axis=0)
            probabilities = distances / distances.sum()
            new_centroid = X[np.random.choice(range(X.shape[0]), p=probabilities)]
            centroids.append(new_centroid)
        return np.array(centroids)
