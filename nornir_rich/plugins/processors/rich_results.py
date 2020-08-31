from typing import List
import logging
import threading
import datetime
import sys
import os
import time
import json
from ruamel import yaml
import lxml.etree as etree

from nornir.core.inventory import Host, Inventory
from nornir.core.task import AggregatedResult, MultiResult, Task, Result

from rich.console import Console, OverflowMethod
from rich.theme import Theme
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.table import Table
from rich.box import ROUNDED
from rich.progress import Progress, BarColumn

from .default_theme import default_theme
from .progress_bar import TimeElapsedColumn


class RichResults:
    """
    This defines the Processor interface. A processor plugin needs to implement each method with the
    same exact signature. It's not necessary to subclass it.
    A processor is a plugin that gets called when certain events happen.
    """


    def __init__(
        self,
        severity_level: int = logging.INFO,
        record: bool = True,
        display_params: bool = False,
        theme: Theme = default_theme,
        width: int = 80,
        timing: bool = True
    ) -> None:
        self.severity_level = severity_level
        self.lock = threading.Lock()
        self.console = Console(theme=theme, record=True)
        self.results = []
        self.record = record
        self.width = width
        self.timing = timing


    def task_started(self, task: Task) -> None:
        """
        This method is called right before starting the task
        """

        if task.severity_level < self.severity_level:
            return

        self.progress = Progress(
            "[progress.description]{task.description}",
            BarColumn(bar_width=self.width - len(task.name) - 6),
            "[progress.percentage]{task.percentage:>3.0f}%",
            TimeElapsedColumn(),
            auto_refresh=True
        )
        self.progress_id = self.progress.add_task(f"{task.name}", total=1)
        self.progress.start()

        task.start_time = time.time()


    def task_completed(self, task: Task, result: AggregatedResult) -> None:
        """
        This method is called when all the hosts have completed executing their respective task
        """
        if not result.failed:
            self.progress.advance(self.progress_id)
        self.progress.stop()

        task.end_time = time.time()
        task.run_time = task.end_time - task.start_time
        result.task = task

        self.results.append(result)
        if task.severity_level < self.severity_level:
            return

        self.lock.acquire()

        for host, host_data in result.items():
            status = self._get_status(host_data[0])
            msg = f"* {host} ** changed = {host_data[0].changed} "
            self.console.print(
                f"{msg}{'*' * (self.width - len(msg))}", 
                style="host", end=''
            )

            if self.timing:
                self.console.print(f" [{datetime.timedelta(seconds = result.task.run_time)}]")
            else:
                self.console.line()

            if len(host_data) > 1:
                self._print_result(host_data[0], group=True)

                for data in host_data[1:]:
                    self._print_result(data)

                msg = f"{'^' * 4} END {host_data[0].name} "
                self.console.print(
                    f"{msg}{'^' * (self.width - len(msg))}"
                )
            else:
                self._print_result(host_data[0])

        self.lock.release()


    def task_instance_started(self, task: Task, host: Host) -> None:
        """
        This method is called before a host starts executing its instance of the task
        """
        task.start_time = time.time()
        self.progress.tasks[0].total += 1


    def task_instance_completed(
        self, task: Task, host: Host, result: MultiResult
    ) -> None:
        """
        This method is called when a host completes its instance of a task
        """
        if not result.failed:
            self.progress.advance(self.progress_id)

        task.end_time = time.time()
        task.run_time = task.end_time - task.start_time
        result[0].task = task


    def subtask_instance_started(self, task: Task, host: Host) -> None:
        """
        This method is called before a host starts executing a subtask
        """
        task.start_time = time.time()
        self.progress.tasks[0].total += 1

    def subtask_instance_completed(
        self, task: Task, host: Host, result: MultiResult
    ) -> None:
        """
        This method is called when a host completes executing a subtask
        """
        if not result.failed:
            self.progress.advance(self.progress_id)

        task.end_time = time.time()
        task.run_time = task.end_time - task.start_time
        result[0].task = task


    def _print_result(self, result: Result, group: bool = False) -> None:
        symbol = 'v' if group else '-'
        msg = f"{symbol * 4} {result.name} ** changed = {result.changed} "
        self.console.print(
            f"{msg}{symbol * (self.width - len(msg))}",
            highlight=False, style=self._get_status(result), end=''
        )

        if self.timing:
            self.console.print(f" \[{datetime.timedelta(seconds = result.task.run_time)}]", end='')

        level_name = logging.getLevelName(result.severity_level)
        self.console.print(f" {level_name}")

        

        for attr in ['stdout', 'result', 'diff']:
            x = getattr(result, attr, None)

            if x:
                self.console.print(x, highlight=False)


    def _get_status(self, result: Result) -> str:
        if result.failed:
            return 'failed'
        elif result.changed:
            return 'changed'
        else:
            return 'ok'


    def results_summary(self) -> None:
        table = Table(expand=True, show_lines=False, box=ROUNDED, show_footer=True, width=self.width)

        table.add_column("Task",ratio=5, no_wrap=True, footer='Total')
        table.add_column("Ok", ratio=1, style="ok")
        table.add_column("Changed", ratio=1, style="changed")
        table.add_column("Failed", ratio=1, style="failed")

        totals = {'ok': 0, 'failed': 0, 'changed': 0}
        for result in self.results:
            failed = ok = changed = 0
            
            for host_data in result.values():
                failed += len(list(filter(lambda x: x.failed, host_data)))
                changed += len(list(filter(lambda x: x.changed, host_data)))
                ok += len(list(filter(lambda x: not x.changed and not x.failed, host_data)))
                
            table.add_row(result.name, str(ok), str(changed), str(failed))
            totals['ok'] += ok
            totals['changed'] += changed
            totals['failed'] += failed
        
        table.columns[1].footer = f"{totals['ok']}"
        table.columns[2].footer = f"{totals['changed']}"
        table.columns[3].footer = f"{totals['failed']}"

        self.console.print(table, width=self.width)


    def write_results(self, filename: str = "results.html", format="html") -> None:
        if format == "text":
            self.console.save_text(filename)
        else:
            self.console.save_html(filename)


    def write_inventory(self, nr: Inventory) -> None:
        for host, host_data in nr.inventory.hosts.items():
            data = host_data.dict()
            del data["name"]
            self.console.print(host, style="bold white")
            self.console.print(yaml.dump(data))

