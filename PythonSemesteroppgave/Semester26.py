import math
import sys
import ctypes
import tkinter as tk
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import RadioButtons, Button
from matplotlib.patches import FancyBboxPatch, Circle
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib.colors import to_rgb
from matplotlib.transforms import Affine2D
import matplotlib.image as mpimg
from Semester26_Model import predict_price

MAP_FILE = 'Semester26_Bergen_kart.jpg'
LOGO_FILE = 'Semester26_Logo.png'
ICON_FILE = 'Semester26_Ikon.png'
SUN_FILE = 'Semester26_Sol.png'
MOON_FILE = 'Semester26_Maane.png'
MAP_EXTENT = (546060.5, 676038.0, 8443625.0, 8522539.9)
MERC_TO_MODEL = [[0.001804877605, -0.0001861719251],
                 [0.0002655721006, 0.001261065026],
                 [-3282.516912, -10533.85722]]

def merc_to_model(mx, my):
    (a, b), (c, d), (e, f) = MERC_TO_MODEL
    return a * mx + c * my + e, b * mx + d * my + f

(_a, _b), (_c, _d), _ = MERC_TO_MODEL
VIEW_ANGLE = math.atan2(-_b, _d)
VIEW_CENTER = ((MAP_EXTENT[0] + MAP_EXTENT[1]) / 2, (MAP_EXTENT[2] + MAP_EXTENT[3]) / 2)
VIEW_W, VIEW_H = MAP_EXTENT[1] - MAP_EXTENT[0], MAP_EXTENT[3] - MAP_EXTENT[2]
VIEW_EXTENT = (-VIEW_W / 2, VIEW_W / 2, -VIEW_H / 2, VIEW_H / 2)

def merc_to_view(mx, my):
    dx, dy = mx - VIEW_CENTER[0], my - VIEW_CENTER[1]
    cos, sin = math.cos(VIEW_ANGLE), math.sin(VIEW_ANGLE)
    return cos * dx + sin * dy, -sin * dx + cos * dy

def view_to_merc(vx, vy):
    cos, sin = math.cos(VIEW_ANGLE), math.sin(VIEW_ANGLE)
    return VIEW_CENTER[0] + cos * vx - sin * vy, VIEW_CENTER[1] + sin * vx + cos * vy

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
    vx, vy = merc_to_view(mx, my)
    marker.set_offsets([[vx, vy]])
    halo.center = (vx, vy)
    popup.xy = (vx, vy)

    house_name = [k for k, v in house_types.items() if v == house_type][0]
    standard_name = [k for k, v in standard_types.items() if v == standard_type][0]
    txt_choice.set_text(f"{house_name} · {standard_name} standard · {m2} m²")
    txt_total_label.set_text(f"Totalpris ({m2} m²)")
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

    price_m2 = [predict_price(x, y, _m2, house_type, standard_type) / _m2 * 1000 for _m2 in m2list]
    colors = [theme['accent'] if _m2 == m2 else theme['accent_soft'] for _m2 in m2list]
    bars = ax_bars.bar([f"{_m2} m²" for _m2 in m2list], price_m2, color=colors, width=0.55)
    ax_bars.bar_label(bars, labels=[f"{p / 1000:.0f}k" for p in price_m2], fontsize=9, color=theme['text'], padding=3)
    ax_bars.set_ylim(0, max(price_m2) * 1.2)
    style_bars()
    fig.canvas.draw_idle()

def style_bars():
    ax_bars.set_facecolor(theme['surface'])
    ax_bars.set_yticks([])
    ax_bars.tick_params(axis='x', length=0, labelsize=9, colors=theme['muted'])
    for side in ('top', 'right', 'left'):
        ax_bars.spines[side].set_visible(False)
    ax_bars.spines['bottom'].set_color(theme['line'])

def on_click_map(event):
    global marked_point
    if event.inaxes != ax_map:
        return
    fx, fy = fig.transFigure.inverted().transform((event.x, event.y))
    if L <= fx <= L + W and B <= fy <= B + H:
        return
    marked_point = view_to_merc(event.xdata, event.ydata)
    draw_the_map()

