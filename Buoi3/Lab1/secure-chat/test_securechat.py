import os
import socket
import threading
import pytest
from cryptography.exceptions import InvalidTag
from message_encryption import MessageEncryption
from protocol import receive, send
from room_manager import RoomManager


def test_random_nonce_and_unicode():
    cipher = MessageEncryption(os.urandom(32))
    a, b = cipher.encrypt('Xin chào'), cipher.encrypt('Xin chào')
    assert a != b
    assert cipher.decrypt(a) == 'Xin chào'


def test_room_binding_and_wrong_key():
    cipher = MessageEncryption(os.urandom(32))
    token = cipher.encrypt('secret', 'study')
    with pytest.raises(InvalidTag):
        cipher.decrypt(token, 'general')
    with pytest.raises(InvalidTag):
        MessageEncryption(os.urandom(32)).decrypt(token, 'study')


def test_frames_larger_than_recv_and_back_to_back():
    a, b = socket.socketpair()
    def writer():
        send(a, {'text': 'x' * 16000}); send(a, {'text': 'next'})
    thread = threading.Thread(target=writer)
    thread.start()
    try:
        assert receive(b) == {'text': 'x' * 16000}
        assert receive(b) == {'text': 'next'}
    finally:
        thread.join(2); a.close(); b.close()


def test_room_switch_removes_previous_membership():
    manager = RoomManager()
    manager.join_room('general', 'client')
    manager.join_room('study', 'client')
    assert manager.members('general') == []
    assert manager.members('study') == ['client']
    manager.leave('client')
    assert not manager.rooms
