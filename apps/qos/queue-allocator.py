#! /usr/bin/python
#  coding: utf-8

import sys
import Queue

nodes = []
server_nodes = []
switch_nodes = []
server = {}
switches = {}
adjacent = []
max_bandwidth = 3000000



#dummy data for test
poll_map = [
[3000000, 3000000, 3000000, 3000000, 3000000], 
[3000000, 3000000, 3000000, 3000000, 3000000], 
[3000000, 3000000, 3000000, 3000000, 3000000], 
[3000000, 3000000, 3000000, 3000000, 3000000], 
[3000000, 3000000, 3000000, 3000000]]

def get_bandwidth_on_link(switch,outport):
    sw = poll_map[switch]
    bandwidth = sw[outport]
    return bandwidth

def allocate_queue():
    #assume all the bandwidth available in every link is 3000000 for now
    index = 0
    #loop through all switches
    for focus_switch in adjacent:
        #loop through all output port of a switch to set queues
        port_num = 0        
        for outport in focus_switch:
            #if output port is another switch, begin to check available bandwidth for each server from this output port
            if outport != -1 and outport < len(switch_nodes):

                node_avai_bandw = [-1 for i in range(len(nodes))]
                node_visited = [False for i in range(len(nodes))]

                ban_node = index
                 
                #start using modified Dijkstra for bottle neck and 
                #mark that don't come back to the switch whose outport itself which has the ref number as index
                #this queue is suppose to contains only switch
                process_queue = Queue.PriorityQueue()

                #add a start node
                #need to get from actual bandwidth map, node -> outport
                bandwidth = get_bandwidth_on_link(index,port_num)
                node_avai_bandw[outport] = bandwidth

                #use max_bandwidth - bandwidth to be able to sort with priority queue
                process_queue.put( (max_bandwidth - bandwidth, outport) )
                node_visited[outport] = True

                #start a modified Dijkstra
                while not process_queue.empty():
                    item = process_queue.get()
                    node_id = item[1]
                     
                    #looking for available outgoing from the node
                    ports = adjacent[node_id]
                    count_port = 0
                    for next_node in ports:
                        if next_node == -1:
                            count_port = count_port+1
                            continue
                        #if next node is not a ban node and isn't visited yet
                        elif next_node != ban_node and not node_visited[next_node]:
                            #need to get from actual bandwidth map, node -> outport
                            bandwidth = get_bandwidth_on_link(node_id,count_port)
                            bandwidth = min(bandwidth, node_avai_bandw[node_id])
                            node_avai_bandw[next_node] = bandwidth
                            node_visited[next_node] = True
                            #if next node is a switch then add to queue for further processing
                            if next_node < len(switch_nodes):
                                process_queue.put( (max_bandwidth - bandwidth, next_node) )
                            count_port = count_port + 1
                        else:
                            count_port = count_port + 1

                #after get all the results of each server 

                #calculate total bandwidth
                total_bandwidth = 0
                for i in range(len(switch_nodes),len(switch_nodes)+len(server_nodes)):
                    if node_visited[i]:
                        print nodes[i] + " : bw " + str(node_avai_bandw[i])
                        total_bandwidth = total_bandwidth + node_avai_bandw[i]
                print "total bandwidth for " + nodes[index] + "-eth" + str(port_num+1) + " : " + str(total_bandwidth)

            port_num = port_num + 1
        index = index + 1

                 

if __name__ == '__main__':
    global nodes
    global server_nodes
    global switch_nodes
    topo_detail = open('topology_detail.txt','r')
    
    line = ""
    item = line.split()
    #start mapping nodes
    while len(item) == 0 or item[0] != 'node':
        line = topo_detail.readline()
        item = line.split()


    line = topo_detail.readline()
    item = line.split()
    while len(item) > 0:

        #found server
        if "." in item[1]:
            server_nodes.append(item[0])
            server[item[1]] = item[0]

        #found switch
        elif ":" in item[1]:
            switch_nodes.append(item[0])
            switches[item[1]] = item[0]

        line = topo_detail.readline()
        item = line.split()

    switch_nodes.sort()
    nodes = switch_nodes + server_nodes
        

    
    #start building adjacent matrix 
    #adjacent information on tology_detail.txt contains only switches' adjacent information
    #row of adjacent equal to number of switch

    line = topo_detail.readline()
    item = line.split()
    while len(item) == 0 or item[0] != 'adjacent':
        line = topo_detail.readline()
        item = line.split()

    adjacent = [[] for i in range len(switch_nodes)]

    line = topo_detail.readline()
    item = line.split()
    while len(item) > 0:
        row = []
        for i in range(1,len(item)):
            if item[i] in nodes:
                row.append( nodes.index(item[i]) )
            else:
                row.append( -1 )
        adjacent[nodes.index(item[0])] = row
        line = topo_detail.readline()
        item = line.split()

    
    #call method to allocate queue on switch periodically
    #it already has a map so it just has to get bandwidth information from polling
    #assume all the bandwidth available in every link is 3000000 for now
    #need to merge this code and polling.py together
            
    allocate_queue()
    
