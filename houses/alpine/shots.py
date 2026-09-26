"""Revision 3: quick descent, complete pool crossing on axis, center-door entry.

64 seconds, continuous. Center salon -> kitchen -> dining -> stair hall -> living
-> library -> salon -> gardens. The garden/reveal tail from 43 s matches revision 2.
"""

def K(t,cam,tgt,lens=24,fstop=8,exp=.45,label='',focus=None):
    return dict(t=t,cam=cam,tgt=tgt,lens=lens,fstop=fstop,exp=exp,label=label,focus=focus)

_keys=[
 K(0,(0,49,11),(0,23,2.8),26,11,.62,'Centered pool-side aerial'),
 K(1.2,(0,44,6.0),(0,18.0,2.8),26,10,.62,'Fast descent toward the far pool edge'),
 K(2.1,(0,39.1,2.3),(0,18.0,2.6),26,9,.62,'Dropping into the central axis'),
 K(2.6,(0,37.2,1.3),(0,18.0,2.5),26,9,.62,'Clearing the flower border'),
 K(3.1,(0,35.60,.50),(0,18.0,2.5),26,9,.62,'Far water edge'),
 K(3.4,(0,35.25,.37),(0,18.0,2.4),26,9,.62,'Settling onto the pool surface'),
 K(3.7,(0,34.9,.36),(0,18.0,2.4),26,9,.62,'Beginning the full pool skim'),
 K(5.5,(0,32.25,.34),(0,18.0,2.4),26,9,.62,'Skimming the center of the pool'),
 K(7.2,(0,29.7,.35),(0,18.0,2.3),26,9,.62,'Crossing to the near edge'),
 K(7.6,(0,29.0,.35),(0,18.0,2.3),26,9,.62,'Low glide continues to the near edge'),
 K(8.0,(0,28.35,.40),(0,18.0,2.2),25,9,.61,'Near water edge / rising to the lawn'),
 K(8.8,(0,27.0,1.70),(0,18.0,2.0),25,8,.58,'Clearing the clipped planting'),
 K(9.8,(0,23.7,1.95),(0,16.0,1.95),24,8,.54,'Straight approach to the center doors'),
 K(10.8,(0,20.5,1.98),(0,13.8,1.85),24,8,.48,'Under the central colonnade'),
 K(11.8,(0,18.1,2.0),(0,13.0,1.85),23,8,.39,'Entering through the center French doors'),
 K(13.3,(1.2,16.15,2.0),(3.5,12.8,1.6),23,8,.37,'Garden salon / toward the kitchen'),
 K(14.8,(1.35,13.7,2.0),(6.6,13.2,1.6),23,8,.36,'Turning into the kitchen'),
 K(15.9,(3.4,14.1,2.0),(9.8,13.7,1.6),23,8,.35,'Kitchen threshold'),
 K(17.7,(5.05,15.5,2.05),(9.2,12.9,1.5),23,8,.35,'Island and range wall'),
 K(19.4,(5.15,11.6,2.05),(8.2,8.5,1.6),23,8,.35,'Along the kitchen aisle'),
 K(21.0,(6.4,8.8,2.0),(8.8,4.7,1.6),23,8,.35,'Formal dining room'),
 K(22.5,(5.25,6.8,2.05),(3.8,3.4,1.9),23,8,.35,'Dining room / turn toward the hall'),
 K(23.7,(5.0,4.8,2.05),(1.4,2.0,2.15),23,8,.36,'The hall comes into view'),
 K(25.5,(3.4,3.3,2.10),(-3.0,6.6,3.0),23,8,.38,'Through to the grand stair hall'),
 K(27.0,(1.5,3.6,2.15),(0,9.0,3.3),23,8,.39,'Grand stair reveal'),
 K(28.5,(0,3.6,2.15),(-2.0,8.0,3.2),23,8,.39,'Stair gallery / beginning the left turn'),
 K(30.0,(-1.8,3.3,2.05),(-6.0,4.6,1.7),23,8,.35,'Toward the formal living room'),
 K(31.0,(-3.4,3.3,2.0),(-8.2,4.8,1.7),23,8,.33,'Living room doorway'),
 K(33.0,(-7.05,3.15,1.95),(-9.8,5.7,1.55),23,7,.33,'Linen, brass and walnut'),
 K(35.0,(-7.4,6.2,2.05),(-7.6,10.7,1.8),23,8,.33,'Continuing into the library'),
 K(36.5,(-7.25,9.1,2.05),(-8.2,13.4,1.8),23,8,.33,'The oak library'),
 K(38.5,(-7.35,11.4,2.05),(-5.0,13.1,1.7),23,8,.34,'Library seating and art'),
 K(39.8,(-5.0,13.2,2.05),(.1,17.0,1.65),23,8,.36,'Returning toward the garden salon'),
 K(40.5,(-3.35,13.3,2.0),(0,17.0,1.7),23,8,.37,'Salon / the garden beyond'),
 K(41.5,(-1.25,15.9,2.0),(0,22.0,1.5),24,8,.41,'Toward the center garden doors'),
 # Garden and estate reveal, unchanged from revision 2.
 K(43,(0,18.3,1.95),(0,31.0,1.5),24,8,.48,'Back into the garden light'),
 K(45,(0,23.5,1.80),(0,44.0,1.5),25,10,.61,'The garden axis'),
 K(47.5,(0,32.0,1.45),(0,44.0,1.5),26,10,.62,'Crossing the water toward the roses'),
 K(50,(0,39.8,1.55),(5.0,46.0,1.25),26,9,.62,'The climbing-rose arbor'),
 K(52,(0,44.2,1.50),(5.0,43.0,1.20),28,8,.62,'Layered planting and open rose blooms'),
 K(54,(.15,47.7,1.10),(2.8,42.0,1.10),36,2.8,.62,'Close garden pass / petals and estate',focus=3.2),
 K(55.7,(0,49.5,2.0),(0,30.0,3.0),29,8,.62,'Flowers falling away beneath the camera'),
 K(57.5,(-1.3,52.5,5.0),(3.5,30.5,2.5),28,10,.62,'Rising into the estate reveal'),
 K(60.5,(-3.8,65.0,13.0),(0,28.5,2.2),29,11,.62,'House, pool and formal garden together'),
 K(64,(-5.4,76.0,20.0),(0,37.0,1.5),29,11,.62,'Final estate portrait'),
]
TAKE=dict(name='take',sec=64,door_t=0,door_secs=1,caption=None,keys=_keys)
SHOTS=[TAKE];BY_NAME={'take':TAKE}
TITLES=dict(main='805 NORTH ALPINE DRIVE',sub='BEVERLY HILLS, CALIFORNIA',end='AN EXTRAORDINARY PRIVATE ESTATE')
