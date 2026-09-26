"""Verify sealed campaign/report evidence; never execute scientific work."""

import sys

from run_publication_campaign import launch

if __name__ == "__main__":
    sys.argv.append("--verify")
    launch()
