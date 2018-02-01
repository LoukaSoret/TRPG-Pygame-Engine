import collections,heapq,pygame,math

class SquareGrid():
    def __init__(self, width, height,nodeSize):
        self.width = width
        self.height = height
        self.nodeSize = nodeSize
        self.weights = {}
        self.walls = []
        self.goal = (-1,-1)
    
    def in_bounds(self, id):
        (x, y) = id
        return 0 <= x < self.width and 0 <= y < self.height
    
    def passable(self, id):
    	for wall in self.walls:
    		if (wall.collidepoint(id[0]*64+32,id[1]*64+32)):
    			return False
    	return True
    
    def check_diagonal(self,from_id,id):
        (x,y) = from_id
        if id == (x-1,y-1):
            return self.passable((x,y-1)) and self.passable((x-1,y))
        if id == (x+1,y+1):
            return self.passable((x,y+1)) and self.passable((x+1,y))
        if id == (x+1,y-1):
            return self.passable((x,y-1)) and self.passable((x+1,y))
        if id == (x-1,y+1):
            return self.passable((x,y+1)) and self.passable((x-1,y))
        else:
            return True

    def neighbors(self, id):
        (x, y) = id
        results = [(x+1, y), (x, y-1), (x-1, y), (x, y+1), (x-1,y-1), (x+1,y+1), (x-1,y+1), (x+1,y-1)]
        if (x + y) % 2 == 0: results.reverse() # aesthetics
        results = filter(self.in_bounds, results)
        results = filter(self.passable, results)
        results = [item for item in results if self.check_diagonal(id,item)]
        return results

    def cost(self, from_node, to_node):
        if to_node==(from_node[0]+1,from_node[1]+1) or to_node==(from_node[0]-1,from_node[1]-1) or to_node==(from_node[0]+1,from_node[1]-1) or to_node==(from_node[0]-1,from_node[1]+1):
            return self.weights.get(to_node, math.sqrt(2))
        return self.weights.get(to_node, 1)

class PriorityQueue():
    def __init__(self):
        self.elements = []
    
    def empty(self):
        return len(self.elements) == 0
    
    def put(self, item, priority):
        heapq.heappush(self.elements, (priority, item))
    
    def get(self):
        return heapq.heappop(self.elements)[1]

def reconstruct_path(came_from, start, goal, graph):
    current = goal
    path = [current]
    #current = came_from[goal]
    #path = []
    while current != start:
        current = came_from[current]
        path.append(current)
    path.append(start) # optional
    path.reverse() # optional
    return path

def heuristic(a, b):
    (x1, y1) = a
    (x2, y2) = b
    return abs(x1 - x2) + abs(y1 - y2)

def a_star_search(graph, start, goal):
    graph.goal = goal
    frontier = PriorityQueue()
    frontier.put(start, 0)
    came_from = {}
    cost_so_far = {}
    came_from[start] = None
    cost_so_far[start] = 0
    

    while not frontier.empty():
        current = frontier.get()
        
        if current == goal:
            break
        
        for next in graph.neighbors(current):
            new_cost = cost_so_far[current] + graph.cost(current, next)
            if next not in cost_so_far or new_cost < cost_so_far[next]:
                cost_so_far[next] = new_cost
                priority = new_cost + heuristic(goal, next)
                frontier.put(next, priority)
                came_from[next] = current
    return reconstruct_path(came_from,start,goal, graph)

# return the costs from the start to every nodes in range
def costs_from_point(graph, start, range):
    costs = {}
    frontier = PriorityQueue()
    frontier.put(start, 0)
    costs[start] = 0

    while not frontier.empty():
        current = frontier.get()
        current_cost = costs[current]

        for next in graph.neighbors(current):
            next_cost = current_cost + graph.cost(current,next)
            if (next_cost <= range) and ( next not in costs or next_cost < costs[next]):
                costs[next] = next_cost
                frontier.put(next, 0)

    return list(costs.keys())