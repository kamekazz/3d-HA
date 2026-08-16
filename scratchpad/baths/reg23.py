import sys
sys.argv=[0]
exec(open("planreg.py").read().split('if __name__')[0])
main(r"C:\Users\Manuel\Desktop\Pro\3d HA\docs\floor plan\Main Floor Plan App.png",
     "reg23.png",
     900.6, -21.73, 1340.6, -22.91,
     [("BATH23", 18.7, 28.6, -4.3, 3.1, (220,0,0)),
      ("LIV5", -1.9, 18.6, -12.4, 4.6, (0,150,0)),
      ("OFF8", 28.8, 39.4, -4.5, 7.1, (0,0,220)),
      ("GAR7", 18.9, 39.3, 13.0, 34.7, (160,0,160)),
      ("KIT6", -4.2, 10.7, 4.7, 21.5, (0,150,150))],
     (200, 1180, 620, 1520), 3)
