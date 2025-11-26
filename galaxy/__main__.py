#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Galaxy Framework Main Entry Point

This module allows Galaxy framework to be run as a package:
    python -m ufo.galaxy --interactive
    python -m ufo.galaxy "Create a data pipeline"
"""

import asyncio
import sys
from .galaxy import main

if __name__ == "__main__":
    asyncio.run(main())
