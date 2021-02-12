import datetime
import json
import logging
from environs import Env
from sierra_api import sierra_session

# Read enviroment variables and set defaults
env = Env()
env.read_env()

client_id = env.str('SIERRA_CLIENT_ID')
client_secret = env.str('SIERRA_CLIENT_SECRET')
base_url = env.str('SIERRA_BASE_URL')
batch_size = env.int('BATCH_SIZE') # Max patrons of each type to update per run
adult_age = env.int('ADULT_AGE')
juvenile_ptypes = env.list('JUVENILE_PTYPES', subcast=int)
adult_ptypes = env.list('ADULT_PTYPES', subcast=int)
log_level = env.str('LOG_LEVEL', 'INFO') # Default to INFO

# Configure logging
log_levels = {
  'DEBUG': logging.DEBUG, 
  'INFO': logging.INFO,
  'WARNING': logging.WARNING,
  'ERROR': logging.ERROR,
}

log_level_config = log_levels.get(log_level, logging.INFO)
logging.basicConfig(
  level=log_level_config, 
  format='%(asctime)s.%(msecs)03d %(levelname)s:%(message)s', 
  datefmt='%Y-%m-%d %H:%M:%S'
)

# Verify that juvenile and adult ptype lists are the same length to create 
# pairs
assert len(juvenile_ptypes) == len(adult_ptypes), 'Juvenile and adult PTypes must be in pairs.'

min_adult_birthdate = datetime.datetime.today().strftime("%m-%d-") + str(datetime.datetime.today().year - adult_age)

sierra = sierra_session(client_id, client_secret, base_url)

patronQueryTemplate = '''
{
  "queries": [
    {
      "target": {
        "record": {
          "type": "patron"
        },
        "id": 47
      },
      "expr": {
        "op": "equals",
        "operands": [
          "PTYPE_PLACEHOLDER",
          ""
        ]
      }
    },
    "and",
    {
      "target": {
        "record": {
          "type": "patron"
        },
        "id": 51
      },
      "expr": {
        "op": "less_than_or_equal",
        "operands": [
          "BIRTHDATE_PLACEHOLDER",
          ""
        ]
      }
    }
  ]
}
'''

if __name__ == "__main__":

  logging.info('START: Updating PType for juvenile patrons who have reached age {}.'.format(adult_age))

  for i, ptype in enumerate(juvenile_ptypes):

    juvenile_ptype = juvenile_ptypes[i]
    adult_ptype = adult_ptypes[i]

    logging.info('Changing PType {} to {} ...'.format(juvenile_ptype, adult_ptype))
    
    query = patronQueryTemplate.replace('PTYPE_PLACEHOLDER', str(juvenile_ptype)).replace('BIRTHDATE_PLACEHOLDER', min_adult_birthdate)
    
    patron_patch = json.dumps({'patronType': adult_ptype})
    
    response = sierra.post(base_url+'patrons/query', params={'offset': 0, 'limit': batch_size}, data=query)
    
    patrons = json.loads(response.content)
    
    logging.info('Found {count} PType {ptype} patrons over age {age}'.format(count=patrons['total'], ptype=juvenile_ptype, age=adult_age))
    
    if patrons['total'] > 0:
      for patron in patrons['entries']:
        patron_url = patron['link'] 
        patron_id = patron_url.split('/')[-1]
        logging.info('Changing patron {} from PType {} to {}'.format(patron_id, juvenile_ptype, adult_ptype))
        #response = sierra.put(patron_url, data=patron_patch)
  
  logging.info('END: Finished updating PTypes.')
