import sys
import networkx as nx
import texttable 

from random import randint,choice
from math import inf

try:
  assert sys.version_info.major == 3
except AssertionError:
  sys.exit('EXIT: i require python3')

# {{{ Car
class Car:
  def __init__(self,x,y):
    self.requests = []
    self.position = (x,y)
    self.verbose = False

    self.complete = []

  def status(self):
    print('position: {0}'.format(self.position))
    print('passengers: {0}'.format(len(self.passengers())))
    print('request queue:')
    table = texttable.Texttable()
    table.set_deco(table.HEADER)
    table.set_cols_align(['l','c','l','l'])
    table.set_cols_width([20,3,18,8])
    for r in self.requests:
      ps = 'IN CAR' if r.in_transit else 'WAITING'
      #print('* {0} {1} | {2} => {3} | {4}'\
      #      .format(r.name,ps,r.start,r.end,r.timer()))
      table.add_row(['* '+r.name,r.timer(),'{0}->{1}'.format(r.start,r.end),ps])
    print(table.draw()) 

  # passengers
  def passengers(self):
    p = []
    return [p.append(r) for r in self.requests if r.in_transit]
      
  def stops_requested(self):
    stops = []
    for r in self.requests:
      if r.in_transit:
        stops.append(r.end)
      else:
        stops.append(r.start)
    return stops

  # routes
  def move(self):
    # poll options
    options = {}
    for r in self.requests:
      # am i creating a socialist bus system? maybe.
      vote = r.path[1]
      try:
        # egalite
        #options[vote]+=1
        # each according to his need
        #options[vote]+=(r.timer())
        # come in from the rain
        options[vote]+=1 if r.in_transit else 1.5
      except KeyError:
        options[vote]=1
    # and the winner is
    nextmove = sorted(options.keys(),key=lambda k: options[k],reverse=True)
    if self.verbose: print('moving to {0} (votes: {1})'\
                      .format(nextmove[0],options[nextmove[0]]))
    self.position = nextmove[0]

  def route(self,city,stop):
    try:
      #routelength = nx.dijkstra_path_length(city,self.position,stop)
      return nx.shortest_path(city,self.position,stop)
    except nx.NoPath as err:
      print('ERROR: {0}'.format(err))
      return None

  def conductor(self):
    for r in self.requests:
      if r.start == self.position and r.in_transit is False:
        r.in_transit = True
        if self.verbose: print('{0} BOARDED at {1}'\
                                .format(r.name,self.position))
      if r.end == self.position and r.in_transit is True:
        r.in_transit = False
        if self.verbose: print('{0} EXITED at {1}'\
                                .format(r.name,self.position))
        self.requests.remove(r)
        self.complete.append(r)
    return self.requests
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

  def timer(self):
    return sum([self.wait_time,self.travel_time])

  def __str__(self):
    string = 'Rider:\n'
    for a in ['name','start','end','path']:
      string += '  {0}: {1}\n'.format(a,getattr(self,a))
    return string
# }}}

# {{{ Session
class Session:
  def __init__(self,interactive=False,verbose=False):
    # env
    self.verbose = verbose
    self.names = self.rnames()
    # time
    self.step = 0
    # graph
    if interactive:
      self.x = self.dimension('X')
      self.y = self.dimension('Y')
    else:
      self.x = 10
      self.y = 10

  # time
  def advance(self,requests):
    for r in requests:
      if r.in_transit:
        r.travel_time+=1
      else:
        r.wait_time+=1
    self.step+=1
    
  # graph
  def dimension(self,axis):
    c = 0
    while (c < 1):
      try:
        c = int(input('enter {0} dimension: '.format(axis)))
        return c
      except ValueError:
        print('{0} must be an integer'.format(axis))

  def graph(self):
    G = nx.grid_2d_graph(self.x,self.y)
    if self.verbose: 
      print('generated {0}x{1} grid; {2} vertices, {3} edges'\
            .format(self.x,self.y,G.number_of_nodes(),G.number_of_edges()))
    return G

  # riders
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
        'start':  (randint(0,self.x-1),randint(0,self.y-1)),
        'end':    (randint(0,self.x-1),randint(0,self.y-1)),
        # FIXME: make sure start+end aren't the same vertex
      }))
    return rq
# }}}

      
### MAIN
#mgr = Session(interactive=False)
mgr = Session(interactive=True)
mgr.verbose = True

# generate graph
mgr.city = mgr.graph()

# init car
herbie = Car(0,0) # TODO: maybe this is worth randomizing?

# generate requests
herbie.requests = mgr.populate(10) # <- set to 'None' for infinite requests

# init car
herbie.status()
herbie.verbose = mgr.verbose

while (len(herbie.requests) > 0):

  # pickup/deliver passengers
  herbie.requests = herbie.conductor()

  # advance time
  ready = input('next turn? ')
  mgr.advance(herbie.requests)
  print()

  # compute routes
  for r in herbie.requests:
    r.path = herbie.route(mgr.city,r.target())

  # decide next move
  herbie.move()

  # status
  if mgr.verbose: herbie.status()
  if mgr.verbose: print('TOTAL ELAPSED: {0}'.format(mgr.step))
### END