def on_click_bars(event):
    global m2
    if event.inaxes != ax_bars or event.xdata is None:
        return
    index = round(event.xdata)
    if 0 <= index < len(m2list):
        m2 = m2list[index]
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
m2list = [50, 100, 150, 200]
marked_point = lat_lon_to_merc(60.39253, 5.32337)

THEMES = {
    'light': {'surface': '#ffffff', 'text': '#1f2933', 'muted': '#7b8794', 'line': '#e4e7eb',
              'border': '#d0d5db', 'accent': '#1e9bf0', 'accent_soft': '#c9e6fc', 'hover': '#f0f2f5',
              'veil': (1, 1, 1), 'dim_inside': 0.0, 'dim_outside': 0.6, 'shadow': 0.08},
    'dark': {'surface': '#1f2630', 'text': '#e6e9ee', 'muted': '#9aa5b1', 'line': '#323b47',
             'border': '#3a4452', 'accent': '#3aa8f5', 'accent_soft': '#2b4560', 'hover': '#2a323d',
             'veil': (0, 0, 0), 'dim_inside': 0.12, 'dim_outside': 0.6, 'shadow': 0.35},
}
theme_name = 'light'
theme = THEMES[theme_name]
themed = []

def themed_artist(artist, method, role):
    themed.append((artist, method, role))
    return artist

plt.rcParams['font.family'] = ['Segoe UI', 'DejaVu Sans']
plt.rcParams['toolbar'] = 'None'

if sys.platform == 'win32':
    
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('Semesteroppgave.BoligpriserBergen')

fig = plt.figure(figsize=(12.0, 7.3))
fig.canvas.manager.set_window_title("Boligpriser Bergen")
window = getattr(fig.canvas.manager, 'window', None)
if isinstance(window, tk.Tk):
    app_icon = tk.PhotoImage(master=window, file=ICON_FILE)
    app_icon_small = app_icon.subsample(8)
    window.iconphoto(False, app_icon, app_icon_small)

ax_map = fig.add_axes((0, 0, 1, 1))
img = mpimg.imread(MAP_FILE)
map_rotation = Affine2D().translate(-VIEW_CENTER[0], -VIEW_CENTER[1]).rotate(-VIEW_ANGLE)
ax_map.imshow(img, extent=MAP_EXTENT, interpolation='antialiased', transform=map_rotation + ax_map.transData)
ax_map.set_xticks([])
ax_map.set_yticks([])
for spine in ax_map.spines.values():
    spine.set_visible(False)
themed_artist(ax_map, 'set_facecolor', 'surface')

gx, gy = np.meshgrid(np.linspace(VIEW_EXTENT[0], VIEW_EXTENT[1], 900),
                     np.linspace(VIEW_EXTENT[2], VIEW_EXTENT[3], 550))
grid_mx, grid_my = view_to_merc(gx, gy)
model_x, model_y = merc_to_model(grid_mx, grid_my)
outside_model = ~is_inside_model_grid(model_x, model_y)
map_margin = np.minimum.reduce([grid_mx - MAP_EXTENT[0], MAP_EXTENT[1] - grid_mx,
                                grid_my - MAP_EXTENT[2], MAP_EXTENT[3] - grid_my])
zone_without_map = ~outside_model & (map_margin < 0)
if (zone_without_map & (gy < 0)).any():
    outside_model |= gy <= gy[zone_without_map & (gy < 0)].max()
if (zone_without_map & (gy > 0)).any():
    outside_model |= gy >= gy[zone_without_map & (gy > 0)].min()
veil = np.ones((*gx.shape, 4))
veil_image = ax_map.imshow(veil, extent=VIEW_EXTENT, origin='lower', interpolation='bilinear', zorder=1)

ZONE_FADE, MAP_EDGE_FADE = 18000, 6000
zone_u, zone_v = gx[~outside_model], gy[~outside_model]
dist_u = np.maximum(np.maximum(zone_u.min() - gx, gx - zone_u.max()), 0)
dist_v = np.maximum(np.maximum(zone_v.min() - gy, gy - zone_v.max()), 0)
edge_fade = np.maximum(np.clip(np.hypot(dist_u, dist_v) / ZONE_FADE, 0, 1),
                       1 - np.clip(map_margin / MAP_EDGE_FADE, 0, 1))
