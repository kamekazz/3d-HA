import sys; sys.path.insert(0,'scratchpad/bsmt')
from boxes import run
P='docs/photos-jpg/Movie Room v3 4.jpg'
B = {
 'ceiling':      (840, 60,1050,200),
 'wallL_up':     (430,300, 590,420),
 'wallR_up':     (1060,440,1190,540),
 'wallR_low':    (1130,600,1195,720),
 'wallL_low':    (250,560, 330,610),
 'plank':        (760,1470, 880,1580),
 'rug':          (350,1100, 700,1400),
 'sofa':         (520,680, 680,745),
 'chair':        (330,890, 430,960),
 'black':        (990,1230,1120,1420),
}
run(P, B, 'scratchpad/bsmt/p4_boxes.png')
