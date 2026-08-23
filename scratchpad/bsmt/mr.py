import sys; sys.path.insert(0,'scratchpad/bsmt')
from boxes import run
S='scratchpad/shots/v3_movie/'
run(S+'look_n.png', {'N_up':(600,300,690,470),'N_up2':(940,300,1035,465),
                     'N_low':(905,560,1035,645),'ceil':(200,120,320,200),
                     'ceil2':(560,80,680,160),'plank':(700,700,1000,755),
                     'tv':(160,300,500,460)}, S+'b_n.png')
run(S+'look_w.png', {'W_up':(480,270,660,450),'W_up2':(950,270,1080,450),
                     'W_low':(900,520,1030,620),'art':(100,320,430,450),
                     'rug':(150,790,700,845)}, S+'b_w.png')
run(S+'look_e.png', {'E_all':(200,270,900,470)}, S+'b_e.png')
run(S+'look_s.png', {'S_all':(200,270,900,470)}, S+'b_s.png')
