# Dependency Installation

To reinstall everything (runtime plus docs/dev/lint/tests), run:

```bash
sudo apt-get update && sudo apt-get install -y default-jre
uv pip install --group dev --group tests --group lint --group docs
```

To force a SonarQube check, run:

```bash
pysonar \
  --sonar-host-url=http://host.containers.internal:9000 \
  --sonar-token=sqb_f4f29cf6e1c2548af1564a9e5fe4a5c845234938 \
  --sonar-project-key=sdd-cash-manager
```

If you want a clean start, delete the existing virtual environment before rerunning the command.
