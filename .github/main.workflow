workflow "run linters and tests" {
  on = "push"
  resolves = ["notify build succeeded"]
}

action "py3.7 linting black" {
  uses = "docker://gr1n/the-python-action:master"
  args = "tox -e py37-black"
  env = {
    PYTHON_VERSION = "3.7.2"
  }
}

action "py3.7 linting flake8" {
  uses = "docker://gr1n/the-python-action:master"
  args = "tox -e py37-flake8"
  env = {
    PYTHON_VERSION = "3.7.2"
  }
}

action "py3.7 linting isort" {
  uses = "docker://gr1n/the-python-action:master"
  args = "tox -e py37-isort"
  env = {
    PYTHON_VERSION = "3.7.2"
  }
}

action "py3.7 linting mypy" {
  uses = "docker://gr1n/the-python-action:master"
  args = "tox -e py37-mypy"
  env = {
    PYTHON_VERSION = "3.7.2"
  }
}

action "py3.7 testing" {
  needs = [
    "py3.7 linting black",
    "py3.7 linting flake8",
    "py3.7 linting isort",
    "py3.7 linting mypy",
  ]
  uses = "docker://gr1n/the-python-action:master"
  args = "tox -e py37-tests"
  env = {
    PYTHON_VERSION = "3.7.2"
  }
}

action "notify build succeeded" {
  needs = "py3.7 testing"
  uses = "docker://gr1n/the-telegram-action:master"
  env = {
    TELEGRAM_MESSAGE = "`aiodogstatsd` build succeeded"
  }
  secrets = [
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
  ]
}

workflow "notify about new star" {
  on = "watch"
  resolves = ["notify project starred"]
}

action "notify project starred" {
  uses = "docker://gr1n/the-telegram-action:master"
  secrets = ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"]
  env = {
    TELEGRAM_MESSAGE = "`aiodogstatsd` starred!"
  }
}

workflow "publish" {
  on = "release"
  resolves = ["notify project published"]
}

action "py37 publish" {
  uses = "docker://gr1n/the-python-action:master"
  secrets = ["PYPI_PASSWORD", "PYPI_USERNAME"]
  env = {
    PYTHON_VERSION = "3.7.2"
  }
  args = "poetry publish --username=$PYPI_USERNAME --password=$PYPI_PASSWORD --build"
}

action "notify project published" {
  uses = "docker://gr1n/the-telegram-action:master"
  needs = ["py37 publish"]
  secrets = ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"]
  env = {
    TELEGRAM_MESSAGE = "`aiodogstatsd` published to PyPI"
  }
}
