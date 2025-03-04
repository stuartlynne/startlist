import sys
import os
import autopage  
#from autopage import AutoPager

# Extend the AutoPager class
# This class will also handle the stderr redirection
#
# stderr=True       - allow stdedrr without redirction use stderr=True
# stderrdup=True    - redirect stderr to stdout 
# stderr=False and stderrdup=False  - redirect stderr to /dev/null
#
# fixLess=True      - apply fix to the LESS environment variable
# fixLess=False     - do not apply fix to the LESS environment variable

class AutoPagerEx(autopage.AutoPager):
    def __init__(self, stderr=False, stderrdup=False, fixLess=True, **kws):
        self.stderr = stderr
        self.stderrdup = stderrdup
        self.fixLess = fixLess
        if fixLess:
            self.less = os.environ.get('LESS', '')
            os.environ['LESS'] += " -F --quit-if-one-screen"
        super(AutoPagerEx, self).__init__(**kws)

    def __enter__(self):
        #print('AutoPagerEx.__enter__ stderr:', self.stderr, 'stderrdup:', self.stderrdup, 'less:', self.less, 'LESS:', os.environ.get('LESS', ''))
        stdout = super(AutoPagerEx, self).__enter__()
        return stdout, sys.stderr if self.stderr else stdout if self.stderrdup else open(os.devnull, 'w')

    def __exit__(self, exc_type, exc_value, traceback):
        if self.fixLess:
            os.environ['LESS'] = self.less
        return super(AutoPagerEx, self).__exit__(exc_type, exc_value, traceback)
