#!/usr/bin/env python3
"""Compatibility entry point: --config FILE --output DIR."""
import sys
from cli import main
if __name__=='__main__':
    sys.argv.insert(1,'build')
    sys.exit(main())
