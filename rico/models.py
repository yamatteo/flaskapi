
import random
from typing import List, Literal, Optional
import uuid
from attr import define
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from .engine.game import Game as GameData

class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)

class DbGame(db.Model):
    __tablename__ = "dbgame"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(8), default="open", nullable=False)
    action_counter: Mapped[int] = mapped_column(Integer, default=0)
    # expected_user: Mapped[str] = mapped_column(String(80), nullable=True)
    data: Mapped[str] = mapped_column(String, nullable=True)

    users: Mapped[List["DbUser"]] = relationship()

    def __repr__(self):
        return f"<DbGame: {self.name}>"

    @classmethod
    def new(cls) -> "DbGame":
        name = None
        while name is None:
            name = generate_random_name()
            prev_game = db.session.query(cls).filter(cls.name == name).first()
            if prev_game is not None:
                name = None
        game = cls(name=name)
        db.session.add(game)
        db.session.commit()
        db.session.refresh(game)
        return game
    
    def start(self):
        assert self.status == "open"
        assert 3 <= len(self.users) <= 5
        self.status = "active"
        game = ActiveGame.start([user.name for user in self.users], self.id, self.name)
        # self.expected_user = game.expected.name
        for user in self.users:
            user.pseudo = game.pseudos[user.name]
        self.data = game.dumps()
        db.session.commit()
        return game

    def update(self, active_game: GameData):
        self.data = active_game.dumps()
        self.action_counter = len(active_game.past_actions)
        db.session.commit()
        db.session.refresh(self)
        return self


class DbUser(db.Model):
    __tablename__ = "dbuser"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    pseudo: Mapped[str] = mapped_column(String(2), nullable=True)
    password: Mapped[str] = mapped_column(String(80), nullable=False)
    token: Mapped[str] = mapped_column(String(16), nullable=False)

    game_id: Mapped[int] = mapped_column(ForeignKey("dbgame.id"))

    @property
    def dbgame(self):
        return db.session.get(DbGame, self.game_id)

    @classmethod
    def new(cls, name: str, password: str, game_id: int) -> "DbUser":

        user = cls(
            name=name,
            password=password,
            token=uuid.uuid4().hex.upper()[:16],
            game_id=game_id,
        )
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        return user

@define
class ActiveGame(GameData):
    id: int = None
    name: str = None

    @classmethod
    def start(cls, usernames, id, name):
        self = super().start(usernames)
        self.id = id
        self.name = name
        return self












class Game(db.Model, GameData):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(8), default="open", nullable=False)
    action_counter: Mapped[int] = mapped_column(Integer, default=0)
    expected_user: Mapped[str] = mapped_column(String(80), nullable=True)
    dumped_data: Mapped[str] = mapped_column(String, nullable=True)

    users: Mapped[List["User"]] = relationship()

    def __repr__(self):
        return f"<Game: {self.name}>"
    
    @classmethod
    def browse(cls, name=None, status=None):
        items = db.session.query(cls)
        if name:
            items = items.filter(cls.name == name)
        if status:
            items = items.filter(cls.status == status)
        return items.all()

    @classmethod
    def add(cls) -> "Game":
        name = None
        while name is None:
            name = generate_random_name()
            prev_game = db.session.query(cls).filter(cls.name == name).first()
            if prev_game is not None:
                name = None
        game = cls(name=name)
        db.session.add(game)
        db.session.commit()
        db.session.refresh(game)
        return game

    def updated(self, gd: Optional[GameData] = None) -> "Game":
        if gd is None:
            self.dumped_data = None
            self.expected_user = None
        self.dumped_data = gd.dumps()
        self.expected_user = gd.expected.name
        self.action_counter = len(gd.past_actions)
        db.session.commit()
        db.session.refresh(self)
        return self

    def start(self):
        assert self.status == "open"
        assert 3 <= len(self.users) <= 5
        self.status = "active"
        game_data = GameData.start([user.name for user in self.users])
        self.expected_user = game_data.expected.name
        self.dumped_data = game_data.dumps()
        db.session.commit()


class User(UserMixin, db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    password: Mapped[str] = mapped_column(String(80), nullable=False)
    token: Mapped[str] = mapped_column(String(16), nullable=False)

    game_id: Mapped[int] = mapped_column(ForeignKey("game.id"))

    @property
    def game(self):
        return db.session.get(Game, self.game_id)

    def __repr__(self):
        return f"User[{self.id}]({self.name}, ***, ***, {self.game_id})"

    @classmethod
    def add(cls, name: str, password: str, game_id: int) -> "User":

        user = cls(
            name=name,
            password=password,
            token=uuid.uuid4().hex.upper()[:16],
            game_id=game_id,
        )
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        return user

    def get_id(self):
        return str(self.id)
    


def generate_random_name():
    # List of plausible South American town names
    towns = [
        "Villarrica",
        "Valparaíso",
        "Santa Cruz",
        "Punta Arenas",
        "Potosí",
        "Maracaibo",
        "Guayaquil",
        "Cuenca",
        "Cuzco",
        "Bariloche",
        "Cartagena",
        "Mendoza",
        "Córdoba",
        "Salta",
        "Ushuaia",
        "Iquitos",
        "Arequipa",
        "Trujillo",
        "Chiclayo",
        "Huaraz",
        "Isla Margarita",
        "Puerto La Cruz",
        "Puerto Cabello",
        "Merida",
        "San Cristóbal",
        "Quito",
        "Guayaquil",
        "Cuenca",
        "Loja",
        "Machala",
        "Manta",
        "San José",
        "Antigua",
        "San Salvador",
        "Tegucigalpa",
        "Managua",
        "Ciudad de Panamá",
        "Cancún",
        "Mérida",
    ]

    # List of country names from South America
    countries = [
        "Argentina",
        "Bolivia",
        "Brasil",
        "Chile",
        "Colombia",
        "Ecuador",
        "Guyana",
        "Paraguay",
        "Perú",
        "Uruguay",
        "Venezuela",
        "Costa Rica",
        "El Salvador",
        "Guatemala",
        "Honduras",
        "Nicaragua",
        "Panamá",
        "México",
    ]
    random_year = random.randint(1578, 1624)
    random_town = random.choice(towns)
    random_country = random.choice(countries)

    return f"{random_town}, {random_country}, {random_year} A.D."
