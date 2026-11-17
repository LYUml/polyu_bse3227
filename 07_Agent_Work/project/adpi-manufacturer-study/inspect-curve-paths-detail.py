import fitz
p=fitz.open(r"C:/Users/lyuml-win/Desktop/polyu_bse3227/07_Agent_Work/project/adpi-manufacturer-study/GRD_Engineering.pdf")[10]
for i,d in enumerate(p.get_drawings()):
 items=[v for v in d["items"] if v[0]=="c" and all(85<=pt.x<=300 and 540<=pt.y<=654 for pt in v[1:])]
 if items:print(i,"width",d["width"],"rect",d["rect"],"n",len(items),str(items)[:4000])
