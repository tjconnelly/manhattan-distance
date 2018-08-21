import sys
import networkx as nx

from random import randint,choice
from math import inf

try:
  assert sys.version_info.major == 3
except AssertionError:
  sys.exit('EXIT: i require python3')

# {{{ Car
class Car:
  def __init__(self,x,y):
    self.position = (x,y)
    self.last_position = self.position
    self.requests = []
    self.deliveries = []

  def status(self,requests,verbose=False):
    self.requests = requests
    print('position: {0}'.format(self.position))
    print('passengers: {0}'.format(len(self.passengers())))
    print('request queue:')
    for r in requests:
      ps = 'IN CAR' if r.in_transit else 'WAITING'
      print('* {0} {1} | {2} => {3} | {4}'\
            .format(r.name,ps,r.start,r.end,r.time_elapsed()))

  # passengers
  def passengers(self):
    p = []
    return [p.append(r) for r in self.requests if r.in_transit]
      
  def stops_requested(self,requests):
    stops = []
    for r in requests:
      if r.in_transit:
        stops.append(r.end)
      else:
        stops.append(r.start)
    return stops

  # routes
  def move(self,requests,verbose=False):
    # poll options
    # am i creating a socialist bus system? maybe.
    options = {}
    for r in requests:
      vote = r.path[1]
      try:
        # egalite
        #options[vote]+=1
        # each according to his need
        options[vote]+=(r.time_elapsed())
      except KeyError:
        options[vote]=1
    # and the winner is
    nextmove = sorted(options.keys(),key=lambda k: options[k],reverse=True)
    if verbose: print('moving to {0} (votes: {1})'\
                      .format(nextmove[0],options[nextmove[0]]))
    self.position = nextmove[0]

  def shortest_distance(self,stop):
    try:
      #routelength = nx.dijkstra_path_length(G,self.position,stop)
      return nx.shortest_path_length(G,self.position,stop)
    except nx.NodeNotFound as err:
      print('ERROR: {0}'.format(err))
      return None

  def route(self,stop):
    try:
      #routelength = nx.dijkstra_path_length(G,self.position,stop)
      return nx.shortest_path(G,self.position,stop)
    except nx.NoPath as err:
      print('ERROR: {0}'.format(err))
      return None
    
# }}}

# {{{ Rider
class Rider:
  def __init__(self,**kwargs):
    for k,v in kwargs.items():
      setattr(self,k,v)
    self.in_transit = False
    self.wait_time = 0
    self.travel_time = 0
    # resets every step
    self.path = []
    self.next = None

  def target(self):
    return self.end if self.in_transit else self.start

  def time_elapsed(self):
    return sum([self.wait_time,self.travel_time])

  def __str__(self):
    string = 'Rider:\n'
    for a in ['name','start','end','path']:
      string += '  {0}: {1}\n'.format(a,getattr(self,a))
    return string
# }}}

# {{{ Session
class Session:
  def __init__(self,interactive=True):
    self.verbose = False
    # graph
    if interactive:
      self.x_axis = self.dimension('X')
      self.y_axis = self.dimension('Y')
    else:
      self.x_axis=10
      self.y_axis=10
    # riders
    self.names = self.rnames()
    self.requests = []
    self.complete = []
    # time
    self.step = 0

  def conductor(self,vertex,requests,verbose=False):
    for r in requests:
      if r.start == vertex and r.in_transit is False:
        r.in_transit = True
        if verbose: print('{0} BOARDED at {1}'.format(r.name,vertex))
      if r.end == vertex and r.in_transit is True:
        r.in_transit = False
        if verbose: print('{0} EXITED at {1}'.format(r.name,vertex))
        requests.remove(r)
        self.complete.append(r)
    return requests

  def advance_time(self,requests):
    for r in requests:
      if r.in_transit:
        r.travel_time+=1
      else:
        r.wait_time+=1
    self.step+=1
    
  def dimension(self,axis):
    c = 0
    while (c < 1):
      try:
        c = int(input('enter {0} dimension: '.format(axis)))
        return c+1
      except ValueError:
        print('{0} must be an integer'.format(axis))

  def rnames(self,wordfile=None):
    if wordfile is None:
      wordfile='/usr/share/dict/words'
    try:
      return open(wordfile).read().splitlines()
    except FileNotFoundError:
      return []

  def populate(self,max):
    rq = []
    if max is None:
      max = randint(0,math.inf)
    while (len(rq) < max):
      rq.append(Rider(**{
        'name':   choice(self.names),
        'start':  (randint(0,self.x_axis-1),randint(0,self.y_axis-1)),
        'end':    (randint(0,self.x_axis-1),randint(0,self.y_axis-1)),
        # FIXME: make sure start+end aren't the same vertex
      }))
    return rq
# }}}
      
### MAIN
sz = Session()
sz.verbose = True

# generate graph
G = nx.grid_2d_graph(sz.x_axis,sz.y_axis)
#if sz.verbose: 
#  print('generated {0}x{1} grid; {2} nodes, {3} edges'\
#      .format(sz.x_axis,sz.y_axis,G.number_of_nodes(),G.number_of_edges()))

# init car, generate requests
herbie = Car(0,0) # TODO: maybe this is worth randomizing?
requests = sz.populate(10)
herbie.status(requests,verbose=True)

#herbie.stops = herbie.stops_requested(requests)

while (len(requests) > 0):
  if sz.verbose: print('TOTAL ELAPSED: {0}'.format(sz.step))

  # pickup/deliver passengers
  requests = sz.conductor(herbie.position,requests,verbose=sz.verbose)

  # advance time
  ready = input('next turn? ')
  sz.advance_time(requests)

  # compute routes
  for r in requests:
    r.path = herbie.route(r.target())

  # decide next move
  herbie.move(requests,verbose=sz.verbose)

  # status
  herbie.status(requests,verbose=sz.verbose)
  print()
### END
