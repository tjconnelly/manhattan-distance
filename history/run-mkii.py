import sys
import os
import networkx as nx
import texttable 
from progress.bar import Bar 

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

    self.busy = False
    self.director = False

    self.complete = []

  # manage passengers
  def passengers(self):
    p = []
    return [p.append(r) for r in self.requests if r.in_transit]

  def conductor(self):
    for r in self.requests:
      if r.start == self.position and r.in_transit is False:
        # pick up passenger
        r.in_transit = True
        if self.verbose: print('{0} BOARDED at {1}'\
                                .format(r.name,self.position))
      if r.end == self.position and r.in_transit is True:
        # drop off passenger
        r.in_transit = False
        self.requests.remove(r)
        r.delivered = True
        self.complete.append(r)
        if self.verbose: print('{0} EXITED at {1}'\
                                .format(r.name,self.position))

  # navigate
  def recompute(self,city):
    for r in self.requests:
      r.path = r.route(city,self.position)
      if r.start == r.end:
        del r

  # move
  def move(self,city,elapsed):
    origin = self.position

    if len(self.director.path) == 0:
      self.director.path = self.director.route(city,self.position)

    if len(self.director.path)>1 and self.director.path[0] == self.position:
      del self.director.path[0]

    nextmove = self.director.path[0]
    if self.verbose: print('round {0}: moving from {1} to {2}'\
                           .format(elapsed,self.position,nextmove))
    self.position = nextmove
    del self.director.path[0]

  # routes
  def proximity(self):
    # shortest path next
    if (len(self.requests)>0):
      moves = sorted(self.requests,key=lambda r: len(r.path))
      winner = moves[0] # this is arbitrary if len(r.path) results in ties
      if self.verbose: print('NEW WINNER: {0} ({1} moves to {2})'\
                          .format(winner.name,len(winner.path),winner.target()))
      self.busy = True
      self.director = winner
    # FUTURE: if two riders have same target go there
    # FUTURE: find clusters of riders in a given size of 'neighborhood'
      
  # XXX: thing here is, eventually with two riders left they'll deadlock
  #def socialism(self):
  #  # poll options
  #  options = {}
  #  for r in self.requests:
  #    # am i creating a socialist bus system? maybe.
  #    vote = r.path[1]
  #    try:
  #      # egalite
  #      #options[vote]+=1
  #      # each according to his need
  #      #options[vote]+=(r.timer())
  #      # come in from the rain
  #      #options[vote]+=1 if r.in_transit else 1.5
  #    except KeyError:
  #      options[vote]=1
  #  # and the winner is
  #  nextmove = sorted(options.keys(),key=lambda k: options[k],reverse=True)
  #  if self.verbose: print('moving to {0} (votes: {1})'\
  #                    .format(nextmove[0],options[nextmove[0]]))
  #  self.position = nextmove[0]

  # displays
  def status(self):
    ls = 'off' if self.busy else 'ON'
    print('HERBIE: at {0} | {1} passengers | light {2}'\
          .format(self.position,len(self.passengers()),ls))
    if self.busy is True:
      ds = 'delivering' if self.director.in_transit else 'picking up'
      print('SORTIE: {0} {1} -> {2}'
            .format(ds,self.director.name,self.director.target()))
  
  def queue(self,dataset):
    print('passengers:')
    table = texttable.Texttable()
    table.set_deco(table.HEADER)
    table.set_cols_align(['l','c','l','c','l'])
    table.set_cols_width([24,3,20,3,10])
    for r in sorted(dataset,key=lambda r: len(r.path)):
      if r.delivered:
        ps = 'DELIVERED'
      else:
        ps = 'IN CAR' if r.in_transit else 'WAITING'
      #print('* {0} {1} | {2} => {3} | {4}'\
      #      .format(r.name,ps,r.start,r.end,r.timer()))
      table.add_row(['* '+r.name,
                     len(r.path),
                     '{0}->{1}'.format(r.start,r.end),
                     r.timer(),
                     ps])
    print(table.draw()) 
# }}}

# {{{ Rider
class Rider:
  def __init__(self,**kwargs):
    for k,v in kwargs.items():
      setattr(self,k,v)
    self.in_transit = False
    self.delivered = False
    self.wait_time = 0
    self.travel_time = 0
    # resets every step
    # yeah don't do that
    self.path = []
    self.next = None

  def target(self):
    return self.end if self.in_transit else self.start

  def timer(self):
    return sum([self.wait_time,self.travel_time])

  def route(self,city,position):
    # populates self.path; can't be run at init because where's the car
    try:
      #routelength = nx.dijkstra_path_length(city,self.position,stop)
      return nx.shortest_path(city,position,self.target())
    except nx.NoPath as err:
      print('ERROR: {0}'.format(err))
      return None

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
      self.x = 50
      self.y = 50
    self.auto = False if interactive else True

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

  def graph(self,echo=True):
    G = nx.grid_2d_graph(self.x,self.y)
    if echo and self.verbose: 
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
      }))
    return rq
# }}}

      
### MAIN
# env
#mgr = Session(interactive=False)
#mgr.verbose = False
mgr = Session(interactive=True)
mgr.verbose = True

# generate graph
mgr.city = mgr.graph(echo=True)

# init car
init_x,init_y = mgr.populate(1)[0].start
herbie = Car(init_x,init_y)

# generate requests
#herbie.requests = mgr.populate(10) # <- set to 'None' for infinite requests
herbie.requests = mgr.populate(randint(10,50))

# init car
herbie.status()
herbie.verbose = mgr.verbose

if not mgr.verbose: bar = Bar('vroom',max=len(herbie.requests)*2)
while (len(herbie.requests)>0):
  # display request queue
  if mgr.verbose:
    if mgr.step>0:
      os.system('clear')
    print('TIME ELAPSED: {0}'.format(mgr.step))
    herbie.queue(herbie.requests)
    print()

  # order of operations here is a little crazy
  # after the initial loop, there is always a director
  if herbie.director and herbie.position == herbie.director.target():
    # pickup/deliver passenger
    herbie.conductor()
    if not mgr.verbose: bar.next()
    # compute for next stop
    herbie.recompute(mgr.city)
    herbie.proximity()
    if mgr.verbose: print()

  # first loop only
  if herbie.director is False:
    herbie.recompute(mgr.city)
    herbie.proximity()
    if not mgr.auto:
      mode = input("enter 'auto' to disable prompts: ")
      mgr.auto = True if mode == 'auto' else False

  # status
  if mgr.verbose:
    herbie.status()
    print()

  # travel in time and relative dimensions in space
  if len(herbie.requests)>0:
    mgr.advance(herbie.requests)
    herbie.move(mgr.city,mgr.step)
    if not mgr.auto:
      nt = input("next turn? [enter 'auto' to disable prompts] ")
      mgr.auto = True if nt == 'auto' else False

if not mgr.verbose: bar.finish()
print('FINISHED! OFF DUTY!\n')
herbie.queue(herbie.complete)
### END
