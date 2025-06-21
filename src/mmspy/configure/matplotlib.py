"""Set up matplotlib.

.. todo:: Add docstring.

"""

__all__ = ["configure_matplotlib"]

import atexit
import logging
import os
import shutil
import tempfile
from importlib.resources import files

import matplotlib
import matplotlib.pyplot as plt

latex_binary = shutil.which("latex")
stylesheet = files("mmspy.data") / "mmspy.mplstyle"

log = logging.getLogger(__name__)


def configure_matplotlib(
    use_stylesheet: bool = True,
    use_tex: bool = False,
    cache_tex: bool = False,
) -> None:
    """Configure matplotlib with custom stylesheet and settings.

    Parameters
    ----------
    use_stylesheet : bool
        Use custom stylesheet.
    use_tex : bool
        Enable latex if toggled and a binary is found in the system path.
    cache_tex : bool
        Configure caching behavior of matplotlib for latex outputs.
        Recommended for multiprocessing.

    """
    plt.rc("text", usetex=use_tex and latex_binary is not None)

    if use_stylesheet:
        logging.info(f"Using stylesheet {str(stylesheet)}")
        plt.style.use(str(stylesheet))

    if cache_tex:
        # Quick fix for matplotlib's tex cache in multiprocessing
        mpldir = tempfile.mkdtemp()
        atexit.register(shutil.rmtree, mpldir)
        umask = os.umask(0)
        os.umask(umask)
        os.chmod(mpldir, 0o777 & ~umask)
        os.environ["HOME"] = mpldir
        os.environ["MPLCONFIGDIR"] = mpldir
        logging.debug(f"Tex cache path: {mpldir}")

        class TexManager(matplotlib.texmanager.TexManager):
            texcache = os.path.join(mpldir, "tex.cache")

        matplotlib.texmanager.TexManager = TexManager  # type: ignore[misc]
