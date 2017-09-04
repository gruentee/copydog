import os
from unittest import TestCase
import vcr

from copydog.api.bitbucket import Bitbucket, Issue, PullRequest, BitbucketException


my_vcr = vcr.VCR(
    cassette_library_dir='fixtures/cassettes',
    filter_headers=['Authorization']
)


def make_client():
    username, password = os.getenv('BITBUCKET_USERNAME'), os.getenv('BITBUCKET_PASSWORD')
    return Bitbucket(username, password)


class TestBitbucket(TestCase):
    def setUp(self):
        self.client = make_client()
        self.repo = os.getenv('BITBUCKET_REPO')

    @my_vcr.use_cassette()
    def test_issues(self):
        issues = self.client.issues('{repo}'.format(repo=self.repo))
        for i in issues:
            self.assertTrue(next(issues), Issue)


    @my_vcr.use_cassette()
    def test_api_version(self):
        default = 2.0
        self.assertEqual(self.client.version, default)
        self.client.version = 1
        self.assertEqual(self.client.version, 1)
        invalid = 99
        with self.assertRaises(BitbucketException):
            self.client.version = invalid


class TestIssue(TestCase):
    def setUp(self):
        self.client = make_client()
        self.repo = os.getenv('BITBUCKET_REPO')

    @my_vcr.use_cassette()
    def test_save_issue(self):
        title = 'A test issue'
        i = Issue(client=self.client, title=title, repository=self.repo)
        # POST
        i.save()
        inserted = next(self.client.issues('{repo}'.format(repo=self.repo), q='title="{title}"'.format(title=title)))
        self.assertEqual(inserted.title, i.title)
        # PUT
        content = 'Test issue content'
        new = Issue(
            client=self.client, repository=self.repo, id=inserted.id, title=title, content=content
        )
        new.save()
        changed = next(self.client.issues('{repo}'.format(repo=self.repo), q='title="{title}"'.format(title=title)))
        self.assertEqual(changed.content.get('raw'), content)


class TestPullRequest(TestCase):
    def setUp(self):
        self.client = make_client()
        self.repo = os.getenv('BITBUCKET_REPO')

    @my_vcr.use_cassette()
    def test_save_pull_request(self):
        title = "A test pull request"
        pr = PullRequest(client=self.client, title=title, repository_src=self.repo, branch_src='feature-task-2',
                         branch_dest='master')
        pr.save()
        created = next(
            self.client.pullrequests('{repo}'.format(repo=self.repo), q='title="{title}"'.format(title=title)))
        self.assertEqual(pr.title, created.title)
