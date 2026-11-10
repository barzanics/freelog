from setuptools import find_packages, setup

setup(name="worktracker", version="6.0.1", packages=find_packages(exclude=("worktracker.tests",)), python_requires=">=3.10",
      install_requires=["PyQt5>=5.15"], extras_require={"full": ["openpyxl>=3.1", "reportlab>=4.0", "cryptography>=42"]},
      entry_points={"gui_scripts": ["worktracker=worktracker.main:main"]})
