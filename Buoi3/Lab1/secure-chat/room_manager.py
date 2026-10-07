import re
import threading


class RoomManager:
    def __init__(self):
        self.rooms = {}
        self.lock = threading.RLock()

    def join_room(self, room, sock):
        if not isinstance(room, str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,32}', room):
            raise ValueError('Room name: 1-32 letters, digits, _ or -')
        with self.lock:
            self.leave(sock)
            self.rooms.setdefault(room, set()).add(sock)

    def leave(self, sock):
        with self.lock:
            for room in list(self.rooms):
                self.rooms[room].discard(sock)
                if not self.rooms[room]:
                    del self.rooms[room]

    def members(self, room):
        with self.lock:
            return list(self.rooms.get(room, set()))
