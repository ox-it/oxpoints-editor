from setuptools import setup, find_packages

setup(name='oxpeditor',
      version='0.1',
      packages=find_packages(),
      include_package_data=True,
      package_data={'': ['*.xml', 'templates/*.html']})
