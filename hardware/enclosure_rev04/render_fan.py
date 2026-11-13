# assembly picture with the fan: outside view + cut view (matplotlib, flat shaded, painter's sort)
import trimesh, numpy as np, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
parts = [('base.stl', (0.23, 0.49, 0.85), 1.0), ('REFERENCE_cm5_cooler_do_not_print.stl', (0.6, 0.62, 0.66), 1.0),
         ('lid.stl', (0.85, 0.55, 0.23), 0.9), ('REFERENCE_fan_4010_do_not_print.stl', (0.12, 0.12, 0.12), 1.0)]
L = np.array([0.4, -0.5, 0.75]); L /= np.linalg.norm(L)
def draw(ax, cut=None, elev=28, azim=-55):
    ax.computed_zorder = False
    for f, c, a in parts:
        m = trimesh.load(f)
        if cut is not None:
            m = m.slice_plane([0, cut, 0], [0, -1, 0], cap=False) if f != 'REFERENCE_fan_4010_do_not_print.stl' or True else m
        if len(m.faces) == 0: continue
        tri = m.vertices[m.faces]; sh = 0.35 + 0.65 * np.clip(m.face_normals @ L, 0, 1)
        pc = Poly3DCollection(tri, facecolors=np.c_[np.outer(sh, c), np.full(len(sh), a)], linewidths=0)
        pc.set_zorder(len(ax.collections)); ax.add_collection3d(pc)
    ax.set_xlim(-5, 60); ax.set_ylim(60, 125); ax.set_zlim(-5, 45); ax.set_box_aspect((65, 65, 50)); ax.view_init(elev, azim); ax.axis('off')
fig = plt.figure(figsize=(14, 7), dpi=110)
ax = fig.add_subplot(1, 2, 1, projection='3d'); draw(ax, elev=35, azim=-60); ax.set_title('Сборка: вентилятор 40x40x10 на крышке (чёрный)')
ax = fig.add_subplot(1, 2, 2, projection='3d'); draw(ax, cut=98.0, elev=8, azim=-90); ax.set_title('Разрез: вентилятор -> решётка -> радиатор CM5')
plt.tight_layout(); plt.savefig('assembly_with_fan.png')
