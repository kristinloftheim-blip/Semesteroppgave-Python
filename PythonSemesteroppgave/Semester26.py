import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import RadioButtons
from matplotlib.patches import FancyBboxPatch, Circle
import matplotlib.image as mpimg
from Semester26_Model import predict_price

MAP_FILE = 'Semester26_Bergen_kart.jpg'
MAP_EXTENT = (546060.5, 676038.0, 8443625.0, 8522539.9)
MERC_TO_MODEL = [[0.001804877605, -0.0001861719251],
                 [0.0002655721006, 0.001261065026],
                 [-3282.516912, -10533.85722]]

def merc_to_model(mx, my):
    (a, b), (c, d), (e, f) = MERC_TO_MODEL
    return a * mx + c * my + e, b * mx + d * my + f

def is_inside_model(x, y):
    return 0 <= x <= 100 and 4.8 <= y <= 100

def is_inside_model_grid(x, y):
    return (x >= 0) & (x <= 100) & (y >= 4.8) & (y <= 100)

def lat_lon_to_merc(lat, lon):
    r = 6378137.0
    return r * math.radians(lon), r * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))

places = pd.read_csv('Semester26_Steder.csv')
places_merc = [(row.navn, lat_lon_to_merc(row.lat, row.lon)) for row in places.itertuples()]

def nearest_place(mx, my):
    name, pos = min(places_merc, key=lambda place: math.dist(place[1], (mx, my)))
    return name

def fmt(value):
    return f"{value:,.0f}".replace(",", " ")

def draw_the_map():
    mx, my = marked_point
    x, y = merc_to_model(mx, my)
    marker.set_offsets([[mx, my]])
    halo.center = (mx, my)
    popup.xy = (mx, my)

    house_name = [k for k, v in house_types.items() if v == house_type][0]
    standard_name = [k for k, v in standard_types.items() if v == standard_type][0]
    txt_choice.set_text(f"{house_name} · {standard_name} standard · {m2} m²")
    txt_coords.set_text(f"x {x:.0f}, y {y:.0f}")
    print(f"marked_point: ({x:.1f}, {y:.1f})")

    ax_bars.cla()
    if not is_inside_model(x, y):
        popup.set_text("Utenfor området\nKlikk innenfor kartet")
        txt_price.set_text("–")
        txt_area.set_text("Utenfor modellområdet")
        txt_total.set_text("–")
        style_bars()
        fig.canvas.draw_idle()
        return

    kr_m2 = predict_price(x, y, m2, house_type, standard_type) / m2 * 1000
    area = nearest_place(mx, my)
    popup.set_text(f"{area}\n{fmt(round(kr_m2, -2))} kr/m²")
    txt_price.set_text(f"{fmt(round(kr_m2, -2))} kr/m²")
    txt_area.set_text(area)
    txt_total.set_text(f"{kr_m2 * m2 / 1e6:.1f}".replace(".", ",") + " mill. kr")

    m2list = [50, 100, 150, 200]
    price_m2 = [predict_price(x, y, _m2, house_type, standard_type) / _m2 * 1000 for _m2 in m2list]
    colors = [BLUE if _m2 == m2 else LIGHT_BLUE for _m2 in m2list]
    bars = ax_bars.bar([f"{_m2} m²" for _m2 in m2list], price_m2, color=colors, width=0.55)
    ax_bars.bar_label(bars, labels=[f"{p / 1000:.0f}k" for p in price_m2], fontsize=9, color=TEXT, padding=3)
    ax_bars.set_ylim(0, max(price_m2) * 1.2)
    style_bars()
    fig.canvas.draw_idle()

def style_bars():
    ax_bars.set_facecolor('white')
    ax_bars.set_yticks([])
    ax_bars.tick_params(axis='x', length=0, labelsize=9, colors=MUTED)
    for side in ('top', 'right', 'left'):
        ax_bars.spines[side].set_visible(False)
    ax_bars.spines['bottom'].set_color(LINE)

