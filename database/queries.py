import logging
from os import getenv
from functools import wraps
from datetime import datetime

from flask import render_template, jsonify, request, abort
from flask_sqlalchemy import SQLAlchemy
from models import db, User, CharacterList, EntryDate, Elo, WinLoss, DRP, DGP, Leaderboard, CharactersEntry
from slippi.slippi_api import SlippiRankedAPI
from slippi.slippi_ranks import get_rank

logger = logging.getLogger(f'andross.{__name__}')


def require_api_key(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key and api_key == getenv('API-KEY'):
            return func(*args, **kwargs)
        else:
            abort(401)
    return decorated_function


def create_user(user_id: int, cc: str, name: str):

    if not user_id or not cc or not name:
        return {'error_message': 'Missing a required parameter (id, cc, name).'}, 400

    if User.query.filter_by(id=user_id).first():
        return {'error_message': 'User already exists.'}, 400

    if User.query.filter_by(cc=cc).first():
        return {'error_message': 'Connect code already in use.'}, 400

    if not SlippiRankedAPI.is_valid_connect_code(cc):
        return {'error_message': f'Invalid connect code "{cc}".'}, 400

    if len(name) > 12:
        return {'error_message': 'Name is too long, please provide a name shorter than 12.'}

    db.session.add(User(id=int(user_id), cc=cc, name=name))
    db.session.commit()

    return {'message': 'User created successfully'}, 201


@require_api_key
def update_user(user_id: int):
    cc = request.args.get('cc')
    name = request.args.get('name')

    if not cc and not name:
        return {'error_message': 'Missing both cc and name, please provide at least one.'}, 400

    user = db.session.query(User).filter(User.id == user_id).first()
    if not user:
        return create_user(user_id, cc, name)

    if cc and cc != user.cc:
        if not SlippiRankedAPI.is_valid_connect_code(cc):
            return {'error_message': 'Invalid connect code.'}

        user_cc = db.session.query(User).filter_by(cc=cc).first()
        if user_cc:
            return {'error_message': f'Connect code is already used by {user_cc.name}'}, 400
        user.cc = cc
        db.session.commit()

    if name and name != user.name:
        if len(name) > 12:
            return {'error_message': 'Name is too long, please provide a name shorter than 12.'}
        user.name = name
        db.session.commit()

    return {'message': 'User updated successfully'}, 201


def get_users():
    users = User.query.all()
    return [user.to_dict() for user in users]


def get_users_by_id(user_id: int):
    user = db.get_or_404(User, user_id, description='User not found')
    return user.to_dict()


def get_users_by_cc(user_cc: str):
    user = db.one_or_404(db.select(User).filter_by(cc=user_cc.replace('-', '#')), description='User not found')
    return user.to_dict()


@require_api_key
def create_elo():
    user_id = request.args.get('user_id')
    elo = request.args.get('elo')
    entry_time = request.args.get('entry_time')

    if not user_id or not elo or not entry_time:
        abort(400, 'Missing required parameter (user_id, elo, entry_time)')

    entry_time = datetime.strptime(entry_time, '%Y-%m-%d %H:%M:%S.%f')

    elo_entry = Elo(user_id=int(user_id), elo=float(elo), entry_time=entry_time)
    db.session.add(elo_entry)
    db.session.commit()

    return {'message': 'elo entry created successfully'}, 200


def get_elo():
    user_id = request.args.get('user_id')
    start_date_arg = request.args.get('start_date')
    end_date_arg = request.args.get('end_date')
    # if start/end_date_arg are none, sub in values
    start_date = datetime.strptime(start_date_arg if start_date_arg else '2020-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
    end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d %H:%M:%S') if end_date_arg \
        else datetime.utcnow()

    elo_entries = db.session.query(Elo)\
        .where(db.and_(Elo.entry_time.between(start_date, end_date), Elo.user_id == int(user_id)))\
        .order_by(Elo.entry_time.desc()).all()

    if not elo_entries:
        abort(404, f'Unable to find elo entries for the given values ({user_id}, {start_date}, {end_date})')

    return [elo.to_dict() for elo in elo_entries]


def get_elo_by_user_id():
    elo_entries = Elo.query.filter_by(user_id=request.args.get('user_id')).all()
    if not elo_entries:
        abort(404, f'Unable to find elo entries with user_id {request.args.get("user_id")}')
    return [elo.to_dict() for elo in elo_entries]


def get_latest_elo():
    user_id = request.args.get('user_id')

    if not user_id:
        latest_elo_entry = db.session.query(Elo).order_by(Elo.entry_time.desc())
    else:
        latest_elo_entry = db.session.query(Elo).where(Elo.user_id == int(user_id)).order_by(Elo.entry_time.desc())

    latest_elo_entry = latest_elo_entry.first()

    if not latest_elo_entry:
        abort(404, f'Unable to find latest elo entry')

    return latest_elo_entry.to_dict()


def get_latest_characters():
    user_id = request.args.get('user_id')
    if not user_id:
        abort(400, 'Required parameter user_id is missing')

    latest_character = db.session.query(CharactersEntry)\
        .where(CharactersEntry.user_id == int(user_id)).order_by(CharactersEntry.entry_time.desc()).first()
    if not latest_character:
        abort(404, f'No character entries for given user_id {user_id}')

    latest_characters_entries = db.session.query(CharactersEntry)\
        .where(db.and_(CharactersEntry.user_id == user_id, CharactersEntry.entry_time == latest_character.entry_time))\
        .order_by(CharactersEntry.game_count.desc()).all()
    if not latest_characters_entries:
        abort(500, f'Was unable to get latest characters for given user_id {user_id}')

    return [character.to_dict() for character in latest_characters_entries]


@require_api_key
def create_entry_date():
    entry_time = request.args.get('entry_time')

    if not entry_time:
        abort(400, 'Missing required parameter entry_time')

    entry_time = datetime.strptime(entry_time, '%Y-%m-%d %H:%M:%S.%f')

    entry_date = EntryDate(entry_time=entry_time)
    db.session.add(entry_date)
    db.session.commit()

    return {'message': 'entry_date entry created successfully',
            'entry_time': entry_time.strftime('%Y-%m-%d %H:%M:%S.%f')}, 200


@require_api_key
def create_win_loss():
    user_id = request.args.get('user_id')
    wins = request.args.get('wins')
    losses = request.args.get('losses')
    entry_time = request.args.get('entry_time')

    if not user_id or not wins or not losses or not entry_time:
        abort(400, 'Missing a required parameter (user_id, wins, losses, entry_time)')

    entry_time = datetime.strptime(entry_time, '%Y-%m-%d %H:%M:%S.%f')

    win_loss = WinLoss(user_id=int(user_id), wins=int(wins), losses=int(losses), entry_time=entry_time)
    db.session.add(win_loss)
    db.session.commit()

    return {'message': 'win_loss entry created successfully'}, 200


@require_api_key
def create_drp():
    user_id = request.args.get('user_id')
    drp = request.args.get('drp')
    entry_time = request.args.get('entry_time')

    if not user_id or not drp or not entry_time:
        abort(400, 'Missing required parameter (user_id, drp, entry_time)')

    entry_time = datetime.strptime(entry_time, '%Y-%m-%d %H:%M:%S.%f')

    drp_entry = DRP(user_id=int(user_id), placement=int(drp), entry_time=entry_time)
    db.session.add(drp_entry)
    db.session.commit()

    return {'message': 'drp entry created successfully'}, 200


def get_latest_leaderboard_entry():
    user_id = request.args.get('id')

    if not user_id:
        abort(400, 'Missing require argument (id)')

    lbe = Leaderboard.query.filter(Leaderboard.user_id == int(user_id)).order_by(Leaderboard.entry_time.desc()).first()
    if not lbe:
        abort(404, f'Unable to get latest leaderboard entry for ({user_id})')

    return lbe.to_dict()


def get_leaderboard():
    users = User.query.order_by(User.latest_elo.desc()).all()
    users = [user.to_dict() for user in users]

    for i, user in enumerate(users):
        user['position'] = i + 1

    return users


def get_leaderboard_website():
    users = User.query.order_by(User.latest_elo.desc()).all()
    characters = [user.get_latest_characters() or [] for user in users]
    return render_template('leaderboard.html', users=users, get_rank=get_rank, characters=characters)
