import logging
from os import getenv
from functools import wraps
from datetime import datetime

from flask import render_template, jsonify, request, abort
from flask_sqlalchemy import SQLAlchemy
from slippi.slippi_api import SlippiRankedAPI
from slippi.slippi_user import Characters
from slippi.slippi_characters import get_character_id, get_character_name

from models import db, User, CharacterList, EntryDate, Elo, WinLoss, DRP, DGP, Leaderboard, CharactersEntry
from database.queries import require_api_key

logger = logging.getLogger(f'andross.{__name__}')


@require_api_key
def update_database():
    logger.info('update_database')

    user_id = request.args.get('user_id')
    slippi_api = SlippiRankedAPI()

    # Create date entry for this update
    current_time = datetime.utcnow()
    entry_date = EntryDate(entry_time=current_time)
    db.session.add(entry_date)
    db.session.commit()

    # Loop through all users and get their ranked data, when unable to get users abort
    users_list = User.query.all() if not user_id else User.query.filter(User.id == int(user_id)).all()
    if not users_list:
        abort(400, 'Unable to get users')

    ranked_data = [[user, slippi_api.get_player_ranked_data(user.cc)] for user in users_list]
    if not ranked_data:
        abort(400, 'Unable to get slippi data')

    for entry in ranked_data:
        local_user = entry[0]
        slippi_user = entry[1]

        # Skip to next entry if user has no ranked id
        if not slippi_user.ranked_profile.id:
            continue

        # Update the slippi_id if it doesn't match
        if local_user.slippi_id != slippi_user.ranked_profile.id:
            local_user.slippi_id = slippi_user.ranked_profile.id
            db.session.commit()

        # Create elo entry if slippi data doesn't match user.latest_elo
        if local_user.latest_elo != slippi_user.ranked_profile.rating_ordinal:
            elo_entry = Elo(user_id=local_user.id,
                            elo=slippi_user.ranked_profile.rating_ordinal,
                            entry_time=entry_date.entry_time)
            db.session.add(elo_entry)
            db.session.commit()

        # Create win-loss entry if slippi data doesn't match user.latest_win/losses
        if local_user.latest_wins != slippi_user.ranked_profile.wins or \
           local_user.latest_losses != slippi_user.ranked_profile.losses:

            win_loss = WinLoss(user_id=local_user.id,
                               wins=slippi_user.ranked_profile.wins,
                               losses=slippi_user.ranked_profile.losses,
                               entry_time=entry_date.entry_time)
            db.session.add(win_loss)
            db.session.commit()

        # Create drp entry if slippi data doesn't match user.latest_drp
        if local_user.latest_drp != slippi_user.ranked_profile.daily_regional_placement:
            drp_entry = DRP(user_id=local_user.id,
                            placement=slippi_user.ranked_profile.daily_regional_placement,
                            entry_time=entry_date.entry_time)
            db.session.add(drp_entry)
            db.session.commit()

        # Create dgp entry if latest dgp entry for user doesn't match slippi data
        if slippi_user.ranked_profile.daily_global_placement:
            latest_dgp = DGP.query.filter_by(DGP.user_id == local_user.id).order_by(DGP.entry_time.desc()).first()

            if latest_dgp:
                if latest_dgp.placement != slippi_user.ranked_profile.daily_global_placement:
                    dgp_entry = DGP(user_id=local_user.id,
                                    placement=slippi_user.ranked_profile.daily_global_placement,
                                    entry_time=entry_date.entry_time)
                    db.session.add(dgp_entry)
                    db.session.commit()

        # Create character_entry for user
        if len(slippi_user.ranked_profile.characters):
            write_character = True
            latest_character_entry = CharactersEntry.query\
                .filter(CharactersEntry.user_id == local_user.id).order_by(CharactersEntry.entry_time.desc()).first()

            local_character_list = []
            if latest_character_entry:
                latest_characters = CharactersEntry.query.filter(
                    db.and_(CharactersEntry.user_id == local_user.id,
                            CharactersEntry.entry_time == latest_character_entry.entry_time)).all()

                if latest_characters:
                    for character in latest_characters:
                        local_character_list.append(Characters(0, character.character_info.name, character.game_count))

                    slippi_character_dict = {c.character: c.game_count for c in slippi_user.ranked_profile.characters}
                    local_character_dict = {c.character: c.game_count for c in local_character_list}

                    if slippi_character_dict == local_character_dict:
                        write_character = False

            if write_character:
                for character in slippi_user.ranked_profile.characters:
                    character_entry = CharactersEntry(character_id=get_character_id(character.character, dk_claus=True),
                                                      user_id=local_user.id,
                                                      game_count=character.game_count,
                                                      entry_time=entry_date.entry_time)

                    db.session.add(character_entry)
                    db.session.commit()

                main_id = get_character_id(
                    max(slippi_user.ranked_profile.characters, key=lambda c: c.game_count).character,
                    dk_claus=True)
                local_user.main_id = main_id
                db.session.commit()

    return {'message': 'Updated database successfully'}, 201
