from typing import List, Any
from ruamel import yaml
from dataclasses import dataclass, field
from rich.console import Console
from rich.style import Style
from rich.text import Text
from rich.table import Table
from rich.box import ROUNDED
import threading
import logging

from nornir.core.task import AggregatedResult, MultiResult, Result
from nornir.core.inventory import Inventory

LOCK = threading.Lock()


@dataclass
class RichResults(object):
    width: int = 80
    lock: threading.Lock = threading.Lock()
    results: List[AggregatedResult] = field(default_factory=list)
    console: Console = Console(record=True)

    def print(
        self,
        result: Result,
        vars: List[str] = None,
        failed: bool = False,
        severity_level: int = logging.INFO,
    ) -> None:
        """
        Prints an object of type `nornir.core.task.Result`
        Arguments:
            result: from a previous task
            vars: Which attributes you want to print
            failed: if ``True`` assume the task failed
            severity_level: Print only errors with this severity level or higher
        """
        LOCK.acquire()

        try:
            self.results.append(result)
            self._print_result(result, vars, failed, severity_level)
        finally:
            LOCK.release()

    def _print_result(
        self,
        result: Result,
        vars: List[str] = None,
        failed: bool = False,
        severity_level: int = logging.info,
    ) -> None:

        if isinstance(result, AggregatedResult):
            msg = f"{result.name}"
            self.console.print(f"{msg}{'*' * (self.width - len(msg))}")

            for host, host_data in sorted(result.items()):
                msg = f"* {host} ** changed = {host_data.changed} "

                self.console.print(
                    f"{msg}{'*' * (self.width - len(msg))}", style=Style(color="blue"),
                )
                self._print_result(host_data, vars, failed, severity_level)

        elif isinstance(result, MultiResult):
            self._print_individual_result(result[0], group=True, vars=vars)

            for r in result[1:]:
                self._print_result(r, vars, failed, severity_level)

            msg = f"{'^' * 4} END {result[0].name} "
            self.console.print(
                f"{msg}{'^' * (self.width - len(msg))}",
                style=self._get_status(result[0]),
            )

        elif isinstance(result, Result):
            self._print_individual_result(result, vars=vars)

    def _print_individual_result(
        self, result: Result, vars: List[str], group: bool = False,
    ) -> None:
        symbol = "v" if group else "-"
        msg = f"{symbol * 4} {result.name} ** changed = {result.changed} "
        level_name = logging.getLevelName(result.severity_level)
        post = f" {level_name}"

        self.console.print(
            f"{msg}{symbol * (self.width - len(msg) - len(post))}{post}",
            highlight=False,
            markup=False,
            style=self._get_status(result),
        )

        attrs = vars if vars else ["stdout", "result", "stderr", "diff"]

        for attr in attrs:
            x = getattr(result, attr, None)

            if x:
                self.console.print(x, highlight=False)

        if getattr(result, 'tests', None):

            for test in result.tests.tests:
                self.console.print(test, style=self._get_test_status(test))


    def _get_test_status(self, test: Any) -> Style:
        if test.passed:
            return Style(color="dark_green")
        else:
            return Style(color="red")
    

    def _get_status(self, result: Result) -> Style:
        if result.failed:
            return Style(color="red")
        elif result.changed:
            return Style(color="orange1")
        else:
            return Style(color="dark_green")

    def summary(self) -> None:
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

    def write(self, filename: str = "results.html", format: str = "html") -> None:
        self.lock.acquire()
        if format == "text":
            self.console.save_text(filename)
        else:
            self.console.save_html(filename)
        self.lock.release()

    def inventory(self, nr: Inventory, passwords: bool = False) -> None:
        table = Table(expand=True, box=ROUNDED, show_lines=True, width=self.width,)

        table.add_column("Host")
        table.add_column("Data")

        for host, host_data in nr.inventory.hosts.items():
            host_dict = host_data.dict()
            if not passwords:
                host_dict["password"] = "******"

            table.add_row(host, yaml.dump(host_dict))

        self.lock.acquire()
        self.console.print(table, width=self.width)
        self.lock.release()
