#!/usr/bin/env python3
"""
Code Protection & Bytecode Compiler
====================================
Made by Satyam

Compiles all source files to optimized Python bytecode (.pyc)
to protect source code from being exposed, inspected or modified.
"""

import os
import sys
import compileall
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()

def protect_codebase():
    print("🔒 Compiling and protecting Telegram Bot codebase...")
    compileall.compile_dir(str(BASE_DIR), force=True, legacy=True, optimize=2)
    print("✅ All Python source files compiled to protected bytecode!")

if __name__ == "__main__":
    protect_codebase()
