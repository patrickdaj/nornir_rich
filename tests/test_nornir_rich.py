from nornir_rich import __version__

def generate_exception(task):
    x = 1 / 0


def test_version():
    assert __version__ == "0.1.0"

def test_exception(nornir):
    nornir.run(generate_exception, name='Generate Exception')

