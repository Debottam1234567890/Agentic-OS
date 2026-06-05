# pyrefly: ignore [missing-import]
import plotext as plt

def plotter(X, Y, width=100, height=30):
    plt.clear_figure()
    
    # Force plotext to match the Textual widget dimensions exactly
    plt.plotsize(width, height)
    plt.theme('clear') # Removes blocky background colors
    plt.canvas_color('none') # Forces complete transparency on the chart canvas
    plt.axes_color('none') # Forces complete transparency behind the axes
    
    if Y[0] <= Y[-1]: # Newer price greater than older price
        color = "green"
    else:
        color = "red"
        
    plt.plot(Y, color=color, marker="braille") # Use braille dots for higher resolution
    plt.xticks([])
    plt.grid(False)
    ansi_string = plt.build()
    
    return ansi_string