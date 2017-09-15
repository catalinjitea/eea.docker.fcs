from pytest import fixture
from flask.ext.webtest import TestApp
from fcs.app import create_app
from fcs.models import db
from fcs.models import loaddata

TEST_CONFIG = {
    'DEBUG': True,
    'SERVER_NAME': 'noname',
    'BDR_ENDPOINT_URL': '',
    'BDR_ENDPOINT_USER': 'user',
    'BDR_ENDPOINT_PASSWORD': 'password',
    'AUTO_VERIFY_NEW_COMPANIES': True,
}


def create_testing_app():
    test_config = dict(TEST_CONFIG)

    app = create_app(test_config)
    return app


@fixture
def app(request):
    app = create_testing_app()
    app_context = app.app_context()
    app_context.push()
    db.create_all()
    loaddata('fcs/fixtures/types.json')

    @request.addfinalizer
    def fin():
        app_context.pop()

    return app


@fixture
def client(app):
    client = TestApp(app)
    return client
