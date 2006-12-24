from distutils.core import setup
setup(name='html5lib',
      version='0.1',
      url='http://code.google.com/p/html5lib/',
      license="MIT License",
      description='HTML parser based on the WHAT-WG Web Applications 1.0' 
                  '("HTML5") specifcation',
      packages=['html5lib'],
      package_dir = {'html5lib': 'src'}
      )
