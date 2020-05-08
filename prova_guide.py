from guide import guide
import osmnx
print(osmnx.geo_utils.geocode("Sagrada Família"))

src = (41.40674136015038, 2.1738860390977446)
dst = (41.4034789, 2.1744103330097055)
Barcelona = guide.load_graph("Barcelona")
'''ruta = guide.get_directions(Barcelona, src, dst)
print(ruta)
guide.plot_directions(Barcelona, src, dst, ruta, "ruta.png")'''
