from rich.progress import ProgressColumn, Text
import datetime

class TimeElapsedColumn(ProgressColumn):
    """Renders elapsed time."""

    # Only refresh twice a second to prevent jitter
    max_refresh = 0.5

    def render(self, task: "Task") -> Text:
        """Show time elapsed."""
        elapsed = task._get_time() - task.start_time
        elapsed_delta = datetime.timedelta(seconds=elapsed)
        return Text(f"[{datetime.timedelta(seconds=elapsed)}]")