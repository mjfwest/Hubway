#! python
"""
Find the best route that connects all the rental stations in the Boston Hubway 
bike rental network (http://www.thehubway.com/). This is essentially a
travelling salesman problem.

Richard West
r.h.west@gmail.com
"""

from xml.etree.ElementTree import ElementTree
import urllib2
import urllib
import json
import os
import numpy
import time
import random

class Station():
    def __init__(self):
        self.id = 0
    def __repr__(self):
        return "<Station %2d>" % self.id
    def __str__(self):
        return self.lat+','+self.long
    def prettystring(self):
        return "%s at %s"%(self.name, str(self))
    pass


def distancematrix(startplaces,endplaces):
    geo_args = {
        'origins': startplaces,
        'destinations': endplaces,
        'mode': 'bicycling',
        'sensor': "false",
        }
    BASE_URL = 'http://maps.googleapis.com/maps/api/distancematrix/json'
    url = BASE_URL + '?' + urllib.urlencode(geo_args)
    result = json.load(urllib2.urlopen(url))
    assert(result['status']!='OVER_QUERY_LIMIT')

    
    times = numpy.zeros((len(result['origin_addresses']), len(result['destination_addresses'])), dtype=numpy.int32) # times in seconds
    distances = numpy.zeros((len(result['origin_addresses']), len(result['destination_addresses'])), dtype=numpy.int32) # distances in m
    for i,row in enumerate(result['rows']):
        for j,element in enumerate(row['elements']):
            if element['status']=='ZERO_RESULTS':
                print 'ZERO_RESULTS for '  + result['origin_addresses'][i]  + ' to ' + result['destination_addresses'][j]
                times[i][j]=-1
                distances[i][j]=-1
            else:
                times[i][j] = element['duration']['value']
                distances[i][j] = element['distance']['value']
    return times,distances,result
        
        
stations_file = urllib2.urlopen('http://thehubway.com/data/stations/bikeStations.xml')

tree = ElementTree()
tree.parse(stations_file)
stations = list()
for s in tree.iter('station'):
    station = Station()
    station.id = int(s.find('id').text)
    station.lat = s.find('lat').text
    station.long = s.find('long').text
    station.name = s.find('name').text
    stations.append(station)

##################### Change These ####################### 
number_of_hackers=2     # This partitions the problem
this_hacker=0           # hacker number 0 of 2
debug=2000       #debug is a limit for testing, make it very big for a full run
data_dir = 'data'
os.path.exists(data_dir) or os.mkdir(data_dir)

assert this_hacker < number_of_hackers
number_each=int(numpy.ceil(len(stations)/float(number_of_hackers)))
startstations=stations[this_hacker*number_each:(this_hacker+1)*number_each]
endstations=stations

number_of_rowblocks=min(debug,int(numpy.ceil(number_each/10.0)))
number_of_colblocks=min(debug,int(numpy.ceil(len(stations)/10.0)))

for idx_row in xrange(number_of_rowblocks):
    for idx_col in xrange(number_of_colblocks):
        startplaces_ids = '|'.join([str(s.id).rjust(2) for s in stations[this_hacker*number_each:(this_hacker+1)*number_each][idx_row*10:(idx_row+1)*10] ])
        endplaces_ids = '|'.join([str(s.id).rjust(2) for s in stations[(idx_col*10):(idx_col+1)*10]])
        #make a check matrix of start->end ids. 
        startplaces_list = [s.id for s in stations[this_hacker*number_each:(this_hacker+1)*number_each][idx_row*10:(idx_row+1)*10] ]
        endplaces_list = [s.id for s in stations[(idx_col*10):(idx_col+1)*10]]
        checkmatrix=numpy.empty((len(startplaces_list),len(endplaces_list)))
        for idx_block_row,start in enumerate(startplaces_list):
            for idx_block_col,end in enumerate(endplaces_list):
                checkmatrix[idx_block_row,idx_block_col]=start*1000+end
        
        startplaces = '|'.join([str(s) for s in stations[this_hacker*number_each:(this_hacker+1)*number_each][idx_row*10:(idx_row+1)*10] ])
        endplaces = '|'.join([str(s) for s in stations[(idx_col*10):(idx_col+1)*10]])
        print 'start ' + startplaces_ids +',  end ' + endplaces_ids
         
        
        distfilename = os.path.join(data_dir,'dist_matrix_'+str(this_hacker*number_of_rowblocks+idx_row)+'_'+str(idx_col)+'.txt')
        timefilename = os.path.join(data_dir,'time_matrix_'+str(this_hacker*number_of_rowblocks+idx_row)+'_'+str(idx_col)+'.txt')
        checkfilename = os.path.join(data_dir,'check_matrix_'+str(this_hacker*number_of_rowblocks+idx_row)+'_'+str(idx_col)+'.txt')
        jsonfilename = os.path.join(data_dir,'json_result_'+str(this_hacker*number_of_rowblocks+idx_row)+'_'+str(idx_col)+'.js')
        if os.path.exists(distfilename) and os.path.exists(timefilename) and os.path.exists(jsonfilename):
            print 'skipping ' + distfilename + ' and ' + timefilename + ' and ' + jsonfilename
        else:
            times,distances,result = distancematrix(startplaces,endplaces)
            with open(jsonfilename,'w') as f:
                 f.write(json.dumps(result))
            #with open(timefilename,'w') as f:
            #        distances.tofile(f)
            numpy.savetxt(distfilename,distances)
            numpy.savetxt(timefilename,times)
            print 'writing ' + distfilename + ' and ' + timefilename      
            time.sleep(numpy.random.rand()*2+12)
        if not os.path.exists(checkfilename):
            numpy.savetxt(checkfilename,checkmatrix)
            
