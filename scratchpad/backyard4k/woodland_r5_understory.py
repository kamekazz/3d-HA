from pathlib import Path
p=Path('frontend/js/environment.js');s=p.read_text();s=s.replace('paintNoisy(bank,color(0x676c50),rng,.37)','paintNoisy(bank,color(0x48503b),rng,.37)',1);s=s.replace('if(rng()<.78) {\n        branch([[x,waterY,z]', 'if(rng()<.94) {\n        branch([[x,waterY,z]',1);s=s.replace('height*.5,1.8+rng(),360,farPos,farCol,1.5)', 'height*.5,1.8+rng(),1100,farPos,farCol,1.5)',1)
# Fill the woodland base with irregular young multi-stem growth between the
# tall tree ranks, avoiding a bare horizontal shelf under their crowns.
needle='    // Three unequal ranks overlap in depth: low pioneer trees on the bank,'
insert='''    for(let x=lakeX0;x<lakeX1;x+=4+rng()*5) {
      const z=far(x)-8-rng()*16,h=3+rng()*6;
      branch([[x,L.lo+1,z],[x-.3,L.lo+h*.6,z-1],[x+1,L.lo+h,z-.4]],.07,.01,masses);
      leafCloud(x,L.lo+h*.62,z,3.4+rng()*2,h*.6,3+rng()*2,1400,farPos,farCol,1.7);
    }
''' +needle
s=s.replace(needle,insert,1);p.write_text(s)
