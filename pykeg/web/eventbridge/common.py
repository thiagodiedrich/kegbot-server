# Copyright 2014 Bevbot LLC, All Rights Reserved
#
# This file is part of the Pykeg package of the Kegbot project.
# For more information on Pykeg or Kegbot, see http://kegbot.org/
#
# Pykeg is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# Pykeg is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pykeg.  If not, see <http://www.gnu.org/licenses/>.

import gflags
import logging
import redis
from kegbot.util import kbjson

from pykeg.proto import protolib

logger = logging.getLogger(__name__)

gflags.DEFINE_string('eventbridge_redis_host', 'localhost',
    'Hostname of the Redis server for the Kegbot event bridge.')

gflags.DEFINE_integer('eventbridge_redis_port', 6379,
    'Port number of the Redis server for the Kegbot event bridge.')

gflags.DEFINE_integer('eventbridge_redis_db', 0,
    'Database number of the Redis server for the Kegbot event bridge.')

gflags.DEFINE_string('eventbridge_channel_name', 'kegbot:eventbridge',
    'Pubsub channel name for the Kegbot event bridge.')

FLAGS = gflags.FLAGS

def get_redis():
    """Returns a new Redis client for the eventbridge server."""
    return redis.StrictRedis(host=FLAGS.eventbridge_redis_host,
        port=FLAGS.eventbridge_redis_port, db=FLAGS.eventbridge_redis_db)

def publish_event(event, redis_client=None):
    """Publishes a single event on the event bridge."""
    publish_events([event], redis_client=redis_client)

def publish_events(events, redis_client=None):
    """Publishes a set of events on the event bridge."""
    logger.debug('Publishing events: {}'.format(events))
    events = [{'type': 'event', 'data': protolib.ToDict(e, True)} for e in events]
    redis_client = get_redis() if not redis_client else redis_client
    for event in events:
        redis_client.publish(FLAGS.eventbridge_channel_name, kbjson.dumps(event, indent=2))

def subscribe_and_listen(redis_client=None):
    redis_client = get_redis() if not redis_client else redis_client
    ps = redis_client.pubsub()

    channel = FLAGS.eventbridge_channel_name
    logger.info('Subscribing to channel {}'.format(channel))
    ps.subscribe([channel])
    for message in ps.listen():
        if message.get('type') != 'event':
            logger.info('Ignoring message: {}'.format(message))
            continue
        logger.info('Received message: {}'.format(message))
        yield message