def on_click_map(event):
    global marked_point
    if event.inaxes != ax_map:
        return
    fx, fy = fig.transFigure.inverted().transform((event.x, event.y))
    if L <= fx <= L + W and B <= fy <= B + H:
        return
    marked_point = (event.xdata, event.ydata)
    draw_the_map()

def on_house_type(key):
    global house_type
    house_type = house_types[key]
    draw_the_map()

def on_standard(key):
    global standard_type
    standard_type = standard_types[key]
    draw_the_map()

house_types = {
    'Enebolig': 1,
    'Rekkehus': 2,
    'Leilighet': 3
}
standard_types = {
    'Dårlig': 1,
    'God': 2,
    'Meget god': 3,
    'Luksus': 4
}

house_type = 1
standard_type = 1
m2 = 100
marked_point = lat_lon_to_merc(60.39253, 5.32337)

BLUE, LIGHT_BLUE = '#1e9bf0', '#c9e6fc'
TEXT, MUTED, LINE, BORDER = '#1f2933', '#7b8794', '#e4e7eb', '#d0d5db'
plt.rcParams['font.family'] = ['Segoe UI', 'DejaVu Sans']
plt.rcParams['toolbar'] = 'None'

fig = plt.figure(figsize=(12.0, 7.3), facecolor='white')
fig.canvas.manager.set_window_title("Boligpriser Bergen")

ax_map = fig.add_axes((0, 0, 1, 1))
img = mpimg.imread(MAP_FILE)
ax_map.imshow(img, extent=MAP_EXTENT, interpolation='antialiased')
ax_map.axis('off')

gx, gy = np.meshgrid(np.linspace(MAP_EXTENT[0], MAP_EXTENT[1], 300),
                     np.linspace(MAP_EXTENT[2], MAP_EXTENT[3], 200))
model_x, model_y = merc_to_model(gx, gy)
veil = np.ones((*gx.shape, 4))
veil[..., 3] = ~is_inside_model_grid(model_x, model_y) * 0.6
ax_map.imshow(veil, extent=MAP_EXTENT, origin='lower', interpolation='bilinear', zorder=1)
ax_map.set_xlim(MAP_EXTENT[0], MAP_EXTENT[1])
ax_map.set_ylim(MAP_EXTENT[2], MAP_EXTENT[3])
fig.text(0.006, 0.01, "© Kartverket", fontsize=7, color=MUTED)

halo = Circle(marked_point, 1800, fc=BLUE, alpha=0.15, ec=BLUE, lw=1, zorder=2)
ax_map.add_patch(halo)
marker = ax_map.scatter(*marked_point, s=140, c=BLUE, edgecolors='white', linewidths=2.5, zorder=3)
popup = ax_map.annotate("", marked_point, xytext=(24, -8), textcoords='offset points', va='top',
                        fontsize=11, color=TEXT, zorder=4, linespacing=1.6,
                        bbox=dict(boxstyle='round,pad=0.7', fc='white', ec=BORDER, lw=1))

ax_top = fig.add_axes((0, 0.935, 1, 0.065))
ax_top.axis('off')
ax_top.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle='square', fc='white', ec='none', transform=ax_top.transAxes))
ax_top.plot([0, 1], [0, 0], color=LINE, lw=1, transform=ax_top.transAxes)
ax_top.text(0.018, 0.5, "⌂", fontsize=18, color=BLUE, va='center', transform=ax_top.transAxes)
ax_top.text(0.042, 0.5, "BOLIGPRISER BERGEN", fontsize=12, weight='bold', color=TEXT, va='center', transform=ax_top.transAxes)
ax_top.add_patch(FancyBboxPatch((0.33, 0.22), 0.34, 0.56, boxstyle='round,pad=0,rounding_size=0.12',
                                fc='#f5f7fa', ec=BORDER, lw=1, transform=ax_top.transAxes, mutation_aspect=0.25))
