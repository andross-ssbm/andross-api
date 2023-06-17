import os
from datetime import datetime
from typing import Optional

from sqlalchemy import DDL, event
from flask_sqlalchemy import SQLAlchemy
from slippi.slippi_characters import SlippiCharacterId

# Database variables
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'

    id: db.Mapped[int] = db.db.Column(db.BigInteger, primary_key=True)
    cc: db.Mapped[str] = db.Column(db.String(10), unique=True, nullable=False)
    name: db.Mapped[str] = db.Column(db.String(14), nullable=False)
    main_id: db.Mapped[int] = db.Column(db.Integer, db.ForeignKey('character_list.id'), server_default='256',
                                        default=256)
    slippi_id: db.Mapped[int] = db.Column(db.BigInteger, server_default='0', default=0)
    latest_elo: db.Mapped[float] = db.Column(db.Double, nullable=False,
                                             server_default='1100.0', default=0)
    latest_wins: db.Mapped[int] = db.Column(db.Integer, nullable=False, server_default='0', default=0)
    latest_losses: db.Mapped[int] = db.Column(db.Integer, nullable=False, server_default='0', default=0)
    latest_dgp: db.Mapped[int] = db.Column(db.Integer, nullable=False, server_default='0', default=0)
    latest_drp: db.Mapped[int] = db.Column(db.Integer, nullable=False, server_default='0', default=0)

    main_character: db.Mapped['CharacterList'] = db.db.relationship('CharacterList', lazy='joined')
    elo_entries: db.Mapped[list['Elo']] = db.relationship('Elo')
    win_loss_entries: db.Mapped[list['WinLoss']] = db.relationship('WinLoss')
    drp_entries: db.Mapped[list['DRP']] = db.relationship('DRP')
    dgp_entries: db.Mapped[list['DGP']] = db.relationship('DGP')
    characters_entries: db.Mapped[list['CharactersEntry']] = db.relationship('CharactersEntry')
    leaderboard_entries: db.Mapped[list['Leaderboard']] = db.relationship('Leaderboard')

    __table_args__ = (
        db.db.Index('idx_users_id', id),
        db.Index('idx_users_cc', cc),
        db.Index('idx_users_slippi_id', slippi_id)
    )

    def __repr__(self):
        return f'User({self.id}, "{self.cc}", "{self.name}", {self.main_id}("{self.main_character.name}"), ' \
               f'{self.slippi_id}, {self.latest_elo}, ({self.latest_wins}/{self.latest_losses}) )'

    def to_dict(self):
        return {
            'id': self.id,
            'cc': self.cc,
            'name': self.name,
            'main_id': self.main_id,
            'slippi_id': self.slippi_id,
            'latest_elo': self.latest_elo,
            'latest_wins': self.latest_wins,
            'latest_losses': self.latest_losses,
            'latest_dgp': self.latest_dgp,
            'latest_drp': self.latest_drp
        }

    def get_latest_characters(self) -> Optional['CharactersEntry']:
        latest_character = db.session.query(CharactersEntry) \
            .where(CharactersEntry.user_id == self.id).order_by(CharactersEntry.entry_time.desc()).first()
        if not latest_character:
            return None

        latest_characters_entries = db.session.query(CharactersEntry) \
            .where(
            db.and_(CharactersEntry.user_id == self.id, CharactersEntry.entry_time == latest_character.entry_time)) \
            .order_by(CharactersEntry.game_count.desc()).all()
        if not latest_characters_entries:
            return None

        return latest_characters_entries

    def get_latest_characters_fast(self) -> Optional[dict]:
        sql_query = '''SELECT ce.*, cl.name
FROM public.character_entry ce
LEFT JOIN character_list cl ON ce.character_id = cl.id
WHERE ce.user_id = :user_id1
AND ce.entry_time = (
    SELECT MAX(entry_time)
    FROM public.character_entry
    WHERE user_id = :user_id2
)
ORDER BY ce.game_count DESC'''

        characters_list = db.session.execute(db.text(sql_query), {'user_id1': self.id, 'user_id2': self.id}).all()
        if not characters_list:
            return None

        character_return_list = []
        for character in characters_list:
            character_return_list.append(
                {
                    'id': character[0],
                    'user_id': character[1],
                    'character_id': character[2],
                    'game_count': character[3],
                    'entry_time': character[4],
                    'name': character[5],
                }
            )

        return character_return_list


