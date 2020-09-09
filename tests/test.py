from nornir_rich.plugins.processors import RichResults
from nornir import InitNornir
from nornir_utils.plugins.tasks.data import echo_data

nr = InitNornir(config_file='test_data/config.yaml')
rr = RichResults()
nr.processors.append(rr)

nr.run(echo_data, x=1, y=2)
