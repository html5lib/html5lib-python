import os
import sys
import glob

#Allow us to import the parent module
os.chdir(os.path.split(os.path.abspath(__file__))[0])
sys.path.insert(0, os.path.abspath(os.path.join(os.pardir, "src")))

try:
    import simplejson
except:
    import re
    class simplejson:
        def load(f):
            true, false = True, False
            input=re.sub(r'(".*?(?<!\\)")',r'u\1',f.read().decode('utf-8'))
            return eval(input.replace('\r',''))
        load = staticmethod(load)

def html5lib_test_files(subdirectory, files='*.dat'):
    return glob.glob(os.path.join(os.path.pardir,os.path.pardir,'testdata',subdirectory,files))
