#! /usr/bin/python
#  coding: utf-8

import sys
import Queue

nodes = []
server_nodes = []
switch_nodes = []
server = {}
switches = {}
switches_dpid = {}
adjacent = []
max_bandwidth = 3000000

linkbandwidth = 10.0
traffic_file_name = "/home/mininet/floodlight-qos-beta-master/traffic.txt"
switchnum = 0
traffic_data = {}
name_index = {}
bandwidthout = [[]]
f_ptr = 0

#dummy data for test
poll_map = [
[3000000, 3000000, 3000000, 3000000, 3000000], 
[3000000, 3000000, 3000000, 3000000, 3000000], 
[3000000, 3000000, 3000000, 3000000, 3000000], 
[3000000, 3000000, 3000000, 3000000, 3000000], 
[3000000, 3000000, 3000000, 3000000]]

def build_port_name():
    global name_index

    page = urllib.request.urlopen('http://localhost:8080/wm/core/controller/switches/json')
    line = page.read().decode("utf-8")

    collections = json.loads(line)

    switchnum = len(collections)
    
    for sw in collections:
        dpid = sw["dpid"]
        port_detail = {}
        ports = sw["ports"]
        for each_port in ports:
            port_detail[each_port["portNumber"]] = each_port["name"]
        name_index[dpid] = port_detail
        

def parsejson():
    global traffic_data
    global traffic_file_name
    global name_index
    global f_ptr 
    global bandwidthout
    global switchnum

    page = urllib.request.urlopen('http://localhost:8080/wm/core/switch/all/flow/json')
    
    line = page.read().decode("utf-8")

    f_ptr = open(traffic_file_name,'w',encoding='utf-8')
    new_traffic_data = {}
    switch_dicts = json.loads(line)
    for switch_id in switch_dicts:
        if switch_id in name_index:
            switch_index = nodes.index(switches[switch_id])
            for flow in switch_dicts[switch_id]:
                match = flow["match"]
                actions = flow["actions"]

                for action in actions:
                    if action["type"] == "OUTPUT":
                        total_duration = 0
                        total_byte = 0
                        found = False
                        if (switch_id,action["port"]) in traffic_data:
                            temp_traffic = traffic_data[(switch_id,action["port"])]
                            if str(match) in temp_traffic:
                                found = True
                                temp_flow = temp_traffic[str(match)]
                                old_duration = temp_flow["duration"]
                                old_bytecount = temp_flow["byteCount"]
                                total_duration = (flow["durationSeconds"]+flow["durationNanoseconds"]/1000000000)-old_duration
                                total_byte = flow["byteCount"]-old_bytecount
                            
                        if not found:
                            total_duration = (flow["durationSeconds"]+flow["durationNanoseconds"]/1000000000)
                            total_byte = flow["byteCount"]

                        buildkey = (switch_id,action["port"])
                        
                        #add information into globall traffic data for next iteration 
                        if buildkey not in new_traffic_data:
                            new_traffic_data[buildkey] = {}
                        new_traffic_data[buildkey][str(match)] = {}
                        new_traffic_data[buildkey][str(match)]["duration"] = (flow["durationSeconds"]+flow["durationNanoseconds"]/1000000000)
                        new_traffic_data[buildkey][str(match)]["byteCount"] = flow["byteCount"]
                        
                        bw = ((total_byte*8)/(total_duration))/1000000
                        bandwidthout[switch_index][action["port"]-1][0] = bandwidthout[switch_index][action["port"]-1] - bw

                        destination = match["networkDestination"]
                        if destination in server:
                            server_name = server[destination]
                            server_index = server_nodes.index(server_name)+1
                            bandwidthout[switch_index][action["port"]-1][server_index] = bandwidthout[switch_index][action["port"]-1][server_index] + bw
                           
    f_ptr.write(str(switchnum) + "\t" + str(switchnumport) + "\n")
#if switch_id in name_index:
#switch_index = nodes.index(switches[switch_id])
    for key in name_index:
        f_ptr.write(key + "\n" + nodes.index(key)+"\n")

    for sw in range( len(bandwidthout) ):
        for port in range ( len(sw) ):
            f_ptr.write(str(bandwidthout[sw][port]) + " ")
        f_ptr.write("\n")
    print("-----------------------------------------------------")
    f_ptr.closed
    traffic_data = new_traffic_data
                        


def get_bandwidth_on_link(switch,outport):
    sw = bandwidthout[switch]
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
    global bandwidthout
    global max_bandwidth

    build_port_name()

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
            switches_dpid[item[0]] = item[1]

        line = topo_detail.readline()
        item = line.split()

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

    

    #begin the loop 

    #initial banwidthout
    bandwidthout = []
    for adj_row in adjacent:
        bw_row = [[] for i in range( len(adj_row)) ]
        for i in range( len(bw_row) ):
            row_info = [0 for j in range( len(server)+1 ) ]
        bandwidthout.append(bw_row)
    
    parsejson()

    #call method to allocate queue on switch periodically
    #it already has a map so it just has to get bandwidth information from polling
    #assume all the bandwidth available in every link is 3000000 for now
    #need to merge this code and polling.py together
            
    allocate_queue()
    
    #end the loop
