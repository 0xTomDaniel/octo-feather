from widgets.cli import main


def test_show(capsys):
    assert main(["show", "w1"]) == 0
    assert capsys.readouterr().out == "sprocket\n"
