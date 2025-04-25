import logging
from datetime import datetime

from flask import request
from slippi.slippi_api import SlippiRankedAPI
from slippi.slippi_user import Characters
from slippi.slippi_characters import get_character_id

from models import db, User, EntryDate, Elo, WinLoss, DRP, DGP, Leaderboard, CharactersEntry
from database.queries import require_api_key

logger = logging.getLogger(f'andross-api')


@require_api_key
def update_leaderboard():
    logger.info('update_leaderboard')

    slippi_api = SlippiRankedAPI()

    current_time = datetime.utcnow()
    entry_date = EntryDate(entry_time=current_time)
    db.session.add(entry_date)
    db.session.commit()

    users_list = User.query.filter_by(is_michigan = True).all()
    if not users_list:
        return {'error_message': 'Unable to get users'}, 404

    ranked_data = [(user, slippi_api.get_player_ranked_data(user.cc)) for user in users_list]
    if not ranked_data:
        return {'error_message': 'Unable to get slippi data'}, 404

    logger.info('Sorting users')
    sorted_ranked_data = sorted([(user, slippi_user) for user, slippi_user in ranked_data if slippi_user],
                                key=lambda x: x[1].ranked_profile.rating_ordinal, reverse=True)

    counter = 1
    for user in sorted_ranked_data:
        local_user = user[0]
        slippi_data = user[1]

        if slippi_data.ranked_profile.wins or slippi_data.ranked_profile.losses:
            leadboard_entry = Leaderboard(user_id=local_user.id,
                                          position=counter,
                                          elo=slippi_data.ranked_profile.rating_ordinal,
                                          wins=slippi_data.ranked_profile.wins,
                                          losses=slippi_data.ranked_profile.losses,
                                          drp=slippi_data.ranked_profile.daily_regional_placement,
                                          dgp=slippi_data.ranked_profile.daily_global_placement,
                                          entry_time=current_time)
            db.session.add(leadboard_entry)
            db.session.commit()
            counter += 1

    return {'message': 'Updated leaderboard'}, 201


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
        logger.critical('Unable to get users')
        return {'error_message': 'Unable to get users'}, 404

    ranked_data = [[user, slippi_api.get_player_ranked_data(user.cc)] for user in users_list]
    if not ranked_data:
        logger.critical('Unable to get slippi data')
        return {'error_message': 'Unable to get slippi data'}, 404

    for entry in [[user, slippi_data] for user, slippi_data in ranked_data if slippi_data]:
        local_user = entry[0]
        slippi_user = entry[1]
        logger.info(f'Attempting to update {local_user}')

        # Skip to next entry if user has no ranked id
        if not slippi_user.ranked_profile.id:
            logger.info('Has no slippi profile')
            continue

        # Update the slippi_id if it doesn't match
        logger.info('Update slippi id')
        if local_user.slippi_id != slippi_user.ranked_profile.id:
            local_user.slippi_id = slippi_user.ranked_profile.id
            db.session.commit()

        # Create elo entry if slippi data doesn't match user.latest_elo
        logger.info('Update elo')
        if local_user.latest_elo != slippi_user.ranked_profile.rating_ordinal:
            elo_entry = Elo(user_id=local_user.id,
                            elo=slippi_user.ranked_profile.rating_ordinal,
                            entry_time=entry_date.entry_time)
            db.session.add(elo_entry)
            db.session.commit()

        # Create win-loss entry if slippi data doesn't match user.latest_win/losses
        logger.info('Update win loss')
        if local_user.latest_wins != slippi_user.ranked_profile.wins or \
           local_user.latest_losses != slippi_user.ranked_profile.losses:

            win_loss = WinLoss(user_id=local_user.id,
                               wins=slippi_user.ranked_profile.wins,
                               losses=slippi_user.ranked_profile.losses,
                               entry_time=entry_date.entry_time)
            db.session.add(win_loss)
            db.session.commit()

        # Create drp entry if slippi data doesn't match user.latest_drp
        logger.info('Update drp')
        if local_user.latest_drp != slippi_user.ranked_profile.daily_regional_placement:
            drp_entry = DRP(user_id=local_user.id,
                            placement=slippi_user.ranked_profile.daily_regional_placement,
                            entry_time=entry_date.entry_time)
            db.session.add(drp_entry)
            db.session.commit()

        # Create dgp entry if latest dgp entry for user doesn't match slippi data
        logger.info('Update dgp')
        if local_user.latest_dgp != slippi_user.ranked_profile.daily_global_placement:
            dgp_entry = DGP(user_id=local_user.id,
                            placement=slippi_user.ranked_profile.daily_global_placement,
                            entry_time=entry_date.entry_time)
            db.session.add(dgp_entry)
            db.session.commit()

        """
        # Create character_entry for user
        logger.info('Update characters')
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

                logger.info('Update main')
                main_id = get_character_id(
                    max(slippi_user.ranked_profile.characters, key=lambda c: c.game_count).character,
                    dk_claus=True)
                local_user.main_id = main_id
                db.session.commit()
        """

        logger.info(f'Updated {local_user}')

    return {'message': 'Updated database successfully'}, 201
