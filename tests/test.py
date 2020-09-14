from nornir_rich.plugins.functions import RichResults
from nornir import InitNornir
from nornir.core.task import Result
from nornir_utils.plugins.tasks.data import echo_data

nr = InitNornir()
rr = RichResults()

def stuff(task):
    return Result(
        host=task.host, exception=Exception("testing"), stdout=task, result=[1, 2, 3]
    )


def level1(task):
    task.run(level2)


def level2(task):
    task.run(level3)


def level3(task):
    return Result(host=task.host, stdout="abcd", result={"x": 9, "y": 10})

def gen_exception(task):
    raise Exception('this is an exception')

rr.print(nr.run(task=echo_data, x=10, z=[1, 2, 3]))

rr.print(nr.run(task=stuff), vars=["stdout", "result", "exception"])

rr.print(nr.run(task=level1), vars=["stdout", "result", "exception"])

rr.print(nr.run(task=gen_exception), vars=["stdout", "result", "exception"])
