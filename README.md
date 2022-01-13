# HB Platform User Management

Hummingbird Platform users management service.

[![CircleCI](https://circleci.com/gh/HummingbirdTechGroup/hb-platform-user-management/tree/main.svg?style=svg&circle-token=1c1a45ecbfbbbeea388ea05f0df8df0fe3fdd87c)](https://circleci.com/gh/HummingbirdTechGroup/hb-platform-user-management/tree/main)


## Development

### Initial configuration

This project started with a Python version **3.9.5**. Version **3.10** branch is used for the
production Docker containers. Use as minimum one of those versions when developing in local.

This service needs access to a PostgreSQL database running in a PostgreSQL +13 cluster.

In case you need to specify local development project settings, you can create a `.env` file in the
root of the project specifying them as environment variables. Core project settings you might need
to set up for running the service in local are:

- `DEBUG`: A boolean flag will lower all Python loggers level to `DEBUG` if set to `true`.
- `DATABASE_URL`: The URI of your local database, e.g. `postgresql://user:password@localhost:5432/user_management`.
- `GCP_CREDENTIALS`: The credentials of a [GCP Service Account](https://cloud.google.com/iam/docs/service-accounts)
  with permissions to operate with GCP Identity Platform.

:warning: **Warning:** setting `GCP_CREDENTIALS` configuration value to a real Service Account will
make your local service synchronize your local development data with the GCP project the Service
Account is assigned to. Otherwise your data will remain in your local PostgreSQL database. Most
probably you don't need this setting, unless you are actually developing or testing the
synchronization with GCP IP backend. Also, take into account that **not** setting the value will
make the app pick up the System Default Google Credentials, which if you have them set up it might
show some errors due to a lack of permissions to operate with GCP-IP.

### Docker setup

Make sure you have [Docker](https://docs.docker.com) installed in your local machine.

Create a Docker image from the HB Platform User Management project:

```bash
DOCKER_BUILDKIT=1 docker build --ssh default -t hb-platform-user-management .
```

:warning: **Note:** If you are using MacOS, you may need to run `ssh-add` to add private key
identities to the authentication agent first for this to work.

You can run the Docker container in local once the image is built:

```bash
docker run --env-file .env hb-platform-user-management <ARGUMENTS>
```

### Native setup

To develop and run the project in native setup it is extremely recommended to use [Poetry](https://python-poetry.org/)
Poetry will create a virtual environment for you and install the dependencies on it:

1. Install Poetry (if you don't have it yet):
   ```bash
   pip install poetry
   ```
2. Install project requirements and development requirements:
   ```bash
   poetry install
   ```

You can now test the basic project setup by running this command in terminal:

```bash
uvicorn --factory user_management.main:create_app
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

[pre-commit](https://pre-commit.com) is installed automatically in development environment by Poetry.
If you are running the Docker setup, please install it with `pip` in your host machine:

    $ pip install pre-commit
