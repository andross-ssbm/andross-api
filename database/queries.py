import logging
from os import getenv
from functools import wraps
from datetime import datetime

from flask import render_template, request, abort
from models import Seasons, db, User, EntryDate, Elo, WinLoss, DRP, Leaderboard, CharactersEntry
from slippi.slippi_api import SlippiRankedAPI
from slippi.slippi_ranks import get_rank

logger = logging.getLogger(f'andross.{__name__}')


def require_api_key(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key and api_key == getenv('API_KEY'):
            return func(*args, **kwargs)
        else:
            abort(401)
    return decorated_function

@require_api_key
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

    if not cc or not name:
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
        return {'error_message': 'Missing required paramter (user_id, elo, entry_time).'}

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
    end_date = datetime.strptime(end_date_arg, '%Y-%m-%d %H:%M:%S') if end_date_arg \
        else datetime.utcnow()

    elo_entries = db.session.query(Elo)\
        .where(db.and_(Elo.entry_time.between(start_date, end_date), Elo.user_id == int(user_id)))\
        .order_by(Elo.entry_time.desc()).all()

    if not elo_entries:
        return {
            'error_message': f'Unable to find elo entries for the given values({user_id}, {start_date}, {end_date})'
        }, 404

    return [elo.to_dict() for elo in elo_entries]


def get_elo_by_user_id(user_id: int):
    elo_entries = Elo.query.filter_by(user_id=user_id).all()
    if not elo_entries:
        return {'error_message': f'Unable to find elo entries with user_id {user_id}'}, 404
    return [elo.to_dict() for elo in elo_entries]


def get_latest_elo(user_id: int):
    current_season = db.session.query(Seasons)\
            .where(Seasons.is_current == True).first()
    if not current_season:
        return {'error_message': 'Unable to get current seasons'}, 404

    if not user_id:
        latest_elo_entry = db.session.query(Elo).where(Elo.entry_time > current_season.start_date).order_by(Elo.entry_time.desc())
    else:
        latest_elo_entry = db.session.query(Elo).where(db.and_(Elo.user_id == int(user_id), Elo.entry_time > current_season.start_date)).order_by(Elo.entry_time.desc())

    latest_elo_entry = latest_elo_entry.first()

    if not latest_elo_entry:
        return {'error_message': 'Unable to find latest elo entry'}, 404

    return latest_elo_entry.to_dict()


def get_latest_characters(user_id: int):

    current_season = db.session.query(Seasons)\
            .where(Seasons.is_current == True).first()
    if not current_season:
        return {'error_message': 'Unable to get current seasons'}, 404

    latest_character = db.session.query(CharactersEntry)\
        .where(
                db.and_(CharactersEntry.user_id == int(user_id), 
                        CharactersEntry.entry_time > current_season.start_date))\
                                .order_by(CharactersEntry.entry_time.desc()).first()

    if not latest_character:
        return {'error_message': f'No character entries for given user_id {user_id}'}

    latest_characters_entries = db.session.query(CharactersEntry)\
        .where(db.and_(CharactersEntry.user_id == user_id, CharactersEntry.entry_time == latest_character.entry_time))\
        .order_by(CharactersEntry.game_count.desc()).all()
    if not latest_characters_entries:
        return {'error_message': f'Was unable to get latest characters for given user_id {user_id}'}, 500

    return [character.to_dict() for character in latest_characters_entries]


@require_api_key
def create_entry_date():
    entry_time = request.args.get('entry_time')

    if not entry_time:
        return {'error_message': 'Missing required paramter entry_time.'}

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
        return {'error_message': 'Missing a required parameter (user_id, wins, losses, entry_time).'}, 400

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
        return {'error_message': 'Missing require paramter (user_id, drp, entry_time).'}, 400

    entry_time = datetime.strptime(entry_time, '%Y-%m-%d %H:%M:%S.%f')

    drp_entry = DRP(user_id=int(user_id), placement=int(drp), entry_time=entry_time)
    db.session.add(drp_entry)
    db.session.commit()

    return {'message': 'drp entry created successfully'}, 200


@require_api_key
def create_season():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    is_current = bool(request.args.get('is_current')) or False

    if not start_date or not end_date:
        return {'error_message': 'Missing required parameter start_date.'}, 400

    start_date = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S.%f')
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S.%f')

    season_entry = Seasons(start_date=start_date, end_date=end_date, is_current=is_current)
    db.session.add(season_entry)
    db.session.commit()

    return {'message': 'seasons entry created successfully'}, 200


def get_latest_leaderboard_entry():
    user_id = request.args.get('id')

    if not user_id:
        return {'error_message': 'Missing required argument (id).'}, 400

    current_season = db.session.query(Seasons)\
            .where(Seasons.is_current == True).first()
    if not current_season:
        return {'error_message': 'Unable to get current seasons'}, 404

    lbe = Leaderboard.query.where(db.and_(Leaderboard.user_id == int(user_id), 
                                          Leaderboard.entry_time > current_season.start_date))\
            .order_by(Leaderboard.entry_time.desc()).first()
    if not lbe:
        return {'error_message': f'Unable to get latest leaderboard entry for ({user_id})'}, 404

    return lbe.to_dict()


def get_leaderboard_position(user_id: int):
    user = User.query.filter(User.id == user_id).first()

    if not user:
        return {'position': 0}, 200

    new_elo = request.args.get('elo')
    position = user.get_position(new_elo if new_elo else None)

    return {'position': position}, 200



def get_leaderboard():
    users = User.query.filter_by(is_michigan = True).order_by(User.latest_elo.desc()).all()
    users = [user.to_dict() for user in users]

    for i, user in enumerate(users):
        user['position'] = i + 1

    return users


def get_leaderboard_website():
    users = User.query.filter_by(is_michigan = True).order_by(User.latest_elo.desc()).all()
    characters = [user.get_latest_characters() or [] for user in users]
    return render_template('leaderboard.html', users=users, get_rank=get_rank, characters=characters)


def get_leaderboard_website_fast():
    sql_query = '''
SELECT ce.*, cl.name AS character_name
FROM users u
LEFT JOIN (
    SELECT ce.*
    FROM public.character_entry ce
    INNER JOIN (
        SELECT user_id, MAX(entry_time) AS max_entry_time
        FROM public.character_entry
        GROUP BY user_id
    ) ce_max ON ce.user_id = ce_max.user_id AND ce.entry_time = ce_max.max_entry_time
    LEFT JOIN character_list cl ON ce.character_id = cl.id
) ce ON u.id = ce.user_id
LEFT JOIN character_list cl ON ce.character_id = cl.id
WHERE ce.entry_time > (SELECT start_date FROM public.seasons WHERE is_current = true) AND u.is_michigan = True
ORDER BY ce.game_count DESC, ce.user_id;
'''
    users = User.query.order_by(User.latest_elo.desc()).all()
    results = db.session.execute(db.text(sql_query)).all()
    character_dict_list = {}
    for item in results:
        main_key = item[1]  # Using the second index as the main key
        if main_key not in character_dict_list:
            character_dict_list[main_key] = []
        character_dict_list[main_key].append({
            'id': item[0],
            'user_id': item[1],
            'character_id': item[2],
            'game_count': item[3],
            'entry_time': item[4],
            'name': item[5]
        })
    return render_template('leaderboard_fast.html', users=users, get_rank=get_rank, characters=character_dict_list)


def user_profile(user_id: int):
    user = db.get_or_404(User, user_id, description='Unable to get user')
    characters = user.get_latest_characters_fast()
    if not user.latest_wins and not user.latest_losses:
        user_rank = 'None'
    elif (user.latest_wins + user.latest_losses) < 5:
        user_rank = 'Pending'
    else:
        user_rank = get_rank(user.latest_elo, user.latest_dgp)
    return render_template('user_profile.html',
                           user=user,
                           user_rank=user_rank,
                           characters=characters or [])