edge_fade[~outside_model] = 0
fade = np.ones((*gx.shape, 4))
fade_image = ax_map.imshow(fade, extent=VIEW_EXTENT, origin='lower', interpolation='bilinear', zorder=1)
TOP_BAR_Y = 0.935
fig_w, fig_h = fig.get_size_inches()
view_h = (zone_v.max() - zone_v.min()) / TOP_BAR_Y
view_w = view_h * fig_w / fig_h
zone_center_u = (zone_u.min() + zone_u.max()) / 2
zone_center_frac = (zone_center_u - VIEW_EXTENT[0]) / VIEW_W
ax_map.set_xlim(zone_center_u - zone_center_frac * view_w, zone_center_u + (1 - zone_center_frac) * view_w)
ax_map.set_ylim(zone_v.min(), zone_v.min() + view_h)
themed_artist(fig.text(0.006, 0.01, "© Kartverket", fontsize=7), 'set_color', 'muted')

halo = themed_artist(Circle(merc_to_view(*marked_point), 1800, alpha=0.15, lw=1, zorder=2), 'set_color', 'accent')
ax_map.add_patch(halo)
marker = themed_artist(ax_map.scatter(*merc_to_view(*marked_point), s=140, edgecolors='white', linewidths=2.5, zorder=3),
                       'set_facecolor', 'accent')
popup = ax_map.annotate("", merc_to_view(*marked_point), xytext=(24, -8), textcoords='offset points', va='top',
                        fontsize=11, zorder=4, linespacing=1.6, bbox=dict(boxstyle='round,pad=0.7', lw=1))
themed_artist(popup, 'set_color', 'text')
themed_artist(popup.get_bbox_patch(), 'set_facecolor', 'surface')
themed_artist(popup.get_bbox_patch(), 'set_edgecolor', 'border')

ax_top = fig.add_axes((0, 0.935, 1, 0.065))
ax_top.axis('off')
top_bar = ax_top.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle='square', ec='none', transform=ax_top.transAxes))
themed_artist(top_bar, 'set_facecolor', 'surface')
themed_artist(ax_top.plot([0, 1], [0, 0], lw=1, transform=ax_top.transAxes)[0], 'set_color', 'line')
ax_logo = fig.add_axes((0.017, 0.9613, 0.0249, 0.022))
ax_logo.imshow(mpimg.imread(LOGO_FILE), interpolation='antialiased')
ax_logo.axis('off')
themed_artist(ax_top.text(0.048, 0.5, "BOLIGPRISER BERGEN", fontsize=12, weight='bold', va='center',
                          transform=ax_top.transAxes), 'set_color', 'text')
themed_artist(ax_top.text(0.5, 0.5, "Klikk på kartet for å estimere boligpris", fontsize=10, ha='center', va='center',
                          transform=ax_top.transAxes), 'set_color', 'muted')

ax_theme = fig.add_axes((0.882, 0.948, 0.103, 0.04))
button_theme = Button(ax_theme, "")
button_theme.label.set_fontsize(9.5)
button_theme.label.set_position((0.6, 0.5))
theme_icons = {'light': mpimg.imread(MOON_FILE), 'dark': mpimg.imread(SUN_FILE)}
theme_icon = OffsetImage(theme_icons['light'], zoom=0.26)
ax_theme.add_artist(AnnotationBbox(theme_icon, (0.17, 0.5), xycoords='axes fraction', frameon=False))

def tint_icon(icon, color):
    tinted = np.zeros_like(icon)
    tinted[..., :3] = to_rgb(color)
    tinted[..., 3] = icon[..., 3]
    return tinted
for spine in ax_theme.spines.values():
    themed_artist(spine, 'set_edgecolor', 'border')

L, B, W, H = 0.725, 0.035, 0.255, 0.87
card_shadow = FancyBboxPatch((L + 0.002, B - 0.004), W, H, boxstyle='round,pad=0,rounding_size=0.01',
                             transform=fig.transFigure, fc='black', ec='none', zorder=5)
card = FancyBboxPatch((L, B), W, H, boxstyle='round,pad=0,rounding_size=0.01',
                      transform=fig.transFigure, lw=1, zorder=6)
fig.patches += [card_shadow, card]
themed_artist(card, 'set_facecolor', 'surface')
themed_artist(card, 'set_edgecolor', 'border')

