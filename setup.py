from setuptools import setup

from manage_shipment.__version__ import __version__

setup(
    name="manage_shipment",
    version=__version__,
    description="Shipment and domestic courier tracking for ERPNext",
    author="Sundaram Technologies",
    author_email="support@sundaramtech.com",
    packages=["manage_shipment"],
    include_package_data=True,
    zip_safe=False,
)
