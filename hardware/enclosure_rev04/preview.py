# renders preview PNGs of base / lid / assembly (matplotlib, flat shaded)
import trimesh, numpy as np, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
def show(ax, f, color, elev, azim, alpha=1.0):
    m = trimesh.load(f); tri = m.vertices[m.faces]
    n = m.face_normals; L = np.array([0.4, -0.5, 0.75]); L /= np.linalg.norm(L)
    sh = 0.35 + 0.65 * np.clip(n @ L, 0, 1)
    col = np.outer(sh, color); pc = Poly3DCollection(tri, facecolors=np.c_[col, np.full(len(col), alpha)], linewidths=0)
    ax.add_collection3d(pc); ax.view_init(elev, azim)
    ax.set_xlim(-5, 50); ax.set_ylim(-5, 145); ax.set_zlim(-30, 60); ax.set_box_aspect((55, 150, 90)); ax.axis('off')
fig = plt.figure(figsize=(14, 7), dpi=110)
for i, (f, c, el, az, t) in enumerate([('base.stl', (0.3, 0.55, 0.85), 35, -60, 'base'), ('lid.stl', (0.85, 0.55, 0.25), -35, -60, 'lid (from below)'), ('assembly_preview.stl', (0.6, 0.6, 0.62), 30, 30, 'assembly')]):
    ax = fig.add_subplot(1, 3, i + 1, projection='3d'); show(ax, f, c, el, az); ax.set_title(t)
plt.tight_layout(); plt.savefig('enclosure_preview.png')
