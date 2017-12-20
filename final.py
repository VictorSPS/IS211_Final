#!/usr/bin/python
# -*- coding: utf-8 -*-
"""IS211. Final"""

import urllib2
from flask import Flask, render_template, request, redirect, session, g, url_for, abort, flash
import pickle
import os.path
import time
import re
import json
import sqlite3
from contextlib import closing

DATABASE = 'bookcatalogue.db'
DEBUG = True
SECRET_KEY = 'generate it using os.urandom(24)'
USERNAME = 'admin'
PASSWORD = 'password'

app = Flask(__name__)
app.config.from_object(__name__)

API_URL = "https://www.googleapis.com/books/v1/volumes?q=isbn:"

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])


@app.before_request
def before_request():
    g.db = connect_db()


@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()


@app.route('/lookup', methods=['POST', 'GET'])
def lookup():
    if request.method == 'POST':
        isbn = request.form['ISBN']
        if isbn == "":
            flash("Please Enter an ISBN Number")
            return redirect(url_for('lookup'))
        else:
            try:
                url = API_URL + isbn
                html = urllib2.urlopen(url)
                data = html.read()
                data = json.loads(data)
                volumeinfo = data['items'][0]['volumeInfo']
                title = volumeinfo['title']
                authors = volumeinfo['authors'][0]
                pagecount = volumeinfo['pageCount']
                averagerating = volumeinfo['averageRating']
                thumbnail = volumeinfo['imageLinks']['smallThumbnail']
                return render_template('lookup.html', thumbnail=thumbnail,
                                       title=title, authors=authors,
                                       pagecount=pagecount,
                                       averagerating=averagerating, isbn=isbn)
            except LookupError:
                flash("ISBN lookup error")
                return redirect(url_for('lookup'))
    if request.method == 'GET':
        return render_template('lookup.html')


@app.route('/add', methods=['POST'])
def add():
    if not session.get('logged_in'):
        abort(401)
    try:
        g.db.execute('INSERT INTO bookcatalogue (ISBN, TITLE, AUTHORS, PAGECOUNT, '
                     'AVERAGERATING, THUMBNAIL) values (?, ?, ?, ?, ?, ?)',
                     (request.form['isbn'], request.form['title'],
                      request.form['authors'], request.form['pagecount'],
                      request.form['averagerating'], request.form['thumbnail']))
        g.db.commit()
        flash("Book added to library")
        return redirect(url_for('homepage'))
    except():
        flash("Error adding to library")
        return redirect(url_for('homepage'))


@app.route('/delete', methods=['GET'])
def delete():
    book_id = request.args.get('id')
    g.db.execute('DELETE FROM bookcatalogue WHERE ID = ?', book_id)
    g.db.commit()
    flash("Deleted library item")
    return redirect(url_for('homepage'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = "Invalid Username"
            flash("Invalid Username")
        elif request.form['password'] != app.config['PASSWORD']:
            error = "Invalid Password"
            flash("Invalid Password")
        else:
            session['logged_in'] = True
            flash("You were logged in. Your current library is displayed below.")
            return redirect(url_for('homepage'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash("You were logged out")
    return redirect(url_for('homepage'))


@app.route('/')
def homepage():
    cur = g.db.execute('SELECT ID, ISBN, TITLE, AUTHORS, PAGECOUNT, '
                       'AVERAGERATING, THUMBNAIL FROM bookcatalogue')
    bookcatalogue = [dict(id=row[0], isbn=row[1], title=row[2], authors=row[3],
                  pagecount=row[4], averagerating=row[5],
                  thumbnail=row[6]) for row in cur.fetchall()]
    return render_template('index.html', bookcatalogue=bookcatalogue)


if __name__ == "__main__":
    app.run()
