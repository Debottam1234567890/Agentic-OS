from textual.screen import Screen
from textual.widgets import Static, Tabs, Tab, Footer
from textual import work, on
from stock_market.plotter import plotter
from stock_market.fetcher import fetcher
import shutil
class StockScreen(Screen):
    BINDINGS = [('escape', 'app.pop_screen', 'Back to OS')]
    def __init__(self, ticker):
        super().__init__()
        self.ticker = ticker
    def compose(self):
        yield Static(f'Loading {self.ticker}...', id='stock_ticker')
        yield Tabs(Tab('1 Day', id='tab_1d'), Tab('1 Week', id='tab_5d'), Tab('1 Month', id='tab_1mo'), Tab('1 Year', id='tab_1y'))
        yield Static('Initializing canvas...', id='stock_canvas')
        yield Footer()
    def on_mount(self) -> None:
        term_width, term_height = shutil.get_terminal_size()
        width = term_width - 6
        height = term_height - 12
        self.fetch_and_draw('1d', width, height)
    @on(Tabs.TabActivated)
    def handle_tab_activation(self, event: Tabs.TabActivated):
        period_map = {'tab_1d': '1d', 'tab_5d': '5d', 'tab_1mo': '1mo', 'tab_1y': '1y'}
        target_period = period_map.get(event.tab.id, '1d')
        term_width, term_height = shutil.get_terminal_size()
        width = term_width - 6
        height = term_height - 12
        self.fetch_and_draw(target_period, width, height)
    @work(thread=True)
    def fetch_and_draw(self, period: str, width: int, height: int):
        def set_loading():
            self.query_one('#stock_canvas', Static).update('\n[dim cyan]Fetching market data...[/dim cyan]')
        self.app.call_from_thread(set_loading)
        try:
            data = fetcher(self.ticker, period)
            if 'error' in data:
                ansi_chart = f"\n[red]{data['error']}[/red]"
                header_text = f'[bold]{self.ticker}[/bold] - ERROR'
            else:
                ansi_chart = plotter(data['x_axis'], data['y_axis'], width, height)
                color = 'green' if data['percent_change'] >= 0 else 'red'
                sign = '+' if data['percent_change'] >= 0 else ''
                header_text = f"[bold]{self.ticker}[/bold] - ${round(data['current_price'], 2)} ([{color}]{sign}{data['percent_change']}%[/{color}])"
            def update_ui():
                self.query_one('#stock_canvas', Static).update(ansi_chart)
                self.query_one('#stock_ticker', Static).update(header_text)
            self.app.call_from_thread(update_ui)
        except Exception as e:
            def show_error():
                self.query_one('#stock_canvas', Static).update(f'\n[red]Failed to load data: {str(e)}[/red]')
            self.app.call_from_thread(show_error)
