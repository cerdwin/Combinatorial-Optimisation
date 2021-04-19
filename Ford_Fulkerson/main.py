#!/usr/bin/env python3
import sys

def build_graph(customers, demand, balances, first_run):
    # Graph: at key has coordinates (column, row), value is a dictionary of ((column, key) : [ lb, current, ub]}
    graph = {}
    ##### 1st column
    tmp = {}
    for i in range(len(customers)):
        if first_run:
            tmp[(2, i + 1)] = (0, 0, customers[i][1]-customers[i][0])
        else:
            tmp[(2, i + 1)] = (customers[i][0], 0, customers[i][1])
    graph[(1, 1)] = tmp
    for i in range(len(customers)):  #### 2nd column
        tmp = {}
        for z in range(len(customers[i])):
            if z < 2:  # upper and lower bounds
                continue
            tmp[(3, customers[i][z])] = (0, 0, 1)  # lower bound, current, upper bound
        graph[(2, i + 1)] = tmp  
    for i in range(len(demand)):  #### 3rd column
        tmp = {}
        if first_run:
            tmp[(4, 1)] = (0, 0, sys.maxsize)  # lower bound is the demand
        else:
            tmp[(4, 1)] = (demand[i], 0, sys.maxsize)
        graph[(3, i + 1)] = tmp

    if first_run:
        #### 4th column
        tmp = {}
        tmp[(1, 1)] = (0, 0, sys.maxsize)  ## into the start column, this is the circular edge
        graph[(4, 1)] = tmp
        ####### Adding s' and t' - > S is connected with nodes with positive balances and t' with the negative ones
        ## s'
        graph[(0,1)] = {}
        ## t'
        graph[(5, 1)] = {}

        for key, value in balances.items():
            if value < 0: ## will be connected to t'
                graph[key][(5, 1)] = (0, 0, abs(value))
            elif value > 0:
                graph[(0, 1)][key] = (0, 0, value)

        #    if value
    else:
        graph[(4,1)] = {}
    return graph

def count_balance(customers, demand):
    balances = {}
    #### start
    tmp = 0
    for i in customers:
        tmp += i[0]
    balances[(1, 1)] = -tmp
    #### customers
    for i in range(len(customers)):
        balances[(2, i + 1)] = customers[i][0]
    #### products
    for i in range(len(demand)):
        balances[(3, i + 1)] = -demand[i]
    #### terminal node
    balances[(4, 1)] = sum(demand)
    return balances

def to_reverse_graph(graph):
    new_graph = {}

    for key, value in graph.items():
        for k, v in value.items():
            if k not in new_graph.keys():
                new_graph[k] = {}
                new_graph[k][key] = graph[key][k]
            else:
                new_graph[k][key] = graph[key][k]
    return new_graph


def dict_to_path(end, parents):
    path = []
    current_child = end
    path.append(current_child)
    current_parent = parents[end]
    while current_parent != -2:
        current_child = current_parent
        path.append(current_child)
        current_parent = parents[current_child]
    return path[::-1]

def new_path_found(graph, start, end, path, flow):
    path = []
    path.append(start)
    queue = []
    queue.append(start)
    parents = {}
    parents[start] = -2
    toky = {}
    toky[start] = sys.maxsize
    reverse_graph = to_reverse_graph(graph)
    while queue:
        u = queue.pop(0)
        for k, v in graph[u].items():
            if k not in parents.keys() and graph[u][k][2] - graph[u][k][1] > 0: # if it is fresh and has room for flow
                parents[k] = u
                toky[k] = min(toky[u], graph[u][k][2] - graph[u][k][1])
                if k != end:
                    queue.append(k)
                else:
                    return dict_to_path(end, parents), toky[k]
        if u in reverse_graph.keys():
            for k, v in reverse_graph[u].items():
                if k not in parents.keys() and reverse_graph[u][k][1] - reverse_graph[u][k][0] > 0:
                    parents[k] = u
                    toky[k] = min(toky[u], reverse_graph[u][k][1] - reverse_graph[u][k][0])
                    queue.append(k)
    return None, None


def ford_fulkerson(graph, start, end):
    flow = 0
    total_flow = 0
    while True:
        my_path, my_flow = new_path_found(graph, start, end, [], sys.maxsize)
        if my_path is None:
            break

        total_flow+=my_flow
        for i in range(len(my_path)-1):
            current_start = my_path[i]
            current_end = my_path[i+1]
            if current_end in graph[current_start].keys():
                graph[current_start][current_end] = (
                    graph[current_start][current_end][0], graph[current_start][current_end][1]+ my_flow,
                    graph[current_start][current_end][2])
            elif current_start in graph[current_end].keys():
                tmp = current_end
                current_end = current_start
                current_start = tmp
                graph[current_start][current_end] = (
                graph[current_start][current_end][0], graph[current_start][current_end][1] - my_flow,
                graph[current_start][current_end][2])
    for key, value in graph.items():
        for k, v in value.items():
            flow += v[1]
    return graph

def is_saturated(graph):
    for key, value in graph[0,1].items():
        if value[1] != value[2]:
            return False
    return True

if __name__ == "__main__":
    # Reading
    origin = sys.argv[1]
    destination = sys.argv[2]
    d = []
    customers = []
    with open(origin) as fp:
        for number in fp.readline().split():
            d.append(int(number))
        for i in range(d[0]):
            customer = []
            for number in fp.readline().split():
                customer.append(int(number))
            customers.append(customer)
        demand = []
        for number in fp.readline().split():
            demand.append(int(number))

    ######################   BALANCES   ##############################
    balances = count_balance(customers, demand)
    ######################     GRAPH    ##############################
    graph = build_graph(customers, demand, balances, True)
    final_graph = build_graph(customers, demand, balances, False)
    ######################   REVERSE GRAPH   ##############################


    ######################   fulkerson   ##############################
    initial_graph = ford_fulkerson(graph, (0, 1), (5, 1))
    # Check if edges from s' are saturated
    if is_saturated(initial_graph):
    ## copy flows into the final graph
        for key,value in final_graph.items():
            for k, v in value.items():
                final_graph[key][k] = (v[0], initial_graph[key][k][1]+v[0],v[2]) # zvysim initial flow o lower bounds

    ######################  final ###################
        resulting_graph = ford_fulkerson(final_graph, (1, 1), (4, 1))
        result = []
        for i in range(1, len(customers)+1):
            res = []
            for key, value in resulting_graph[(2, i)].items():
                if value[1] ==1:
                    res.append(key[1])
            res.sort()
            result.append(res)
        with open(destination, mode='w') as f:
            for i in range(len(result)):
                for x in range(len(result[i])):
                    f.write(str(int(result[i][x])))
                    if x < len(result[i]) - 1:
                        f.write(' ')
                if i < len(result)-1:
                    f.write('\n')

    else:
        # printuji na sys out -1
        with open(destination, mode='w') as f:
            f.write(str(-1))


