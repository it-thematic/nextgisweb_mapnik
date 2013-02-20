from setuptools import setup, find_packages
import sys, os

version = '0.0'

requires = (
    'nextgisweb',
)

entry_points = {
    'nextgisweb.component': ['nextgisweb_mapnik = nextgisweb_mapnik', ],
    'nextgisweb.amd_packages': [ 'nextgisweb_mapnik = nextgisweb_mapnik:amd_packages', ],
}

setup(name='nextgisweb_mapnik',
      version=version,
      description="",
      long_description="",
      classifiers=[],
      keywords='',
      author='',
      author_email='',
      url='',
      license='',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      entry_points=entry_points,
)
