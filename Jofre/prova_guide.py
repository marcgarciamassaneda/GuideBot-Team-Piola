from guide import guide

src = (41.40674136015038, 2.1738860390977446)
dst = (41.4034789, 2.1744103330097055)

Barcelona = guide.load_graph("Barcelona")


route = guide.get_directions(Barcelona, src, dst)

guide.plot_directions(Barcelona, src, dst, route[1], "Barcelona")
