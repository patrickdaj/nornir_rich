from rich.progress import ProgressColumn, Text, Task
import datetime


class TimeElapsedColumn(ProgressColumn):
    """Renders elapsed time."""

    # Only refresh twice a second to prevent jitter
    max_refresh = 0.5

    def render(self, task: "Task") -> Text:
        """Render elapsed time

        Args:
            task (Task): progress bar task

        Returns:
            Text: timedelta between start and current time
        """
        elapsed = task._get_time() - task.start_time
        return Text(f"[{datetime.timedelta(seconds=elapsed)}]")

class TaskStatusColumn(ProgressColumn):

    max_refresh = 0.5

    def render(self, task: "Task") -> Text:
        """Render task status done/failed/total"""
        pass