def card_line(y):
    line = plt.Line2D([L, L + W], [y, y], lw=1, zorder=7)
    fig.add_artist(themed_artist(line, 'set_color', 'line'))

def card_text(x, y, s, role, **kwargs):
    return themed_artist(fig.text(x, y, s, zorder=7, **kwargs), 'set_color', role)

card_text(L + W / 2, 0.855, "Prisoversikt", 'text', ha='center', fontsize=13, weight='bold')
txt_price = card_text(L + W / 2, 0.78, "", 'accent', ha='center', fontsize=22, weight='bold')
txt_choice = card_text(L + W / 2, 0.75, "", 'muted', ha='center', fontsize=9)
card_line(0.73)
fig.text(L + 0.02, 0.70, "●", fontsize=9, color='#2ecc71', zorder=7)
txt_area = card_text(L + 0.037, 0.70, "", 'text', fontsize=10.5)
txt_coords = card_text(L + W - 0.02, 0.70, "", 'muted', ha='right', fontsize=9)
card_line(0.68)
txt_total_label = card_text(L + 0.02, 0.65, "", 'muted', fontsize=9.5)
txt_total = card_text(L + W - 0.02, 0.65, "", 'text', ha='right', fontsize=11.5, weight='bold')
card_line(0.63)
card_text(L + 0.02, 0.60, "Boligtype", 'muted', fontsize=9.5)
card_text(L + W / 2 + 0.01, 0.60, "Standard", 'muted', fontsize=9.5)

ax_radio_house_type = fig.add_axes((L + 0.01, 0.465, W / 2 - 0.01, 0.125))
ax_radio_standard = fig.add_axes((L + W / 2, 0.435, W / 2 - 0.01, 0.155))
for ax in (ax_radio_house_type, ax_radio_standard):
    ax.set_zorder(8)
    themed_artist(ax, 'set_facecolor', 'surface')
    for spine in ax.spines.values():
        spine.set_visible(False)

radio_button_category = RadioButtons(ax_radio_house_type, list(house_types.keys()),
                                     radio_props={'s': [80] * len(house_types), 'edgecolor': '#9aa5b1'})
radio_button_standard = RadioButtons(ax_radio_standard, list(standard_types.keys()),
                                     radio_props={'s': [80] * len(standard_types), 'edgecolor': '#9aa5b1'})
for radio in (radio_button_category, radio_button_standard):
    for label in radio.labels:
        label.set_fontsize(10)
        themed_artist(label, 'set_color', 'text')
radio_button_category.on_clicked(on_house_type)
radio_button_standard.on_clicked(on_standard)
card_line(0.425)

card_text(L + 0.02, 0.39, "Pris per m² etter størrelse (klikk for å velge)", 'muted', fontsize=9.5)
ax_bars = fig.add_axes((L + 0.02, 0.075, W - 0.04, 0.29))
ax_bars.set_zorder(8)

def apply_theme():
    for artist, method, role in themed:
        getattr(artist, method)(theme[role])
    fig.set_facecolor(theme['surface'])
    card_shadow.set_alpha(theme['shadow'])
    veil[..., :3] = theme['veil']
    veil[..., 3] = np.where(outside_model, theme['dim_outside'], theme['dim_inside'])
    veil_image.set_data(veil)
    fade[..., :3] = to_rgb(theme['surface'])
    fade[..., 3] = edge_fade
    fade_image.set_data(fade)
    for radio in (radio_button_category, radio_button_standard):
        radio.activecolor = theme['accent']
    button_theme.label.set_text("Lys modus" if theme_name == 'dark' else "Mørk modus")
    theme_icon.set_data(tint_icon(theme_icons[theme_name], theme['text']))
    button_theme.label.set_color(theme['text'])
    button_theme.color, button_theme.hovercolor = theme['surface'], theme['hover']
    ax_theme.set_facecolor(theme['surface'])
    draw_the_map()

def on_toggle_theme(event):
    global theme_name, theme
    theme_name = 'dark' if theme_name == 'light' else 'light'
    theme = THEMES[theme_name]
    apply_theme()

button_theme.on_clicked(on_toggle_theme)

apply_theme()
fig.canvas.mpl_connect('button_press_event', on_click_map)
fig.canvas.mpl_connect('button_press_event', on_click_bars)
plt.show()
