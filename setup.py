from setuptools import setup, find_packages

# Idea borrowed from http://cburgmer.posterous.com/pip-requirementstxt-and-setuppy
install_requires, dependency_links = [], []
for line in open('requirements.txt'):
    line = line.strip()
    if line.startswith('-e'):
        dependency_links.append(line[2:].strip())
    elif line:
        install_requires.append(line)

setup(name='oxpeditor',
      version='0.1.1',
      packages=find_packages(),
      include_package_data=True,
      package_data={'': ['*.xml', 'templates/*.html']},
      install_requires=install_requires,
      dependency_links=dependency_links)
