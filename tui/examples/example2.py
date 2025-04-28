from typing import Literal

from textual.app import App, ComposeResult, on
from textual.widgets import Input, Header, Footer, RichLog
from textual.screen import ModalScreen
from rich.panel import Panel
from rich.align import Align

class ChatScreen(ModalScreen):
    app: "Application"
    BINDINGS = [
        ("ctrl+s", "app.switch_mode('settings')", "Settings"),
    ]
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True, name="Logs")
        yield RichLog(markup=True, id="output")
        yield Input(placeholder="Type a log message", id="input")
        yield Footer()

    async def write_log(self, message: str, title: str, side: Literal["left", "right"], colour: str):
        msg = Align(
            Panel(
                message,
                title=f"[{colour}]{title}[/]",
                title_align=side,
                width=max(self.app.console.width // 3, 80)
            ),
            side
        )
        self.query_one(RichLog).write(msg, expand=True)

    @on(Input.Submitted)
    async def submit_handler(self, event: Input.Submitted) -> None:
        await self.write_log(event.value, "Message", "left", "green")
        self.query_one("#input", Input).clear()
        await self.write_log("A response", "Response", "right", "blue")


class SettingsScreen(ModalScreen):
    app: "Application"
    BINDINGS = [
        ("escape", "app.switch_mode('chat')", "Logs"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Input(value=self.app.config_setting, id="input")
        yield Footer()

    @on(Input.Submitted)
    async def submit_handler(self, event: Input.Submitted) -> None:
        self.app.config_setting = event.value
        self.app.pop_screen()

class Application(App):
    MODES = {"chat": ChatScreen, "settings": SettingsScreen}

    def __init__(self, config_setting="Default Setting"):
        self.config_setting = config_setting
        super().__init__()

    async def on_mount(self) -> None:
        await self.switch_mode("chat")


def main() -> None:
    app = Application()
    app.run()

if __name__ == "__main__":
    main()
