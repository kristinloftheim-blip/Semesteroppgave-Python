# importing modules and packages
import matplotlib.pyplot as plt
from matplotlib.widgets import RadioButtons
import matplotlib.image as mpimg
from Semester26_Model import  predict_price

def draw_the_map():
    ax_map.cla()
    ax_map.imshow(img, extent=(0, 100, 0, 100), aspect='auto')
    x,y = marked_point
    ax_map.scatter(x, y, marker='+', c='blue', s=200)
    print(f"marked_point: {marked_point}")
    if marked_point == (0, 0):
        return

    m2_price:float = predict_price(x, y, m2, house_type, standard_type) / m2
    price = f"{round(m2_price * 1000, -2):,.0f}"

    m2list = [50,100,150,200]
    price_m2 = [predict_price(x, y,  _m2, house_type, standard_type)/_m2 for _m2 in m2list]

    ax_map.text(x + 3, y - 1, price, color='blue', fontsize=15)
    ax_history.cla()
    ax_history.bar(m2list, price_m2, color='blue', width=5)
    ax_history.legend(["pris per m2"])

    plt.draw()

def on_click_map(event) :
    global marked_point
    if event.inaxes != ax_map:
        return
    marked_point = (event.xdata, event.ydata)
    draw_the_map()
    return

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
    'Rekke': 2,
    'Leilighet': 3
}
standard_types = {
    'Dårlig': 1,
    'God': 2,
    'Meget God': 3,
    'Luksus': 4
}

house_type = 1
standard_type = 1
m2 = 100
marked_point = (43,57)

# Create the figures
fig = plt.figure(figsize=(8.0, 8.0),facecolor='lightgray')  # type: ignore[arg-type]
fig.suptitle("Hus priser Bergen (per m2)", fontsize=20, y=0.95)

ax_map = fig.add_axes((0.4, 0.05, 0.50, .85))
ax_radio_house_type = fig.add_axes((0.05, 0.75, 0.30, .15))
ax_radio_standard = fig.add_axes((0.05, 0.57, 0.30, .15))
ax_history = fig.add_axes((0.05, 0.05, 0.30, .50))
ax_radio_house_type.set_facecolor('lightgray')
ax_radio_standard.set_facecolor('lightgray')

radio_button_category = RadioButtons(ax_radio_house_type, list(house_types.keys()))
radio_button_standard = RadioButtons(ax_radio_standard, list(standard_types.keys()))
radio_button_category.on_clicked(on_house_type)
radio_button_standard.on_clicked(on_standard)

fig.subplots_adjust(left=0, right=1, top=1, bottom=0) # Adjust the figure to fit the image
ax_map.margins(x=0.01, y=0.01)  # Adjust x and y margins
img = mpimg.imread('Semester26_Bergen.jpg')
ax_map.imshow(img, aspect='auto')

draw_the_map()
plt.connect('button_press_event', on_click_map)
plt.show()


