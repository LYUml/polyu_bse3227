import fitz,collections
p=fitz.open(r"C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/project/adpi-manufacturer-study/GRD_Engineering.pdf")[10]
for i,d in enumerate(p.get_drawings()):
 r=d["rect"]
 if r.x0<=300 and r.x1>=90 and r.y0<=640 and r.y1>=548:print(i,"n",len(d["items"]),collections.Counter(v[0] for v in d["items"]),"rect",r,"width",d["width"])
