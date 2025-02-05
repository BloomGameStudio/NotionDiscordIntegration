from setuptools import setup, find_packages

setup(
    name="notion-discord-bot",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "discord.py",
        "sqlalchemy",
        "asyncpg",
        "python-dotenv",
    ],
)