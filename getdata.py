'''
- get job from github:
https://github.com/awesome-jobs/vietnam/issues
- insert job into jobs table
'''
import logging
import requests
from datetime import date
from math import ceil
from sqlalchemy import create_engine, exc, MetaData
from urllib.parse import urljoin

TOKEN = '' # github Personal access tokens
# connect db
engine = create_engine('') # database uri
connection = engine.connect()
meta = MetaData()
meta.reflect(bind=engine)
# map table jobs
jobs_table = meta.tables['jobs']


# get open_issues
repos_url = 'https://api.github.com/users/awesome-jobs/repos'
repos_token = urljoin(repos_url, '?access_token={0}'.format(TOKEN))
repo = requests.get(repos_token)
open_issues = repo.json()[1]['open_issues']

# get issues
issues_url = 'https://api.github.com/repos/awesome-jobs/vietnam/issues'
url_token = urljoin(issues_url, '?access_token={0}'.format(TOKEN))
issues = requests.get(url_token)
per_page = len(issues.json())
paged = ceil(open_issues / per_page)

# get ids from db
query = 'SELECT * FROM jobs'
jobs = connection.execute(query).fetchall()
ids = [int(job[4]) for job in jobs]

for page in range(1, paged + 1):
    parameters = [url_token, '&page={0}'.format(page)]
    page_issues = ''.join(parameters)
    jobpages = requests.get(page_issues)
    for job in jobpages.json():
        updated_at = job['updated_at']
        postdate = date(int(updated_at.split('-')[0]),
                        int(updated_at.split('-')[1]),
                        int(updated_at.split('-')[2][:2]))
        if job['id'] in ids:
            continue
        else:
            ins_job = jobs_table.insert().values(title=job['title'],
                                                 content=job['body'],
                                                 postdate=postdate,
                                                 issuesid=job['id'])
            try:
                connection.execute(ins_job)
            except (exc.SQLAlchemyError, exc.StatementError) as e:
                logging.error(e)
                raise
