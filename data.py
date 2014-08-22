#!flask/bin/python

from app import app

import os
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash

# app = Flask(__name__)

#if __name__ == '__main__':
app.debug = True
#  app.run(host='0.0.0.0') # public binding
app.run() # localhost hinding
