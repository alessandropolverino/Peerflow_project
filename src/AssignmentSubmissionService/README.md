## Use this template

To make this template work, just create a python environment and install the dependencies:

```bash
python3 -m venv venv
# activate the env with the OS specific command
source venv/bin/activate
pip install "fastapi[standard]" pymongo
```

Then, you can export your dependencies to a `requirements.txt` file:

```bash
pip freeze > requirements.txt
```

Or with the make command:

```bash
make export_dep
```

Then, make the necessary changes to the docker-compose\* files.