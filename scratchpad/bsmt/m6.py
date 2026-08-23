import sys; sys.path.insert(0,'scratchpad/bsmt')
from boxes import run
P='docs/photos-jpg/Movie Room v3 4.jpg'
B = {
 'ottoman_top':(505,645, 615,682),
 'sofa_seat':  (700,640, 760,672),
 'sofa_back':  (660,585, 700,612),
 'chair_body': (283,930, 350,1000),
 'chair_arm':  (95,900, 148,975),
 'crown':      (430,290, 600,305),
 'rail':       (300,536, 420,548),
 'base':       (900,745, 990,762),
 'art':        (790,398,1040,478),
 'grey_throw': (700,545, 790,585),
}
run(P, B, 'scratchpad/bsmt/p4_boxes2.png')
