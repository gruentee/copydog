import requests
from requests.auth import _basic_auth_str
from urlparse import urlparse, parse_qs
import json

from .base import ApiObject, ApiClient, ApiException


class BitbucketException(ApiException):
    """Bitbucket API Exception"""


class Bitbucket(ApiClient):
    """Bitbucket API class"""
    service_name = 'bitbucket'
    _versions = [1.0, 2.0]
    __version = None

    def __init__(self, username=None, password=None):
        self.username = username
        self.password = password
        self.host = 'https://api.bitbucket.org/'
        self.version = 2.0

    @property
    def version(self):
        return self.__version

    @version.setter
    def version(self, version):
        if version in self._versions:
            self.__version = version
        else:
            raise BitbucketException("API version {version} doesn't exist. Possible values: {versions}".format(
                version=self.version, versions=self._versions
            ))

    def build_api_url(self, path=''):
        return '{host}/{version}/{path}'.format(host=self.host.strip('/'), version=self.version, path=path)

    def method(self, method, path, data=None, headers=None, expect_json=True, **payload):
        # Add authorization headers neccessary for Bitbucket
        auth = {'Authorization': _basic_auth_str(self.username, self.password)}
        headers = headers.update(auth) if headers else auth
        headers.update({'Content-Type': 'application/json'})
        return super(Bitbucket, self).method(method, path, data, headers, expect_json, **payload)

    def get_many(self, path, **payload):
        data = self.method('get', path, **payload)
        for item in data['values']:
            yield item
        # fetch remaining pages if present
        while data.get('next'):
            parsed_url = urlparse(data['next'])
            payload.update(parse_qs(parsed_url.query))
            data = self.method('get', path, **payload)
            for item in data['values']:
                yield item

    def issues(self, repository, updated__after=None, **kwargs):
        """ Get a list of issues"""
        if updated__after:
            kwargs['updated_on'] = '>={0}'.format(updated__after.date().isoformat())

        for data in self.get_many('repositories/{repository}/issues'.format(repository=repository), **kwargs):
            yield Issue(self, **data)

    def pullrequests(self, repository, **kwargs):
        """Get a list of pull requests"""
        for data in self.get_many('repositories/{repository}/pullrequests'.format(repository=repository), **kwargs):
            # TODO: maybe fix constructor to take unformatted JSON response
            yield PullRequest(self, repository_src=data['source']['repository']['full_name'],
                              branch_src=data['source']['branch']['name'],
                              branch_dest=data['destination']['branch']['name'],
                              **data)

    def members(self, team):
        """Get team members for specified team

        :param string team: Name or UUID of the team of which to fetch members"""
        for data in self.get_many('teams/{team}/members'.format(team=team)):
            yield Member(self, **data)

    def states(self):
        # TODO: remove hard-coded statuses?
        states = ['new', 'open', 'resolved', 'on hold', 'invalid', 'duplicate', 'wontfix', 'closed']
        for idx, name in enumerate(states):
            yield State(self, id=idx, name=name)


class State(ApiObject):
    """Issue status object
        TODO: maybe move -> Issue"""
    pass


class Issue(ApiObject):
    """API Issue object
    TODO: implement comments"""
    created = False
    date_fields = ('created_on', 'updated_on')

    def get_url(self):
        return self.links['html']['href']

    def validate(self):
        assert self.title is not None, "Issue title cannot be empty"
        assert self.repository is not None, "You must specify a repository to post the issue to"

    def save(self):
        """Save an issue"""
        self.validate()
        repository = self._data.pop('repository', None)
        if self.get('id'):
            self.client.version = 1.0
            # As BB API v2 doesn't allow PUT for issues we have to use API v.1
            # API v1.0 id is named issue_id
            self._data['issue_id'] = self._data.pop('id')
            result = self.client.put('repositories/{repository}/issues/{issue_id}'.format(
                repository=repository,
                issue_id=self.issue_id),
                data=self._data
            )
            # argh! API v1.0 returned identifier key is now local_id
            result['id'] = result.pop('local_id')
            self.client.version = 2.0
        else:
            result = self.client.post('repositories/{repository}/issues'.format(repository=repository), self._data)
        self._data = result
        return self

    @property
    def last_updated(self):
        return self.updated_on


class PullRequest(ApiObject):
    """A Bitbucket pull request"""

    # def __init__(self, client, **data):
    #     super().__init__(client=client, **data)

    def validate(self):
        assert self.title is not None, "Pull request title cannot be empty"
        assert self.repository_src is not None, "Source repository cannot be empty"
        assert self.branch_src is not None, "Source branch cannot be empty"
        assert self.branch_dest, "Destination branch cannot be empty"

    def save(self):
        """Save a pull request"""
        self.validate()
        self._data['source'] = {'branch': {'name': self._data.pop('branch_src')}}
        self._data['destination'] = {'branch': {'name': self._data.pop('branch_dest')}}
        repository_src = self._data.pop('repository_src')
        result = self.client.post('repositories/{repository}/pullrequests'.format(repository=repository_src),
                                  self._data)
        self._data = result
        return self


class Member(ApiObject):
    """API team Member object"""
    pass
