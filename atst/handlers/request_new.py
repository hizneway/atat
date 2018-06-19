import tornado
from atst.handler import BaseHandler
from atst.forms.request import RequestForm
from atst.forms.organization_info import OrganizationInfoForm
from atst.forms.funding import FundingForm
from atst.forms.readiness import ReadinessForm
from atst.forms.review import ReviewForm
import tornado.httputil
from tornado.httpclient import HTTPError


class RequestNew(BaseHandler):
    screens = [
            { 'title' : 'Details of Use',
              'form'  : RequestForm,
              'subitems' : [
                {'title' : 'Application Details',
                 'id' : 'application-details'},
                {'title' : 'Computation',
                  'id' : 'computation' },
                {'title' : 'Storage',
                  'id' : 'storage' },
                {'title' : 'Usage',
                  'id' : 'usage' },
            ]},
            {
                'title' : 'Organizational Info',
                'form'  : OrganizationInfoForm,
            },
            {
                'title' : 'Funding/Contracting',
                'form'  : FundingForm,
            },
            {
                'title' : 'Readiness Survey',
                'form'  : ReadinessForm,
            },
            {
                'title' : 'Review & Submit',
                'form'  : ReviewForm,
            }
     ]

    def initialize(self, page, requests_client):
        self.page = page
        self.requests_client = requests_client

    @tornado.web.authenticated
    @tornado.gen.coroutine
    def post(self, screen=1, request_id=None):
        self.check_xsrf_cookie()
        screen = int(screen)
        form = self.screens[ screen - 1 ]['form'](self.request.arguments)
        if form.validate():
            response = yield self.create_or_update_request(form.data, request_id)
            if response.ok:
                where = self.application.default_router.reverse_url(
                    'request_form_update', str(screen + 1), request_id or response.json['id'])
                self.redirect(where)
            else:
                self.set_status(response.code)
        else:
            self.show_form(screen, form)

    @tornado.web.authenticated
    @tornado.gen.coroutine
    def get(self, screen=1, request_id=None):
        form = None
        if request_id:
            request = yield self.get_request(request_id)
            form_data = request['body'] if request else {}
            form = self.screens[ int(screen) - 1 ]['form'](data=form_data)
        self.show_form(screen=screen, request_id=request_id, form=form)

    def show_form(self, screen=1, request_id=None, form=None):
        if not form:
            form = self.screens[ int(screen) - 1 ]['form'](self.request.arguments)
        self.render('requests/screen-%d.html.to' % int(screen),
                    f=form,
                    page=self.page,
                    screens=self.screens,
                    current=int(screen),
                    next_screen=int(screen) + 1,
                    request_id=request_id)

    @tornado.gen.coroutine
    def get_request(self, request_id):
        try:
            request = yield self.requests_client.get('/requests/{}'.format(request_id))
        except HTTPError:
            request = None
        return request.json

    @tornado.gen.coroutine
    def create_or_update_request(self, form_data, request_id=None):
        request_data = {
            'creator_id': '9cb348f0-8102-4962-88c4-dac8180c904c',
            'request': form_data
        }
        if request_id:
            response = yield self.requests_client.patch(
                '/requests/{}'.format(request_id), json=request_data)
        else:
            response = yield self.requests_client.post(
                '/requests', json=request_data)
        return response
