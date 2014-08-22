from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash

app = Flask( __name__ ) # create app object
app.config.from_object('config') # some config elements come from this file

from app import views

