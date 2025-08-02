from setuptools import setup, find_packages

setup(
    name="NarratorChat",
    version="0.1.0",
    description="TTS bot for Twitch IRC",
    author="NerveCulture",
    packages=find_packages(),  # This auto-discovers packages like NarratorChat/
    install_requires=[
        "pywin32",
        "pystray",
        "pillow",
        # Add any other dependencies here
    ],
    entry_points={
        "console_scripts": [
            # optional: you could define a CLI command here later if needed
        ],
    },
    python_requires=">=3.8",
)
