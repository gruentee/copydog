# -*- coding: utf-8 -*-
from logging import getLogger

log = getLogger('copydog')


class Mapper(object):
    """
        TODO: remove hardcoded services
    """

    def __init__(self, storage, services, config=None):
        self.config = config
        self.storage = storage
        self.services = services

    def save_list_status_mapping(self):
        """ TODO: Optimize lookup
        """
        statuses = list(self.services['bitbucket'].client.states())
        lists = list(self.services['trello'].client.lists(self.config.clients.trello.board_id))
        mapping = self.config.status_to_list_mapping

        for status in statuses:
            trello_list = self.config.status_to_list_mapping.get(status.name)
            if trello_list:
                self.storage.set_list_or_status_id(bitbucket_id=status.name, trello_id=mapping[status.name])
            else:
                self.storage.set_list_or_status_id(bitbucket_id=status.name, trello_id=mapping['new'])
            # for trello_list in lists:
            #     if self.config.status_to_list_mapping.get(status.name) == trello_list.id:
            #         self.storage.set_list_or_status_id(bitbucket_id=status.id, trello_id=trello_list.id)
            #         log.debug('Mapped Status %s to Trello', status.name)
            #         break
            #     else:
            #         self.storage.set_list_or_status_id(bitbucket_id=status.id, trello_id=
            #             self.config.status_to_list_mapping.get('new'))
            #         log.debug('Status %s not mapped to Trello', status.name)

    def save_user_member_mapping(self):
        users = list(self.services['bitbucket'].client.members(self.config.clients.bitbucket.team))
        members = list(self.services['trello'].client.members(self.config.clients.trello.board_id))
        for user in users:
            for member in members:
                if user.username == member.username or user.display_name == member.fullName:
                    self.storage.set_user_or_member_id(bitbucket_id=user.id, trello_id=member.id)
                    log.debug('Mapped User %s to Trello', user.username)
                    break
            else:
                log.debug('User %s not mapped to Trello', user.username)