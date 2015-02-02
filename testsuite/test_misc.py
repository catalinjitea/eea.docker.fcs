import os

from flask import url_for
from openpyxl import load_workbook

from testsuite import factories
from fcs.models import MailAddress

MIMETYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'


def test_export_companies(client):
    undertaking = factories.UndertakingFactory()
    resp = client.get(url_for('misc.company-list-export'))
    assert resp.status_code == 200
    assert resp.content_type == MIMETYPE
    fn = 'test_file.xlsx'
    with open(fn, 'w') as f:
        f.write(resp.body)
        f.close()
    wb = load_workbook(fn)
    assert len(wb.worksheets) == 1
    rows = wb.worksheets[0].rows
    assert len(rows) == 2
    assert rows[0][0].value == 'company_id'
    assert rows[1][0].value == undertaking.external_id
    assert rows[0][1].value == 'name'
    assert rows[1][1].value == undertaking.name
    assert rows[0][2].value == 'domain'
    assert rows[1][2].value == undertaking.domain
    assert rows[0][3].value == 'status'
    assert rows[1][3].value == undertaking.status
    assert rows[0][4].value == 'undertaking_type'
    assert rows[1][4].value == undertaking.undertaking_type
    assert rows[0][5].value == 'website'
    assert rows[1][5].value == undertaking.website
    os.remove(fn)


def test_mail_address_list(client):
    ma = factories.MailAddress()
    resp = client.get(url_for('misc.mails-list'))
    assert resp.status_code == 200
    data = resp.json
    assert len(data) == 1
    assert data[0]['mail'] == ma.mail
    assert data[0]['first_name'] == ma.first_name
    assert data[0]['last_name'] == ma.last_name


def test_mail_address_add_new(client):
    resp = client.post(url_for('misc.mails-add'), dict(
        mail='a@ya.com', first_name='a', last_name='b'))
    assert resp.status_code == 200
    assert resp.body == 'true'
    assert len(MailAddress.query.all()) == 1
    ma = MailAddress.query.all()[0]
    assert ma.mail == 'a@ya.com'
    assert ma.first_name == 'a'
    assert ma.last_name == 'b'


def test_mail_address_add_existing(client):
    ma = factories.MailAddress()
    resp = client.post(url_for('misc.mails-add'), dict(
        mail=ma.mail, first_name='a', last_name='b'))
    assert resp.status_code == 200
    assert resp.body == 'false'
    assert len(MailAddress.query.all()) == 1


def test_mail_address_edit_existing_with_existing(client):
    ma = factories.MailAddress()
    ma2 = factories.MailAddress(mail='old@old.com')
    resp = client.post(url_for('misc.mails-edit'), dict(
        old_mail=ma2.mail, mail=ma.mail, first_name='a', last_name='b'))
    assert resp.status_code == 200
    assert resp.body == 'false'
    assert MailAddress.query.all()[1].mail == ma2.mail


def test_mail_address_edit_nonexisting(client):
    ma = factories.MailAddress()
    resp = client.post(url_for('misc.mails-edit'), dict(
        old_mail='non@existing.com', mail='m', first_name='a', last_name='b'))
    assert resp.status_code == 200
    assert resp.body == 'false'
    assert len(MailAddress.query.all()) == 1
    assert MailAddress.query.all()[0].mail == ma.mail


def test_mail_address_edit_with_new(client):
    ma = factories.MailAddress()
    resp = client.post(url_for('misc.mails-edit'), dict(
        old_mail=ma.mail, mail='new@new.com', first_name='x', last_name='y'))
    assert resp.status_code == 200
    assert resp.body == 'true'
    assert len(MailAddress.query.all()) == 1
    assert MailAddress.query.all()[0].mail == 'new@new.com'
    assert MailAddress.query.all()[0].first_name == 'x'
    assert MailAddress.query.all()[0].last_name == 'y'


def test_mail_address_delete_existing(client):
    ma = factories.MailAddress()
    resp = client.post(url_for('misc.mails-delete'), dict(mail=ma.mail))
    assert resp.status_code == 200
    assert resp.body == 'true'
    assert len(MailAddress.query.all()) == 0


def test_mail_address_delete_nonexisting(client):
    factories.MailAddress()
    resp = client.post(url_for('misc.mails-delete'),
                       dict(mail='non@existing.com'))
    assert resp.status_code == 200
    assert resp.body == 'false'
    assert len(MailAddress.query.all()) == 1
