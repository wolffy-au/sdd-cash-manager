# Dependency Installation

To reinstall everything (runtime plus docs/dev/lint/tests), run:

```bash
sudo apt-get update && sudo apt-get install -y default-jre
pip install --upgrade uv
uv pip install --group dev --group tests --group lint --group docs
```

To force a SonarQube check, run:

```bash
pysonar \
  --sonar-host-url=http://host.containers.internal:9000 \
  --sonar-token=squ_0ef6cbaa955c58d8b5e8073b4c64a71fe3ccd7bf \
  --sonar-project-key=sdd-cash-manager
```

If you want a clean start, delete the existing virtual environment before rerunning the command.
