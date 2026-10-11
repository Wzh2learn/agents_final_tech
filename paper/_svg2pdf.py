# -*- coding: utf-8 -*-
# Faithful re-render of the bound fig1 SVG to vector PDF + PNG via matplotlib.
import re, sys, xml.etree.ElementTree as ET
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, FancyBboxPatch
from matplotlib.lines import Line2D

SRC = sys.argv[1]; OUTPDF = sys.argv[2]; OUTPNG = sys.argv[3]

tree = ET.parse(SRC); root = tree.getroot()
def tag(e): return e.tag.split('}')[-1]
def f(e,n,d=None): return e.attrib.get(n, d)
def num(e,n,d=0.0):
    v = e.attrib.get(n); return float(v) if v is not None else d

W = float(root.attrib.get('width','1800')); H = float(root.attrib.get('height','700'))
dpi = 100.0
fig = plt.figure(figsize=(W/dpi, H/dpi), dpi=dpi)
ax = fig.add_axes([0,0,1,1]); ax.set_xlim(0,W); ax.set_ylim(H,0); ax.axis('off')
PX2PT = 72.0/dpi

def anchor_ha(a): return {'middle':'center','start':'left','end':'right'}.get(a,'left')

for e in root.iter():
    t = tag(e)
    if t == 'rect':
        x,y,w,h = num(e,'x'),num(e,'y'),num(e,'width'),num(e,'height')
        rx = num(e,'rx',0)
        fill = f(e,'fill'); stroke = f(e,'stroke'); sw = num(e,'stroke-width',0)
        dash = f(e,'stroke-dasharray')
        ls = '--' if dash else '-'
        if fill in (None,'none') and stroke in (None,'none'): continue
        if rx>0:
            p = FancyBboxPatch((x+rx, y+rx), max(w-2*rx,1), max(h-2*rx,1),
                               boxstyle="round,pad=%f,rounding_size=%f" % (rx, rx),
                               linewidth=(sw*PX2PT if sw else 0), edgecolor=(stroke if stroke else 'none'),
                               facecolor=(fill if fill not in (None,'none') else 'none'), mutation_aspect=1.0)
            ax.add_patch(p)
        else:
            ax.add_patch(Rectangle((x,y), w, h, linewidth=(sw*PX2PT if sw else 0),
                                   edgecolor=(stroke if stroke else 'none'),
                                   facecolor=(fill if fill not in (None,'none') else 'none'), linestyle=ls))
    elif t == 'line':
        ax.add_line(Line2D([num(e,'x1'),num(e,'x2')],[num(e,'y1'),num(e,'y2')],
                    color=f(e,'stroke','#000'), linewidth=num(e,'stroke-width',1)*PX2PT,
                    linestyle=('--' if f(e,'stroke-dasharray') else '-')))
    elif t == 'polygon':
        pts = [float(v) for v in re.split(r'[ ,]+', f(e,'points','').strip()) if v]
        xy = list(zip(pts[0::2], pts[1::2]))
        ax.add_patch(Polygon(xy, closed=True, linewidth=num(e,'stroke-width',0)*PX2PT,
                             edgecolor=f(e,'stroke','none'), facecolor=f(e,'fill','none')))
    elif t == 'text':
        s = (e.text or '')
        if not s.strip(): continue
        fs = num(e,'font-size',20); wt = f(e,'font-weight','400')
        ax.text(num(e,'x'), num(e,'y'), s, fontsize=fs*PX2PT, color=f(e,'fill','#000'),
                ha=anchor_ha(f(e,'text-anchor','start')), va='baseline',
                fontweight=('bold' if wt in ('700','bold') else 'normal'), family='DejaVu Sans')

fig.savefig(OUTPDF, format='pdf')
fig.savefig(OUTPNG, format='png', dpi=200)
print("wrote", OUTPDF, OUTPNG)