from setuptools import find_packages, setup

setup(
    name="stock-alert",
    version="1.0.0",
    description="A CLI tool for managing stock watchlists and price alerts.",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[],  # No external dependencies
    entry_points={
        "console_scripts": [
            "stock-alert=stock_alert.main:main",
            "stock-alert-manage=stock_alert.tools.t_manage_settings:main",
            "stock-alert-monitor=stock_alert.tools.t_monitor_stocks:main",
        ]
    },
)
