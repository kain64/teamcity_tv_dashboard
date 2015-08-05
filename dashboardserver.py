import re
from datetime import datetime, timezone
import jsonpickle
import requests
from flask import Flask
from dateutil.parser import parse

from crossdomain import crossdomain

TEAM_CITY_URL = XXXX #example 'http://portal:9090'

app = Flask(__name__)


class Dashboard:
    def __init__(self):
        self.builds = list()


class Build:
    def __init__(self):
        self.build_id = ""
        self.investigator = ""
        self.status_img_url = ""
        self.status = ""
        self.assignment_timestamp = ""


class Generator:
    def __init__(self, base_url):
        self.base_url = base_url

    def get_data_from_url(self, sub_url):
        headers = {'accept': 'application/json'}
        resp = requests.get(url=self.base_url + sub_url, headers=headers)
        return resp.json()

    def generate(self):
        jsondata = self.get_data_from_url('/guestAuth/app/rest/investigations')
        taken_investigations_list = filter(lambda x: x['state'] in ['TAKEN', 'FIXED'], jsondata['investigation'])
        taken_investigations_dict = {self.parse_id(x['id']): x for x in taken_investigations_list}
        build_types = self.get_data_from_url('/guestAuth/app/rest/buildTypes')
        dashboard = Dashboard()
        for build_type in build_types['buildType']:
            build = Build()
            build.build_id = build_type['id']
            if build.build_id in taken_investigations_dict:
                build.investigator = taken_investigations_dict[build.build_id]['assignee']['name']
                if taken_investigations_dict[build.build_id]['state'] == 'FIXED':
                    build.investigator = 'Marked as "Fixed" by: ' + build.investigator
                else:
                    str_timestamp = taken_investigations_dict[build.build_id]['assignment']['timestamp']
                    assign_timestamp = parse(str_timestamp)
                    nowt = datetime.now(timezone.utc)
                    timegap = nowt - assign_timestamp
                    build.investigator = build.investigator + ': Assigned:' + str(timegap) + ' time ago'
                    build.assignment_timestamp = assign_timestamp

            build.status_img_url = self.base_url + '/app/rest/builds/buildType:(id:' + build.build_id + ')/statusIcon'
            build.status = self.get_data_from_url('/guestAuth/app/rest/builds/buildType:(id:' + build.build_id + ')')[
                'status']
            dashboard.builds.append(build)

        return jsonpickle.encode(dashboard, unpicklable=False)

    @staticmethod
    def parse_id(id_str):
        match = re.search('buildType:\(id:(.*)\)', id_str)
        if match:
            return match.groups(1)[0]
        return id_str


@app.route('/getbuildsstatus')
@crossdomain(origin='*')
def get_buildstatus():
    gen = Generator('%s' % TEAM_CITY_URL)
    return gen.generate()


if __name__ == "__main__":
    app.run(port=500, host='127.0.0.1')
