import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from stock_market.fetcher import fetcher
import pandas as pd

def launch_stock_window(ticker):
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.canvas.manager.set_window_title(f"{ticker} - Agentic OS Market Data")
    plt.subplots_adjust(bottom=0.2) # Make room for buttons

    def draw_chart(period):
        ax.clear()
        ax.set_title(f"Loading {period} data for {ticker}...", color='white')
        fig.canvas.draw_idle()
        fig.canvas.flush_events()
        
        data = fetcher(ticker, period)
        ax.clear()
        
        if "error" in data:
            ax.text(0.5, 0.5, data["error"], ha="center", va="center", color="red", fontsize=14)
        else:
            X = data["x_axis"]
            Y = data["y_axis"]
            
            color = "#00ff00" if data["percent_change"] >= 0 else "#ff4444"
            fill_color = "#00ff0020" if data["percent_change"] >= 0 else "#ff444420"
            sign = "+" if data["percent_change"] >= 0 else ""
            title = f"{ticker} - ${round(data['current_price'], 2)} ({sign}{data['percent_change']}%)"
            
            ax.plot(X, Y, color=color, linewidth=2)
            ax.fill_between(X, Y, min(Y), color=fill_color)
            ax.set_title(title, fontsize=16, pad=15, color=color)
            ax.grid(True, alpha=0.15, color='#444444')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_color('#555555')
            ax.spines['left'].set_color('#555555')
            ax.tick_params(colors='#888888')
            
            fig.autofmt_xdate()
            
        fig.canvas.draw_idle()

    # Style the buttons
    ax_1d = plt.axes([0.2, 0.05, 0.1, 0.075])
    ax_5d = plt.axes([0.35, 0.05, 0.1, 0.075])
    ax_1mo = plt.axes([0.5, 0.05, 0.1, 0.075])
    ax_1y = plt.axes([0.65, 0.05, 0.1, 0.075])

    b_1d = Button(ax_1d, '1 Day', color='#333333', hovercolor='#555555')
    b_5d = Button(ax_5d, '1 Week', color='#333333', hovercolor='#555555')
    b_1mo = Button(ax_1mo, '1 Month', color='#333333', hovercolor='#555555')
    b_1y = Button(ax_1y, '1 Year', color='#333333', hovercolor='#555555')

    # Keep references to the buttons so they don't get garbage collected!
    fig.buttons = [b_1d, b_5d, b_1mo, b_1y]

    b_1d.on_clicked(lambda event: draw_chart("1d"))
    b_5d.on_clicked(lambda event: draw_chart("5d"))
    b_1mo.on_clicked(lambda event: draw_chart("1mo"))
    b_1y.on_clicked(lambda event: draw_chart("1y"))

    draw_chart("1d")
    plt.show(block=True)
