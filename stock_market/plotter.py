import plotext as plt
def plotter(X, Y, width=100, height=30):
    plt.clear_figure()
    plt.plotsize(width, height)
    plt.theme('clear')
    plt.canvas_color('none')
    plt.axes_color('none')
    if Y[0] <= Y[-1]:
        color = 'green'
    else:
        color = 'red'
    plt.plot(Y, color=color, marker='braille')
    plt.xticks([])
    plt.grid(False)
    ansi_string = plt.build()
    return ansi_string
