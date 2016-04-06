import json
import os

import gevent
import pytest
from py.test import raises

from volttron.platform import jsonrpc
from volttron.platform.auth import (AuthEntry, AuthFile, AuthFileIndexError,
                                    AuthFileEntryAlreadyExists,
                                    AuthEntryInvalid)


@pytest.fixture(scope='function')
def auth_file_platform_tuple(volttron_instance1_encrypt):
    platform = volttron_instance1_encrypt
    auth_file = AuthFile(os.path.join(platform.volttron_home, 'auth.json'))

    allow_entries, groups, roles = auth_file.read()
    gevent.sleep(0.5)
    return auth_file, platform


@pytest.fixture(scope='module')
def auth_entry_only_creds():
    return AuthEntry(credentials='CURVE:'+'B'*43)


@pytest.fixture(scope='module')
def auth_entry1():
    return AuthEntry(domain='domain1', address='tcp://127.0.0.1',
                     credentials='NULL', user_id='user1', groups=['group1'],
                     roles=['role1'], capabilities=['cap1'], comments='com1',
                     enabled=True)


@pytest.fixture(scope='module')
def auth_entry2():
    return AuthEntry(domain='domain2', address='tcp://127.0.0.2',
                     credentials='CURVE:' + 'A'*43,
                     user_id='user2', groups=['group2'], roles=['role2'],
                     capabilities=['cap2'], comments='com2', enabled=False)


@pytest.fixture(scope='module')
def auth_entry3():
    return AuthEntry(domain='domain3', address='tcp://127.0.0.3',
                     credentials='CURVE:' + 'B'*43,
                     user_id='user3', groups=['group3'], roles=['role3'],
                     capabilities=['cap3'], comments='com3', enabled=False)


@pytest.mark.auth
def test_auth_file_overwrite(auth_file_platform_tuple, auth_entry_only_creds):
    authfile, platform = auth_file_platform_tuple
    authfile.add(auth_entry_only_creds)
    authfile.add(auth_entry_only_creds)
    with raises(AuthFileEntryAlreadyExists):
        authfile.add(auth_entry_only_creds, False)


@pytest.mark.auth
def test_auth_file_api(auth_file_platform_tuple, auth_entry1,
                       auth_entry2, auth_entry3):
    auth_file, platform = auth_file_platform_tuple

    # add entries
    auth_file.add(auth_entry1)
    auth_file.add(auth_entry2)
    entries = auth_file.read_allow_entries()
    entries_len = len(entries)
    assert entries_len >= 2

    # update entries
    auth_file.update_by_index(auth_entry3, 0)
    entries = auth_file.read_allow_entries()
    assert entries_len == len(entries)

    # remove entries
    auth_file.remove_by_index(1)
    entries = auth_file.read_allow_entries()
    assert entries_len - 1 == len(entries)


@pytest.mark.auth
def test_remove_invalid_index(auth_file_platform_tuple):
    auth_file, _ = auth_file_platform_tuple
    with pytest.raises(AuthFileIndexError):
        auth_file.remove_by_index(1)


@pytest.mark.auth
def test_update_invalid_index(auth_file_platform_tuple, auth_entry1):
    auth_file, _ = auth_file_platform_tuple
    with pytest.raises(AuthFileIndexError):
        auth_file.update_by_index(auth_entry1, 1)


@pytest.mark.auth
def test_invalid_auth_entries(auth_file_platform_tuple):
    auth_file, _ = auth_file_platform_tuple
    with pytest.raises(AuthEntryInvalid):
        AuthEntry()
    with pytest.raises(AuthEntryInvalid):
        AuthEntry(credentials='CURVE:invalid key')
    with pytest.raises(AuthEntryInvalid):
        AuthEntry(credentials='Not NULL or PLAIN: or CURVE:')


@pytest.mark.auth
def test_find_by_credentials(auth_file_platform_tuple):
    auth_file = auth_file_platform_tuple[0]
    cred1 = 'CURVE:' + 'A'*43
    cred2 = 'CURVE:' + 'B'*43
    auth_file.add(AuthEntry(domain='test1', credentials=cred1))
    auth_file.add(AuthEntry(domain='test2', credentials=cred1))
    auth_file.add(AuthEntry(domain='test3', credentials=cred2))

    # find non-regex creds
    results = auth_file.find_by_credentials(cred1)
    assert len(results) == 2
    domains = [entry.domain for entry in results]
    assert 'test1' in domains and 'test2' in domains

    # try to find non-existing creds
    results = auth_file.find_by_credentials('CURVE:' + 'C'*43)
    assert len(results) == 0
