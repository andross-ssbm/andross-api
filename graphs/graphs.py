import os
import logging

import matplotlib
from matplotlib import pyplot, dates, cycler
from datetime import timedelta

from flask import request, abort, send_file

from slippi.slippi_characters import SlippiCharacterColors
from slippi.slippi_ranks import rank_list

from models import db, User, Elo, CharactersEntry

matplotlib.use('Agg')
logger = logging.getLogger(f'andross.{__name__}')


discord_colors = {
    'green': '#57F287',
    'slippi_green': '#21ba45',
    'yellow': '#FAA61A',
    'blurple': '#5865F2',
    'fuchsia': '#EB459E',
    'red': '#ED4245',
    'grey': '#B9BBBE',
    'dark': '#36393F',
    'dark_theme_bg': '#313338',
    'dark_theme_highlight': '#2b2d31',
    'light_blue': '#4FC1E9',
    'orange': '#FFA500',
    'purple': '#9B59B6',
    'turquoise': '#1ABC9C',
    'pink': '#E91E63',
    'grey_blue': '#607D8B',
    'black': '#000000',
}

discord_dark_style = {
    'axes.facecolor': discord_colors['dark_theme_bg'],
    'axes.edgecolor': discord_colors['grey'],
    'axes.labelcolor': discord_colors['grey'],
    'text.color': discord_colors['grey'],
    'xtick.color': discord_colors['grey'],
    'ytick.color': discord_colors['grey'],
    'grid.color': discord_colors['grey'],
    'figure.facecolor': discord_colors['dark_theme_bg'],
    'figure.edgecolor': discord_colors['dark_theme_bg'],
    'savefig.facecolor': discord_colors['dark_theme_highlight'],
    'savefig.edgecolor': discord_colors['dark_theme_bg'],
    'font.family': 'sans-serif',
    'font.sans-serif': ['Open Sans', 'Arial', 'Helvetica', 'DejaVu Sans', 'Bitstream Vera Sans', 'sans-serif'],
    'axes.prop_cycle': cycler(color=[discord_colors['slippi_green'], discord_colors['yellow'],
                                     discord_colors['blurple'], discord_colors['fuchsia'], discord_colors['green'],
                                     discord_colors['red'], discord_colors['light_blue'], discord_colors['orange'],
                                     discord_colors['purple'], discord_colors['turquoise'], discord_colors['pink'],
                                     discord_colors['grey_blue']]),

    'axes.titlesize': 'xx-large',
    'axes.labelsize': 'x-large'
}


def get_character_usage_pie():
    logger.debug('get_character_usage_pie')

    user_id = request.args.get('id')
    as_image = request.args.get('as_image')

    if not user_id:
        abort(400, 'Missing required parameter (id)')

    user = db.get_or_404(User, user_id, description='User not found')

    latest_character = db.session.query(CharactersEntry)\
        .where(CharactersEntry.user_id == int(user_id))\
        .order_by(CharactersEntry.entry_time.desc()).first()

    if not latest_character:
        abort(404, f'No character entries for given user_id {user_id}')

    latest_character_entries = db.session.query(CharactersEntry)\
        .where(db.and_(CharactersEntry.user_id == int(user_id),
                       CharactersEntry.entry_time == latest_character.entry_time))\
        .order_by(CharactersEntry.game_count.desc()).all()

    if not latest_character_entries:
        abort(500, f'Was unable to get latest characters for given user_id {user_id}')

    labels = []
    data = []
    colors = []

    for character in latest_character_entries:
        labels.append(character.character_info.name.title())
        data.append(character.game_count)
        colors.append(SlippiCharacterColors[character.character_info.name])

    pyplot.style.use(discord_dark_style)
    fig, ax = pyplot.subplots()
    ax.pie(data, labels=labels, colors=colors, autopct='%1.1f%%', textprops={'color': discord_colors['grey']})
    ax.set_title(user.name, fontsize='xx-large')

    cwd = os.getcwd()
    static_dir = "static"
    images_dir = "images"
    graphs_dir = "graphs"
    sub_path = os.path.join(cwd, *[static_dir, images_dir, graphs_dir])

    if not os.path.exists(sub_path):
        os.makedirs(sub_path)

    # concatenate directory path with image file name
    filename = f'characters_{user.id}.png'
    filepath = os.path.join(cwd, *[static_dir, images_dir, graphs_dir], filename)

    # save image to specified directory
    pyplot.savefig(filepath)
    pyplot.clf()
    pyplot.close(fig)

    return filename if not as_image else send_file(filepath, mimetype='image/png')


def get_basic_elo_graph():
    logger.debug('get_basic_elo_graph')

    user_id = request.args.get('id')
    as_image = request.args.get('as_image')

    if not user_id:
        abort(400, 'Missing required parameter (id)')

    user = db.get_or_404(User, user_id, description='User not found')

    x_axis = []
    y_axis = []

    for elo_entry in user.elo_entries:
        x_axis.append(elo_entry.entry_time)
        y_axis.append(elo_entry.elo)

    if not x_axis or not y_axis:
        return

    if len(x_axis) == 1:
        single_point = x_axis[0]
        x_axis.append(single_point - timedelta(days=1) - timedelta(weeks=1))  # Offset the new data point by 1 minute
        y_axis.append(y_axis[0])  # Duplicate the single data point

    pyplot.style.use(discord_dark_style)
    fig, ax = pyplot.subplots(figsize=(15, 10))
    ax.plot(x_axis, y_axis)
    ax.set_title(user.name, fontsize='xx-large')
    ax.set_ylabel('Elo', fontsize='x-large')
    ax.set_xlabel('Time', fontsize='x-large')
    date_range = dates.drange(min(x_axis).date(), max(x_axis).date() + timedelta(days=1), timedelta(weeks=1))
    ax.set_xticks(date_range)
    ax.set_xticklabels([dates.num2date(d).strftime('%Y-%m-%d') for d in date_range], rotation=90)

    # Get y ticks to check bounds of ranks
    y_ticks = ax.get_yticks()

    # Add extra y-axis ticks for rank names
    for rank in rank_list:
        if y_ticks[-1] > rank.lower_bound and y_ticks[0] < rank.upper_bound:
            ax.axhline(y=rank.lower_bound, color='gray', linestyle='--', linewidth=0.5)
            ax.text(x_axis[0], rank.lower_bound, rank.rank_name, fontsize='x-small')

    cwd = os.getcwd()
    static_dir = "static"
    images_dir = "images"
    graphs_dir = "graphs"
    sub_path = os.path.join(cwd, *[static_dir, images_dir, graphs_dir])

    if not os.path.exists(sub_path):
        os.makedirs(sub_path)

    # concatenate directory path with image file name
    filename = f'elo_{user.id}.png'
    filepath = os.path.join(cwd, *[static_dir, images_dir, graphs_dir], filename)

    # save image to specified directory
    pyplot.savefig(filepath)
    pyplot.clf()
    pyplot.close(fig)
    if not as_image:
        return {
            'filename': filename,
            'start_date': min(x_axis).date().strftime('%m/%d/%Y'),
            'end_date': max(x_axis).date().strftime('%m/%d/%Y')
        }, 200
    else:
        return send_file(filepath, mimetype='image/png')
