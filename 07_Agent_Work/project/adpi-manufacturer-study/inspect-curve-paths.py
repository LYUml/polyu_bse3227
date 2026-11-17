import fitz,json
p=fitz.open(r"C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/project/adpi-manufacturer-study/GRD_Engineering.pdf")[10]
for i,d in enumerate(p.get_drawings()):
 r=d["rect"]
 if r.x0>=85 and r.x1<=300 and r.y0>=548 and r.y1<=654 and any(v[0]=="c" for v in d["items"]):
  print(i,"width",d["width"],"type",d["type"],"rect",r,"items",str(d["items"]))
