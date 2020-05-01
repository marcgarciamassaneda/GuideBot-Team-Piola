from guide import guide
src = (41.975741, 2.824696)
dst = (41.964138, 2.828515)
Girona = guide.load_graph("Girona")
ruta = guide.get_directions("Girona", src, dst)
guide.plot_directions("Girona", src, dst, ruta, "directions")
