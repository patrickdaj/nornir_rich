from typing import List
from rich import style
from ruamel import yaml
from dataclasses import dataclass, field
from rich.console import Console
from rich.style import Style
from rich.text import Text
from rich.table import Table
from rich.box import ROUNDED
from rich.markdown import Markdown
from rich.highlighter import ReprHighlighter, Highlighter
from rich.panel import Panel
from rich.padding import Padding
from rich.pretty import Pretty
from rich.traceback import Traceback
import threading
import logging

from nornir.core.task import AggregatedResult, MultiResult, Result
from nornir.core.inventory import Inventory

LOCK = threading.Lock()


class RedHighlighter(Highlighter):
    def highlight(self, text):
        text.stylize("bright_red", 0, len(text))


@dataclass
class RichResults(object):
    width: int = 80
    lock: threading.Lock = threading.Lock()
    results: List[AggregatedResult] = field(default_factory=list)
    highlighter: Highlighter = ReprHighlighter()
    console: Console = Console(record=True)
    current_indent: int = 0

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
            self.console.line()
        finally:
            LOCK.release()

    def _print_result(  # pylama:ignore=C:select=C901
        self,
        result: Result,
        vars: List[str] = None,
        failed: bool = False,
        severity_level: int = logging.info,
    ) -> None:

        if isinstance(result, AggregatedResult):
            msg = f"{result.name} (hosts: {len(result)}"
            if result.failed:
                msg += ", failed: True"
            if result.failed_hosts:
                msg += f", failed_hosts: {list(result.failed_hosts.keys())})"
            else:
                msg += ")"

            if severity_level >= 20:
                self.console.print(
                    f"{msg}", style=Style(underline=True, color="bright_black")
                )

            for host, host_data in sorted(result.items()):
                max_severity_level = max(host_data, key=lambda k: k.severity_level)
                max_severity_level = max_severity_level.severity_level
                msg = f"{host} "

                if max_severity_level >= severity_level:
                    result_details = []
                    if host_data.changed:
                        result_details.append("changed = True")

                    if host_data.failed or failed:
                        result_details.append("failed = True")

                    if result_details:
                        msg += "(" + ", ".join(result_details) + ")"

                    self.console.print(
                        f"* {msg}", style=Style(color="blue"),
                    )
                self._print_result(host_data, vars, failed, severity_level)

        elif isinstance(result, MultiResult):
            self.current_indent += 1
            self._print_individual_result(
                result[0], group=True, vars=vars, severity_level=severity_level
            )

            for r in result[1:]:
                self._print_result(r, vars, failed, severity_level=severity_level)

            self.current_indent -= 1

        elif isinstance(result, Result):
            self._print_individual_result(
                result, vars=vars, severity_level=severity_level
            )

    def _print_individual_result(
        self,
        result: Result,
        vars: List[str],
        group: bool = False,
        severity_level: int = 20,
    ) -> None:

        title_text = f"{result.name} "

        result_details = []
        if result.changed:
            result_details.append("changed = True")

        if result.severity_level >= severity_level:
            result_details.append(
                f"logging_level = {logging.getLevelName(result.severity_level)}"
            )

        if result.failed:
            result_details.append("failed = True")

        if result_details:
            title_text += "(" + ", ".join(result_details) + ")"

        title = self.highlighter(title_text)
        if group:
            group_title = f"{' ' * self.current_indent}:heavy_check_mark: {title_text}"

        if result.severity_level >= severity_level:
            items_table = Table.grid(padding=(0, 1), expand=False)
            items_table.add_column(width=self.current_indent)
            items_table.add_column(justify="right")

        attrs = vars if vars else ["stdout", "result", "stderr", "diff"]

        for attr in attrs:
            x = getattr(result, attr, None)

            if x and attr == "tests":
                for i, test in enumerate(result.tests.tests):
                    status = ":green_circle:" if test.passed else ":red_circle:"
                    items_table.add_row(
                        None,
                        f"{attr} {status} " if i == 0 else f"{status}",
                        Pretty(test, highlighter=self.highlighter),
                    )
            elif x and attr == "exception":
                if result.severity_level >= severity_level:
                    # TODO - figure out how to add traceback highlighting
                    highl = RedHighlighter()
                    items_table.add_row(
                        None, f"{attr} = ", Pretty(x, highlighter=highl),
                    )
            elif x:
                if result.severity_level >= severity_level:
                    if result.failed:
                        highl = RedHighlighter()
                    else:
                        highl = self.highlighter
                    items_table.add_row(
                        None, f"{attr} = ", Pretty(x, highlighter=highl)
                    )
        if result.severity_level >= severity_level:
            if items_table.row_count > 0:
                self.console.print(
                    Padding(
                        Panel(items_table, title=title, title_align="left"),
                        (0, 0, 0, self.current_indent + 1),
                    )
                )
            else:
                self.console.print(group_title)

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

    def _get_summary_count(
        self, count: int, style: str
    ) -> Text:  # pylama:ignore=C:select=C901
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