class CharacterList(db.Model):
    __tablename__ = 'character_list'

    id: db.Mapped[int] = db.Column(db.Integer, primary_key=True)
    name: db.Mapped[str] = db.Column(db.String(20), nullable=False)
    character_entries: db.Mapped[list['CharactersEntry']] = db.relationship('CharactersEntry',
                                                                            back_populates='character_info',
                                                                            lazy='select')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
        }


class EntryDate(db.Model):
    __tablename__ = 'entry_date'

    entry_time: db.Mapped[datetime] = db.Column(db.DateTime, primary_key=True,
                                                default=datetime.utcnow())

    def to_dict(self):
        return {
            'entry_time': self.entry_time.strftime("%Y-%m-%d %H:%M:%S.%f"),
        }


class Elo(db.Model):
    __tablename__ = 'elo'

    id: db.Mapped[int] = db.Column(db.BigInteger, primary_key=True)
    user_id: db.Mapped[int] = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False)
    elo: db.Mapped[float] = db.Column(db.Double, nullable=False, server_default='0.0', default=0)
    entry_time: db.Mapped[datetime] = db.Column(db.DateTime, db.ForeignKey('entry_date.entry_time'), nullable=False)

    __table_args__ = (
        db.Index('idx_elo_user_id', user_id),
        db.Index('idx_elo_entry_time', entry_time)
    )

    trigger = DDL("""
            CREATE OR REPLACE FUNCTION update_latest_elo()
            RETURNS TRIGGER AS $$
            BEGIN
              UPDATE users SET latest_elo = NEW.elo WHERE users.id = NEW.user_id;
              RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;

            CREATE TRIGGER update_latest_elo_trigger
            AFTER INSERT OR UPDATE ON elo
            FOR EACH ROW
            EXECUTE FUNCTION update_latest_elo();
        """)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'elo': self.elo,
            'entry_time': self.entry_time.strftime("%Y-%m-%d %H:%M:%S.%f"),
        }


event.listen(Elo.__table__, 'after_create', Elo.trigger)


class WinLoss(db.Model):
    __tablename__ = 'win_loss'

    id: db.Mapped[int] = db.Column(db.BigInteger, primary_key=True)
    user_id: db.Mapped[int] = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False)
    wins: db.Mapped[int] = db.Column(db.Integer, nullable=False, server_default='0', default=0)
    losses: db.Mapped[int] = db.Column(db.Integer, nullable=False, server_default='0', default=0)
    entry_time: db.Mapped[datetime] = db.Column(db.DateTime, db.ForeignKey('entry_date.entry_time'), nullable=False)

    __table_args__ = (
        db.Index('idx_win_loss_user_id', user_id),
        db.Index('idx_win_loss_entry_time', entry_time)
    )

    trigger = DDL("""
                CREATE OR REPLACE FUNCTION update_latest_win_loss()
                RETURNS TRIGGER AS $$
                BEGIN
                  UPDATE users SET latest_wins = NEW.wins WHERE users.id = NEW.user_id;
                  UPDATE users SET latest_losses = NEW.losses WHERE users.id = NEW.user_id;
                  RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;

                CREATE TRIGGER update_latest_win_loss_trigger
                AFTER INSERT OR UPDATE ON win_loss
                FOR EACH ROW
                EXECUTE FUNCTION update_latest_win_loss();
            """)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'wins': self.wins,
            'losses': self.losses,
            'entry_time': self.entry_time.strftime("%Y-%m-%d %H:%M:%S.%f"),
        }


event.listen(WinLoss.__table__, 'after_create', WinLoss.trigger)


class DRP(db.Model):
    __tablename__ = 'daily_regional_placement'

    id: db.Mapped[int] = db.Column(db.BigInteger, primary_key=True)
    user_id: db.Mapped[int] = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False)
    placement: db.Mapped[int] = db.Column(db.Integer, nullable=False, server_default='0', default=0)
    entry_time: db.Mapped[datetime] = db.Column(db.DateTime, db.ForeignKey('entry_date.entry_time'), nullable=False)

    __table_args__ = (
        db.Index('idx_daily_regional_placement_user_id', user_id),
        db.Index('idx_daily_regional_placement_entry_time', entry_time)
    )

    trigger = DDL("""
                CREATE OR REPLACE FUNCTION update_latest_drp()
                RETURNS TRIGGER AS $$
                BEGIN
                  UPDATE users SET latest_drp = NEW.placement WHERE users.id = NEW.user_id;
                  RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;

                CREATE TRIGGER update_latest_drp_trigger
                AFTER INSERT OR UPDATE ON daily_regional_placement
                FOR EACH ROW
                EXECUTE FUNCTION update_latest_drp();
            """)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'placement': self.placement,
            'entry_time': self.entry_time.strftime("%Y-%m-%d %H:%M:%S.%f"),
        }


