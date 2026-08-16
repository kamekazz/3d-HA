import sys
exec(open("planreg.py").read().split('if __name__')[0])
# second-floor plan: fit from the previous agent's derivation, refined below
main(r"C:\Users\Manuel\Desktop\Pro\3d HA\docs\floor plan\Second Floor Plan App.png",
     "reg26.png",
     977.8, -28.6, 1372.0, -27.4,
     [("R15rios", -2.0, 10.5, 22.7, 34.4, (0,150,0)),
      ("R26bath", 10.5, 18.6, 23.4, 32.1, (220,0,0)),
      ("R17hall", 10.5, 18.6, 6.6, 23.3, (0,0,220)),
      ("R16mb", 18.6, 33.4, -0.3, 12.4, (160,0,160))],
     (250, 380, 800, 800), 2)
