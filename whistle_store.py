import datetime
import json
import os
from typing import Dict, List
import asyncio
from hashlib import sha256

WLSTORE_FILENAME = "store.json"

INITIAL_DATA = {
    "whitelist": {
        "example_user": {
            "pretty": "Example User",
            "session_limit": 0,
            "sessions": [],
            "roles": [],
        }
    }
}


class User:
    username: str
    pretty: str
    roles: List[int]
    __session_limit: int
    __sessions: List[int]

    def __init__(self, username: str, data: Dict):
        self.username = username
        self.pretty = data.get("pretty", username)
        self.roles = data.get("roles", [])
        self.__session_limit = data.get("session_limit", 1)
        self.__sessions = data.get("sessions", [])

    def jsonify(self) -> Dict:
        return {
            "pretty": self.pretty,
            "roles": self.roles,
            "session_limit": self.__session_limit,
            "sessions": self.__sessions,
        }

    def create_session(self, session_id: int):
        if session_id in self.__sessions:
            return
        if (len(self.__sessions) + 1) > self.__session_limit:
            raise Exception(
                f"Session limit reached - Cannot create session {session_id}"
            )
        self.__sessions.append(session_id)

    def drop_session(self, session_id: int):
        try:
            self.__sessions.remove(session_id)
        except ValueError:
            return

    def list_sessions(self) -> List[int]:
        return self.__sessions

    def drop_all_sessions(self):
        self.__sessions = []

    def get_session_limit(self) -> int:
        return self.__session_limit

    def set_session_limit(self, limit: int):
        self.__session_limit = limit
        if len(self.__sessions) > self.__session_limit:
            self.__sessions = self.__sessions[0 : self.__session_limit]


class Whitelist:
    __users: List[User]

    def __init__(self, data: Dict):
        self.__users = {
            username: User(username, user_data) for username, user_data in data.items()
        }

    def jsonify(self) -> Dict:
        return {
            username: user_obj.jsonify() for username, user_obj in self.__users.items()
        }

    def get_session(self, session_id: int) -> User | None:
        for user in self.__users.values():
            if session_id in user.list_sessions():
                return user.username
        return None

    def get_user(self, username: str) -> User | None:
        return self.__users.get(username, None)

    def add_user(
        self,
        username: str,
        pretty: str = None,
        max_sessions: int = 1,
        sessions: List[int] = [],
        roles: List[int] = [],
    ) -> None:
        self.__users[username] = User(
            username,
            {
                "pretty": pretty if pretty else username,
                "session_limit": max_sessions,
                "sessions": sessions,
                "roles": roles,
            },
        )

    def list_users(self) -> Dict:
        return {username: user.jsonify() for username, user in self.__users.items()}

    def get_users(self) -> List[User]:
        return {username: user for username, user in self.__users.items()}

    def remove_user(self, username: str):
        self.__users.pop(username, None)

    def remove_all_users(self):
        self.__users = []


class wlStore:
    __file_path: str
    __data: Dict
    last_update: datetime.datetime
    last_save: datetime.datetime

    def __init__(self, file_name):
        self.__file_path = file_name
        self.load()

    def reload(self):
        self.save()
        self.load()

    def save(self):
        self.save_store(self.__file_path, self.jsonify())
        self.last_save = datetime.datetime.now()

    def load(self):
        json_data = self.load_store(self.__file_path)
        self.__data = self.from_json(json_data)
        self.last_update = datetime.datetime.now()

    def jsonify(self):
        return {"whitelist": self.__data.get("whitelist").jsonify()}

    def get_whitelist(self) -> Whitelist | None:
        return self.__data.get("whitelist", None)

    @staticmethod
    def from_json(json_data: Dict) -> Dict:
        return {"whitelist": Whitelist(json_data.get("whitelist"))}

    @staticmethod
    def create_initial_store(file_path):
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(INITIAL_DATA, file)

    @staticmethod
    def load_store(file_path):
        if not os.path.exists(file_path):
            wlStore.create_initial_store(file_path)
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError:
            wlStore.create_initial_store(file_path)
            return wlStore.load_store(file_path)

    @staticmethod
    def save_store(file_path, data):
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file)
            file.flush()
            file.close()

    async def autosaver(self):
        data_hash = lambda x: sha256(str(x).encode("utf-8")).hexdigest()
        last_save_hash = None
        print("Auto saver -- Loop initializing!")
        while 1:
            current_save_hash = data_hash(self.jsonify())
            print(
                f"Auto saver -- (Current) {current_save_hash}\n              (Last)    {last_save_hash}"
            )
            if current_save_hash != last_save_hash:
                self.save()
                last_save_hash = current_save_hash
                print("Auto saver -- Saved!")
            print("Auto saver -- Waiting for next itteration...")
            await asyncio.sleep(120)
        print("Auto saver -- Loop terminated!")
