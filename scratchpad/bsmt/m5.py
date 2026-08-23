import sys; sys.path.insert(0,'scratchpad/bsmt')
from boxes import run
P='docs/photos-jpg/Movie Room v3 4.jpg'
B = {
 'ceil_a':   (840, 60,1050,200),
 'ceil_b':   (150, 60, 330,180),
 'S_up_a':   (430,300, 590,420),
 'S_up_b':   (330,345, 425,470),
 'W_up_a':   (1060,445,1190,545),
 'W_up_b':   (800,300,1030,385),
 'S_low':    (150,565, 245,645),
 'W_low':    (930,645,1008,706),
 'plank_a':  (760,1470, 880,1580),
 'plank_b':  (105,1150, 200,1345),
 'rug':      (350,1100, 700,1400),
 'sofa_a':   (762,600, 848,655),
 'sofa_b':   (560,655, 660,700),
 'chair':    (172,782, 262,862),
 'blkpill':  (452,496, 530,530),
 'blkcube':  (1000,1250,1120,1420),
}
run(P, B, 'scratchpad/bsmt/p4_boxes.png')
