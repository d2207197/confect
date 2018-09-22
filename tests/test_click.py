import datetime as dt

import pendulum as pdl
import pytest

click = pytest.importorskip("click")


@pytest.fixture(scope='function')
def click_runner(request):
    from click.testing import CliRunner
    return CliRunner()


def test_help(conf, click_runner):
    @click.command()
    @conf.click_options
    def cli():
        return

    result = click_runner.invoke(cli, ['--help'])
    assert result.output == ('''Usage: cli [OPTIONS]

Options:
  --dummy-x INTEGER           [default: 3]
  --dummy-y TEXT              [default: some string]
  --yummy-kind TEXT           [default: seafood]
  --yummy-name TEXT           [default: fish]
  --yummy-weight FLOAT        [default: 10.5]
  --yummy-rank INTEGER        [default: 3]
  --yummy-sold BOOLEAN        [default: True]
  --yummy-some_day DATE       [default: 2018-06-01]
  --yummy-some_time DATETIME  [default: 2018-06-01T03:02:00+08:00]
  --help                      Show this message and exit.
''')


def test_builtin_types(conf, click_runner):
    @click.command()
    @conf.click_options
    def cli():
        click.echo(f'yummy.name = {conf.yummy.name}')
        click.echo(f'yummy.weight = {conf.yummy.weight}')
        click.echo(f'yummy.rank = {conf.yummy.rank}')
        click.echo(f'yummy.sold = {conf.yummy.sold}')
        assert conf.yummy.name == 'octopus'
        assert conf.yummy.weight == 20.0
        assert conf.yummy.rank == 4
        assert conf.yummy.sold is False

    assert conf.yummy.name == 'fish'
    assert conf.yummy.weight == 10.5
    assert conf.yummy.rank == 3
    assert conf.yummy.sold is True

    result = click_runner.invoke(
        cli, ['--yummy-name', 'octopus',
              '--yummy-weight', '20',
              '--yummy-rank', '4',
              '--yummy-sold', 'False'
              ])
    assert result.output == ('yummy.name = octopus\n'
                             'yummy.weight = 20.0\n'
                             'yummy.rank = 4\n'
                             'yummy.sold = False\n'
                             )
    assert conf.yummy.name == 'octopus'
    assert conf.yummy.weight == 20.0
    assert conf.yummy.rank == 4
    assert conf.yummy.sold is False


def test_other_types(conf, click_runner):
    @click.command()
    @conf.click_options
    def cli():
        click.echo(f'yummy.some_day = {conf.yummy.some_day}')
        click.echo(f'yummy.some_time = {conf.yummy.some_time}')
        assert conf.yummy.some_day == dt.date(2018, 8, 3)
        assert conf.yummy.some_time == pdl.datetime(
            2018, 8, 3, 3, 3, tz='Asia/Taipei')

    assert conf.yummy.some_day == pdl.date(2018, 6, 1)
    assert conf.yummy.some_time == pdl.datetime(
        2018, 6, 1, 3, 2, tz='Asia/Taipei')

    result = click_runner.invoke(
        cli, ['--yummy-some_day', '2018-08-03',
              '--yummy-some_time', '2018-08-03T03:03+08:00',
              ])
    assert result.output == ('yummy.some_day = 2018-08-03\n'
                             'yummy.some_time = 2018-08-03T03:03:00+08:00\n')
    assert conf.yummy.some_day == dt.date(2018, 8, 3)
    assert conf.yummy.some_time == pdl.datetime(
        2018, 8, 3, 3, 3, tz='Asia/Taipei')
