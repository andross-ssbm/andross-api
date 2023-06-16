import argparse
import os

import requests

from custom_logging import CustomFormatter

logger = CustomFormatter().get_logger()

logger.info(f'create_snapshot.py ran')

parser = argparse.ArgumentParser()
parser.add_argument('-v', '--verbose', help='Sets logging level to debug')
parser.add_argument('-l', '--leaderboard', help='Update the leaderboard', action='store_true')
parser.add_argument('-d', '--database', help='Update the main database entries', action='store_true')

args = parser.parse_args()
logger.debug(f'--verbose: {args.verbose}')
logger.debug(f'--leaderboard: {args.leaderboard}')
logger.debug(f'--database {args.database}')

api_key = os.getenv('API_KEY')

if args.leaderboard:
    logger.info('Updating leaderboard')
    response = requests.post(f'localhost:5000/rest/update_leaderboard/',
                             headers={"X-API-KEY": api_key, 'Content-Type': 'application/json'})
    logger.info(f'Leaderboard {"Updated." if response.status_code == 201 else "not updated."} {response.status_code}')

if args.database:
    logger.info('Updating database')
    response = requests.post(f'localhost:5000/rest/update/',
                             headers={"X-API-KEY": api_key, 'Content-Type': 'application/json'})
    logger.info(f'Database {"Updated." if response.status_code == 201 else "not updated."}  {response.status_code}')