ax_top.text(0.345, 0.5, "Klikk på kartet for å estimere boligpris", fontsize=10, color=MUTED, va='center', transform=ax_top.transAxes)
ax_top.text(0.982, 0.5, "DAT · Semesteroppgave 2026", fontsize=9, color=MUTED, va='center', ha='right', transform=ax_top.transAxes)

L, B, W, H = 0.725, 0.035, 0.255, 0.87
fig.patches.append(FancyBboxPatch((L + 0.002, B - 0.004), W, H, boxstyle='round,pad=0,rounding_size=0.01',
                                  transform=fig.transFigure, fc='black', alpha=0.08, ec='none', zorder=5))
fig.patches.append(FancyBboxPatch((L, B), W, H, boxstyle='round,pad=0,rounding_size=0.01',
                                  transform=fig.transFigure, fc='white', ec=BORDER, lw=1, zorder=6))

def card_line(y):
    fig.add_artist(plt.Line2D([L, L + W], [y, y], color=LINE, lw=1, zorder=7))

def card_text(x, y, s, **kwargs):
    return fig.text(x, y, s, zorder=7, **kwargs)

card_text(L + W / 2, 0.855, "Prisoversikt", ha='center', fontsize=13, weight='bold', color=TEXT)
txt_price = card_text(L + W / 2, 0.78, "", ha='center', fontsize=22, weight='bold', color=BLUE)
txt_choice = card_text(L + W / 2, 0.75, "", ha='center', fontsize=9, color=MUTED)
card_line(0.73)
card_text(L + 0.02, 0.70, "●", fontsize=9, color='#2ecc71')
txt_area = card_text(L + 0.037, 0.70, "", fontsize=10.5, color=TEXT)
txt_coords = card_text(L + W - 0.02, 0.70, "", ha='right', fontsize=9, color=MUTED)
card_line(0.68)
card_text(L + 0.02, 0.65, "Totalpris", fontsize=9.5, color=MUTED)
txt_total = card_text(L + W - 0.02, 0.65, "", ha='right', fontsize=11.5, weight='bold', color=TEXT)
card_line(0.63)
card_text(L + 0.02, 0.60, "Boligtype", fontsize=9.5, color=MUTED)
card_text(L + W / 2 + 0.01, 0.60, "Standard", fontsize=9.5, color=MUTED)

ax_radio_house_type = fig.add_axes((L + 0.01, 0.465, W / 2 - 0.01, 0.125))
ax_radio_standard = fig.add_axes((L + W / 2, 0.435, W / 2 - 0.01, 0.155))
for ax in (ax_radio_house_type, ax_radio_standard):
    ax.set_zorder(8)
    ax.set_facecolor('white')
    for spine in ax.spines.values():
        spine.set_visible(False)

radio_button_category = RadioButtons(ax_radio_house_type, list(house_types.keys()), activecolor=BLUE,
                                     radio_props={'s': [80] * len(house_types), 'edgecolor': '#9aa5b1'})
radio_button_standard = RadioButtons(ax_radio_standard, list(standard_types.keys()), activecolor=BLUE,
                                     radio_props={'s': [80] * len(standard_types), 'edgecolor': '#9aa5b1'})
for radio in (radio_button_category, radio_button_standard):
    for label in radio.labels:
        label.set_fontsize(10)
        label.set_color(TEXT)
radio_button_category.on_clicked(on_house_type)
radio_button_standard.on_clicked(on_standard)
card_line(0.425)

card_text(L + 0.02, 0.39, "Pris per m² etter størrelse", fontsize=9.5, color=MUTED)
ax_bars = fig.add_axes((L + 0.02, 0.075, W - 0.04, 0.29))
ax_bars.set_zorder(8)

draw_the_map()
fig.canvas.mpl_connect('button_press_event', on_click_map)
plt.show()
