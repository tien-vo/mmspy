"""Configure `numba`.

.. todo:: Add docstring.

"""

import os

from mmspy.config.paths import CACHE_DIR

os.environ["NUMBA_CACHE_DIR"] = str(CACHE_DIR / "numba")