from matplotlib import pyplot as plt

times=numpy.zeros((len(stations),len(stations)),dtype=numpy.int32)
time_matrix_list=[a for a in os.listdir(data_dir) if a.startswith('time_matrix') and a.endswith('.txt')]
for time_matrix in time_matrix_list:
    row,col=time_matrix.split('.')[0].split('_')[2:4]
    row=int(row)
    col=int(col)
    timesblock=numpy.loadtxt(os.path.join(data_dir,time_matrix),ndmin=2)
    print("row {row}, col {col}, block shape = {blockshape}").format(row=row,col=col,blockshape=timesblock.shape)
    block_rows,block_cols=timesblock.shape
    times[row*10:row*10+block_rows,col*10:col*10+block_cols]=timesblock
check=numpy.zeros((len(stations),len(stations)),dtype=numpy.int32)
check_matrix_list=[a for a in os.listdir(data_dir) if a.startswith('check_matrix') and a.endswith('.txt')]
for check_matrix in check_matrix_list:
    row,col=check_matrix.split('.')[0].split('_')[2:4]
    row=int(row)
    col=int(col)
    checkblock=numpy.genfromtxt(os.path.join(data_dir,check_matrix))
    rows,cols=checkblock.shape
    check[row*10:row*10+rows,col*10:col*10+cols]=checkblock

start=check/1000       
end=check%100     
  
plt.spy(times)

plt.spy(times==-1) 
# the shape of this is discouraging: did we screw up somewhere?

# get the rows with more than one negative one
inaccessible_stations = set(((times==-1).sum(1)>1).nonzero()[0])
# add the columns with more than one negative one
inaccessible_stations = inaccessible_stations.union(((times==-1).sum(0)>1).nonzero()[0])
print "Difficulty accessing these stations, so removing them:"
for s in inaccessible_stations:
    print stations[s].prettystring()
keepers = range(len(times))
for s in inaccessible_stations:
    keepers.remove(s)
    
print "Also removing these stations, just for testing:"
for s in range(0):
    if s in keepers:
        print stations[s].prettystring()
        keepers.remove(s)
    
pruned_times = times[keepers][:,keepers]
pruned_stations = [stations[i] for i in range(len(stations)) if i in keepers]
plt.spy(pruned_times==-1)

### Now for the good stuff, based on tsp.py
# Copyright 2010-2012 Google
# Licensed under the Apache License, Version 2.0




from google.apputils import app
import gflags
import os
import sys
# set OR_TOOLS_PATH in your environment to override the default
or_tools_path = '/Users/rwest/XCodeProjects/google-or-tools/trunk'
if not os.path.exists(or_tools_path):
    or_tools_path = 'or_tools_path'
or_tools_path = os.getenv('OR_TOOLS_PATH',or_tools_path)
sys.path.append(os.path.join(or_tools_path,'src'))

from constraint_solver import pywraprouting


def Distance(i, j):
  """The distance from i to j"""
  return pruned_times[i,j]
 
tsp_size = len(pruned_times)
forbidden_connections = [] # a list of tuples of forbidden connections

sorted_stations = []

if True:
    # TSP of size FLAGS.tsp_size
    # Second argument = 1 to build a single tour (it's a TSP).
    # Nodes are indexed from 0 to FLAGS_tsp_size - 1, by default the start of
    # the route is node 0.
    routing = pywraprouting.RoutingModel(tsp_size, 1)
    # Setting first solution heuristic (cheapest addition).
    routing.SetCommandLineOption('routing_first_solution', 'PathCheapestArc')
    # Disabling Large Neighborhood Search, comment out to activate it.
    # routing.SetCommandLineOption('routing_no_lns', 'true')
    
    # Setting the cost function.
    # Put a callback to the distance accessor here. The callback takes two
    # arguments (the from and to node inidices) and returns the distance between
    # these nodes.
    routing.SetCost(Distance)

    for from_node,to_node in forbidden_connections:
      if routing.NextVar(from_node).Contains(to_node):
        print 'Forbidding connection ' + str(from_node) + ' -> ' + str(to_node)
        routing.NextVar(from_node).RemoveValue(to_node)

    # Solve, returns a solution if any.
    assignment = routing.Solve()
    if assignment:
      # Solution cost.
      print "total time:", assignment.ObjectiveValue()
      # Inspect solution.
      # Only one route here; otherwise iterate from 0 to routing.vehicles() - 1
      route_number = 0
      node = routing.Start(route_number)
      route = ''
      while not routing.IsEnd(node):
        station = pruned_stations[int(node)]
        route += station.prettystring() + ' -> \n'
        sorted_stations.append({'name': station.name, 'lat':station.lat, 'long':station.long})
        node = assignment.Value(routing.NextVar(node))

      route += '0'
      print route
    else:
      print 'No solution found.'

with open('route.json','w') as f:
    json.dump(sorted_stations,f)
