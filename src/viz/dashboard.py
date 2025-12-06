from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Button, Static, Log, Label
from textual.reactive import reactive
import threading
import subprocess
import time
import os

class Dashboard(App):
    CSS = """
    Screen {
        layout: grid;
        grid-size: 2 2;
        grid-columns: 1fr 2fr;
        grid-rows: 1fr 3fr;
    }
    .box {
        height: 100%;
        border: solid green;
        padding: 1;
    }
    #status {
        background: $surface;
    }
    #controls {
        background: $surface;
    }
    #logs {
        column-span: 2;
        background: $surface-darken-1;
    }
    """

    status_text = reactive("System Idle")
    best_cost = reactive("N/A")

    def compose(self) -> ComposeResult:
        yield Header()
        
        with Container(id="status", classes="box"):
            yield Label("System Status")
            yield Static(id="status-display")
            yield Label("Best Cost (Sigma Pi)")
            yield Static(id="cost-display")

        with Container(id="controls", classes="box"):
            yield Label("Controls")
            yield Button("Start Optimization", id="btn-opt", variant="primary")
            yield Button("Launch Web Viz", id="btn-viz", variant="warning")
            yield Button("Stop", id="btn-stop", variant="error")

        with Container(id="logs", classes="box"):
            yield Label("System Logs")
            yield Log(id="log-view")

        yield Footer()

    def on_mount(self) -> None:
        self.set_interval(1, self.update_status)
        self.query_one("#status-display", Static).update(self.status_text)
        self.query_one("#cost-display", Static).update(self.best_cost)

    def update_status(self) -> None:
        # Update logs
        if os.path.exists("logs/optimizer.log"):
            with open("logs/optimizer.log", "r") as f:
                # Seek to end? No, just read last few lines for now
                lines = f.readlines()[-10:]
                log_view = self.query_one("#log-view", Log)
                log_view.clear()
                for line in lines:
                    log_view.write(line.strip())
                    if "Cost:" in line:
                        try:
                            parts = line.split("Cost: ")[1].split(",")
                            self.best_cost = parts[0]
                            self.query_one("#cost-display", Static).update(self.best_cost)
                        except:
                            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-opt":
            self.status_text = "Optimization Running..."
            self.query_one("#status-display", Static).update(self.status_text)
            threading.Thread(target=self.run_optimization).start()
        
        elif event.button.id == "btn-viz":
            self.status_text = "Web Server Running..."
            self.query_one("#status-display", Static).update(self.status_text)
            threading.Thread(target=self.run_web_server).start()

    def run_optimization(self):
        # Run the optimizer script
        # In a real app, we'd import and run, but capturing output is easier via subprocess for TUI log
        subprocess.run(["python3", "src/optimizer.py"])
        self.status_text = "Optimization Finished"
        self.query_one("#status-display", Static).update(self.status_text)

    def run_web_server(self):
        subprocess.run(["python3", "src/viz/server.py"])

if __name__ == "__main__":
    app = Dashboard()
    app.run()
