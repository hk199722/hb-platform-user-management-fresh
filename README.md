# HB Platform User Management

Hummingbird Platform users management service.


## Development

### Initial configuration

In case you need to specify local development project settings, you can create a `.env` file in the 
root of the project specifying them as environment variables.

### Docker setup (recommended)

Make sure you have [Docker](https://docs.docker.com) installed in your local machine.

Create a Docker image from the HB Platform User Management project:

```bash
DOCKER_BUILDKIT=1 docker build --ssh default -t hb-platform-user-management .
```

**Note:** If you are using MacOS, you may need to run `ssh-add` to add private key identities to the
authentication agent first for this to work.

You can run the Docker container in local once the image is built:

```bash
docker run --env-file .env hb-platform-user-management <ARGUMENTS>
```

### Native setup

To develop and run the project in native setup it is extremely recommended to use a 
[Python virtual environment](https://docs.python.org/3/tutorial/venv.html). There is a range of
options to create a virtual environment, but here we will describe the easiest one which is using
the `venv` builtin module.

1. Type on the terminal:
   ```bash
   python -m venv ~/.virtualenvs/hb-platform-user-management
   ```
2. Activate the virtual environment:
   ```bash
   source ~/.virtualenvs/hb-platform-user-management/bin/activate
   ```
3. Install project requirements and development requirements:
   ```bash
   pip install -r requirements/base.txt
   pip install -r requirements/development.txt
   ```

You can now test the basic project setup by running this command in terminal:

```bash
python user_management/main.py
```

:warning: **Note:** you might need to add the generated project root directory to the
[`PYTHONPATH`](https://docs.python.org/3/using/cmdline.html#envvar-PYTHONPATH) in some cases:

```bash
export PYTHONPATH="{$PYTHONPATH}:/absolute/path/to/hb-platform-user-management"
```   


## Contributing

Before starting to contribute to Analysis Data Transformation, please install `pre-commit` to make
sure your changes get checked for style and standards before committing them to repository:

    $ pre-commit install

[pre-commit](https://pre-commit.com) is installed automatically in development environment by pip.
If you are running the Docker setup, please install it with `pip` in your host machine:

    $ pip install pre-commit
