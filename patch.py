"""
This file MUST be imported first before anything else!
It patches eventlet to work with standard library.
"""
import eventlet
eventlet.monkey_patch()