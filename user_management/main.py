import logging.config

import typer

from user_management.core.config.logging import logging_config


def main():
    # Configuring Python logging.
    logging.config.dictConfig(logging_config)

    typer.echo(
        typer.style(
            "\nWelcome to the auto-generated project layout for " "HB Platform User Management!",
            fg=typer.colors.WHITE,
            bold=True,
        )
    )
    typer.echo(
        "\nYou can probably call your main logic from this `main` function and use it as an "
        "entrypoint \U0001F914\n"
    )
    typer.echo(typer.style("Happy hacking :)\n", fg=typer.colors.GREEN, bold=True))


if __name__ == "__main__":
    typer.run(main)