event.listen(DRP.__table__, 'after_create', DRP.trigger)


class DGP(db.Model):
    __tablename__ = 'daily_global_placement'

    id: db.Mapped[int] = db.Column(db.BigInteger, primary_key=True)
    user_id: db.Mapped[int] = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False)
    placement: db.Mapped[int] = db.Column(db.Integer, nullable=False, server_default='0', default=0)
    entry_time: db.Mapped[datetime] = db.Column(db.DateTime, db.ForeignKey('entry_date.entry_time'), nullable=False)

    __table_args__ = (
        db.Index('idx_daily_global_placement_user_id', user_id),
        db.Index('idx_daily_global_placement_entry_time', entry_time)
    )

    trigger = DDL("""
                CREATE OR REPLACE FUNCTION update_latest_dgp()
                RETURNS TRIGGER AS $$
                BEGIN
                  UPDATE users SET latest_dgp = NEW.placement WHERE users.id = NEW.user_id;
                  RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;

                CREATE TRIGGER update_latest_dgp_trigger
                AFTER INSERT OR UPDATE ON daily_global_placement
                FOR EACH ROW
                EXECUTE FUNCTION update_latest_dgp();
            """)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'placement': self.placement,
            'entry_time': self.entry_time.strftime("%Y-%m-%d %H:%M:%S.%f"),
        }


event.listen(DGP.__table__, 'after_create', DGP.trigger)


class Leaderboard(db.Model):
    __tablename__ = 'leaderboard'

    id: db.Mapped[int] = db.Column(db.BigInteger, primary_key=True)
    user_id: db.Mapped[int] = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False)
    position: db.Mapped[int] = db.Column(db.Integer, nullable=False, server_default='0', default=0)
    elo: db.Mapped[float] = db.Column(db.Double, nullable=False, server_default='0.0', default=0)
    wins: db.Mapped[int] = db.Column(db.Integer, nullable=False, server_default='0', default=0)
    losses: db.Mapped[int] = db.Column(db.Integer, nullable=False, server_default='0', default=0)
    drp: db.Mapped[int] = db.Column(db.Integer, nullable=False, server_default='0', default=0)
    dgp: db.Mapped[int] = db.Column(db.Integer, nullable=False, server_default='0', default=0)
    entry_time: db.Mapped[datetime] = db.Column(db.DateTime, db.ForeignKey('entry_date.entry_time'), nullable=False)

    __table_args__ = (
        db.Index('idx_leaderboard_user_id', user_id),
        db.Index('idx_leaderboard_entry_time', entry_time)
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'position': self.position,
            'elo': self.elo,
            'wins': self.wins,
            'losses': self.losses,
            'dgp': self.dgp,
            'drp': self.drp,
            'entry_time': self.entry_time.strftime("%Y-%m-%d %H:%M:%S.%f"),
        }


class CharactersEntry(db.Model):
    __tablename__ = 'character_entry'

    id: db.Mapped[int] = db.Column(db.BigInteger, primary_key=True)
    user_id: db.Mapped[int] = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False)
    character_id: db.Mapped[int] = db.Column(db.Integer, db.ForeignKey('character_list.id'), nullable=False)
    game_count: db.Mapped[int] = db.Column(db.Integer, nullable=False)
    entry_time: db.Mapped[datetime] = db.Column(db.DateTime, db.ForeignKey('entry_date.entry_time'), nullable=False)

    character_info: db.Mapped['CharacterList'] = db.relationship('CharacterList',
                                                                 back_populates='character_entries', lazy='joined')

    __table_args__ = (
        db.Index('idx_character_entry_user_id', user_id),
        db.Index('idx_character_entry_entry_time', entry_time)
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'character_id': self.character_id,
            'game_count': self.game_count,
            'entry_time': self.entry_time.strftime("%Y-%m-%d %H:%M:%S.%f"),
        }


'''

def generate_latest_entry(model):
    return (
        select(model.user_id, func.max(model.entry_time).label('max_entry_time'))
        .group_by(model.user_id)
        .alias()
        )

'''


def create_character_list():

    # Create CharacterList with entries from SlippiCharacterId
    # Because 0 is used for DK, we are mapping 0 to 255
    if len(CharacterList.query.all()) != 27:
        for key, value in SlippiCharacterId.items():
            # DK claus
            if value == 0:
                value = 255
            db.session.add(CharacterList(id=value, name=key))

        db.session.commit()
