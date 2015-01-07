#! /usr/bin/python
#  coding: utf-8

import sys

nodes = []
server_nodes = []
switch_nodes = []
server = {}
adjacent = []

if __name__ == '__main__':
    topo_detail = open('topology_detail.txt','r')
    
    line = topo_detail.readline()    
    #start mapping nodes
    if line == 'node':
        line = topo_detail.readline()
        while line != '':
            item = line.split()

            #found server
            if len(item) == 2:
                server_nodes.append(item[0])
                server[item[1]] = item[0]

            #found switch
            elif len(item) ==1:
                switch_nodes.append(item[0])

            line = topo_detail.readline()

        nodes = switch_nodes + server_nodes

    line = topo_detail.realine()
    #start building adjacent matrix
    if line == 'adjacent':
        line = topo_detail.readline()
        while line != '':
            row = []
            item = line.split()
            for i in range(len(item)):
                row.append( nodes.index(item[i]) )
            adjacent.append( row )
                
            
            
    
