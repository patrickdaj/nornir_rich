from typing import List, Any
import logging
import threading
import datetime
import time
import pprint

from nornir.core.inventory import Host, Inventory
from nornir.core.task import AggregatedResult, MultiResult, Task, Result

from rich.console import Console
from rich.theme import Theme
from rich.table import Table
from rich.box import ROUNDED
from rich.progress import Progress, BarColumn
from rich.text import Text

from .progress_bar import TimeElapsedColumn
from .custom_theme import CustomTheme


class RichResults:
    """
    rich implementation of the Processor interface.
    This plugin gets called when certain events happen by `nornir`.
    """

    def __init__(
        self,
        severity_level: int = logging.INFO,
        record: bool = True,
        display_params: bool = False,
        theme: Theme = CustomTheme,
        width: int = 0,
        timing: bool = True,
        progress_bar: bool = True,
        show_skipped=True,
        attrib_highlight: bool = False,  # TODO - customize as its kinda ugly by default
        vars: List[str] = ["stdout", "diff", "result"],
    ) -> None:
        """Creates a RichResult object to be set as nornir processor

        Args:
            severity_level (int, optional): Severity level of task. Defaults to logging.INFO.
            record (bool, optional): Allows record to write results. Defaults to True.
            display_params (bool, optional): Displays task params. Defaults to True.
            theme (Theme, optional): `Theme` to use for output. Defaults to default_theme.
            width (int, optional): Width of standard output minus log and timing. Defaults to 80.
            timing (bool, optional): Include timing info. Defaults to True.
            progress_bar (bool, optional): Include progress bar. Defaults to True.
            show_skipped (bool, optional): Display details of skipped hosts. Defaults to True.
            attrib_highlight (bool, optional): Use rich hightlighting on result attributes.  Defaults to False.
            vars (list, optional): Define what attributes of result to show.  Defaults to ['stdout', 'diff', 'result']
        """
        self.severity_level = severity_level
        self.lock = threading.Lock()
        self.console = Console(theme=theme, record=True)
        self.results: List[AggregatedResult] = []
        self.record = record
        self.width = width or self.console.width
        self.timing = timing
        self.progress_bar = progress_bar
        self.attrib_highlight = attrib_highlight
        self.vars = vars
        self.display_params = display_params
        self.show_skipped = show_skipped

    def task_started(self, task: Task) -> None:
        """
        This method is called right before starting the task
        """

        if task.severity_level < self.severity_level:
            return

        if self.progress_bar:
            self.progress = Progress(
                "[progress.description]{task.description}",
                BarColumn(bar_width=self.width - len(task.name) - 23),
                "[progress.percentage]{task.percentage:>3.0f}%",
                TimeElapsedColumn(),
                auto_refresh=True,
            )
            self.progress_id = self.progress.add_task(f"{task.name}", total=1)
            self.progress.start()

        if self.timing:
            task.start_time = time.time()

    def task_completed(self, task: Task, result: AggregatedResult) -> None:
        """
        This method is called when all the hosts have completed executing
        their respective task
        """
        if task.severity_level < self.severity_level:
            return

        if self.progress_bar:
            if not result.failed and len(result) > 0:
                self.progress.advance(self.progress_id)
            self.progress.stop()

        if self.timing:
            task.end_time = time.time()
            task.run_time = task.end_time - task.start_time
            result.task = task

        self.results.append(result)
        self.lock.acquire()
        self._print_result(result)
        self.lock.release()

    def task_instance_started(self, task: Task, host: Host) -> None:
        """
        This method is called before a host starts executing its instance of
        the task
        """
        if self.timing:
            task.start_time = time.time()

        if self.progress_bar:
            self.progress.tasks[0].total += 1

    def task_instance_completed(
        self, task: Task, host: Host, result: MultiResult
    ) -> None:
        """
        This method is called when a host completes its instance of a task
        """
        if self.progress_bar:
            if not result.failed:
                self.progress.advance(self.progress_id)

        if self.timing:
            task.end_time = time.time()
            task.run_time = task.end_time - task.start_time
            result[0].task = task

    def subtask_instance_started(self, task: Task, host: Host) -> None:
        """
        This method is called before a host starts executing a subtask
        """
        if self.timing:
            task.start_time = time.time()

        if self.progress_bar:
            self.progress.tasks[0].total += 1

    def subtask_instance_completed(
        self, task: Task, host: Host, result: MultiResult
    ) -> None:
        """
        This method is called when a host completes executing a subtask
        """
        if self.progress_bar:
            if not result.failed:
                self.progress.advance(self.progress_id)

        if self.timing:
            task.end_time = time.time()
            task.run_time = task.end_time - task.start_time
            result[0].task = task

    def _print_result(self, result: Result) -> None:

        if isinstance(result, AggregatedResult):
            if not self.progress_bar:
                msg = f"{result.name}"
                self.console.print(f"{msg}{'*' * (self.width - len(msg))}")

            hosts_set = set(result.task.nornir.inventory.hosts)
            skipped = result.task.nornir.data.failed_hosts | hosts_set 
            
            for skipped_host in skipped:
                if skipped_host not in result:
                    msg = f"* {skipped} ** skipped "
                    self.console.print(
                        f"{msg}{'*' * (self.width - len(msg))}",
                        style='skipped'
                    )

            for host, host_data in sorted(result.items()):
                msg = f"* {host} ** changed = {host_data.changed} "

                self.console.print(
                    f"{msg}{'*' * (self.width - len(msg))}",
                    style="host",
                )
                self._print_result(host_data)

        elif isinstance(result, MultiResult):
            self._print_individual_result(result[0], group=True)

            for r in result[1:]:
                self._print_result(r)

            msg = f"{'^' * 4} END {result[0].name} "
            self.console.print(
                f"{msg}{'^' * (self.width - len(msg))}",
                style=self._get_status(result[0]),
            )

        elif isinstance(result, Result):
            self._print_individual_result(result)

    def _print_individual_result(self, result: Result, group: bool = False) -> None:
        symbol = "v" if group else "-"
        msg = f"{symbol * 4} {result.name} ** changed = {result.changed} "
        level_name = logging.getLevelName(result.severity_level)

        if self.timing and getattr(result, "task", None):
            post = (
                f" {level_name} [{datetime.timedelta(seconds = result.task.run_time)}]"
            )
        else:
            post = f" {level_name}"

        self.console.print(
            f"{msg}{symbol * (self.width - len(msg) - len(post))}{post}",
            highlight=False,
            markup=False,
            style=self._get_status(result),
        )

        if self.display_params:
            task = result.task.task.__name__
            msg = f"{'!' * 4} task={task} args={result.task.params} "
            self.console.print(
                f"{msg}{'!' * (self.width - len(msg))}",
                highlight=False,
                markup=False,
                style="params",
            )

        for attr in ["stdout", "result", "stderr", "diff"]:
            x = getattr(result, attr, None)

            if x:
                self.console.print(x, highlight=self.attrib_highlight)

    def _get_status(self, result: Result) -> str:
        if result.failed:
            return "failed"
        elif result.changed:
            return "changed"
        else:
            return "ok"

    def write_summary(self) -> None:
        table = Table(
            expand=True,
            show_lines=False,
            box=ROUNDED,
            show_footer=True,
            width=self.width,
        )

        table.add_column("Task", ratio=5, no_wrap=True, footer="Total")
        table.add_column("Ok", ratio=1)
        table.add_column("Changed", ratio=1)
        table.add_column("Failed", ratio=1)

        totals = {"ok": 0, "failed": 0, "changed": 0}
        for result in self.results:
            failed = ok = changed = 0

            for host_data in result.values():
                failed += len(list(filter(lambda x: x.failed, host_data)))
                changed += len(list(filter(lambda x: x.changed, host_data)))
                ok += len(
                    list(filter(lambda x: not x.changed and not x.failed, host_data))
                )

            table.add_row(
                result.name,
                self._get_summary_count(ok, "ok"),
                self._get_summary_count(changed, "changed"),
                self._get_summary_count(failed, "failed"),
            )
            totals["ok"] += ok
            totals["changed"] += changed
            totals["failed"] += failed

        table.columns[1].footer = self._get_summary_count(totals["ok"], "ok")
        table.columns[2].footer = self._get_summary_count(totals["changed"], "changed")
        table.columns[3].footer = self._get_summary_count(totals["failed"], "failed")

        self.lock.acquire()
        self.console.print(table, width=self.width)
        self.lock.release()

    def _get_summary_count(self, count: int, style: str) -> Text:
        text = str(count) if count else "-"
        style = style if count else "no_style"
        return Text(text, style=style)

    def write_results(
        self, filename: str = "results.html", format: str = "html"
    ) -> None:
        self.lock.acquire()
        if format == "text":
            self.console.save_text(filename)
        else:
            self.console.save_html(filename)
        self.lock.release()

    def write_inventory(self, nr: Inventory, passwords: bool = False) -> None:
        table = Table(expand=True, box=ROUNDED, show_lines=True, width=self.width,)

        table.add_column("Host")
        table.add_column("Data")

        for host, host_data in nr.inventory.hosts.items():
            host_dict = host_data.dict()
            if not passwords:
                host_dict["password"] = "******"

            table.add_row(host, pprint.pformat(host_dict))

        self.lock.acquire()
        self.console.print(table, width=self.width)
        self.lock.release()
