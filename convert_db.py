#!/usr/bin/env python2
# coding: utf-8

from kebleball.database import *
import MySQLdb
from MySQLdb.cursors import DictCursor
from datetime import datetime
import re

affiliations = {
    1: 6,
    2: 1,
    3: 2,
    4: 3
}

conn=MySQLdb.connect(
    host='<host>',
    user='<user>',
    passwd='<password>',
    db='<database>',
    cursorclass=DictCursor
)
c = conn.cursor()

c.execute('SELECT * FROM `users`')

while True:
    user = c.fetchone()
    if user is None:
        break

    print user['name']

    if user['college'] == 45:
        college = 46
    else:
        college = user['college']

    affiliation = affiliations[user['affiliation']]

    names = user['name'].split(' ')
    firstname = names.pop(0)
    lastnames = ' '.join(names)
    if lastnames == '':
        lasnames = 'UNKNOWN'

    new_user = User(
        user['emailaddr'],
        'password',
        firstname,
        lastnames,
        user['phonenum'],
        college,
        affiliation
    )
    new_user.id = user['userid']
    new_user.passhash = user['passhash']

    if user['role'] >= 10:
        new_user.secretkey = None
        new_user.verified = True

    if user['role'] == 100:
        new_user.promote()

    db.session.add(new_user)
    db.session.commit()

c.execute('SELECT * FROM `tickets`')

while True:
    ticket = c.fetchone()
    if ticket is None:
        break

    owner = User.get_by_id(ticket['ownerid'])

    price = int(ticket['price'] * 100)

    new_ticket = Ticket(owner, 'Battels', price)
    new_ticket.id = ticket['ticketid']
    new_ticket.setReferrer(ticket['referrer'])

    if ticket['ispaidfor'] == 1:
        term = re.match(
            r'Put on (MT|HT|MTHT) battels of ([A-Z+0-9]{6})',
            ticket['paymentref']
        ).group(1)

        owner.battels.charge(new_ticket, term, True)
    else:
        new_ticket.expires = ticket['expireat']

    db.session.add(new_ticket)
    db.session.commit()

c.execute("DELETE FROM `log` WHERE `ticketid` NOT IN (SELECT `ticketid` FROM `tickets`)")
c.execute("DELETE FROM `log` WHERE `actorid` NOT IN (SELECT `userid` FROM `users`)")
c.execute("DELETE FROM `log` WHERE `targetid` NOT IN (SELECT `userid` FROM `users`)")
c.execute("UPDATE `log` SET `action`=REPLACE(`action`,'Â£','£') WHERE 1")
c.execute('SELECT * FROM `log`')

while True:
    entry = c.fetchone()
    if entry is None:
        break

    new_entry = Log(
        entry['ip'],
        entry['action'],
        entry['actorid'],
        entry['targetid'],
        [] if entry['ticketid'] is None else [entry['ticketid']]
    )
    new_entry.timestamp = entry['timestamp']

    db.session.add(new_entry)
    db.session.commit()