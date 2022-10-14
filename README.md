# incidents-db
Get incident data and save to a database.

Duplicate rows are not inserted into the database. However, duplicate incidents may be inserted because incidents may be updated later. Since each case can have multiple incidents, I do not know if a case has an updated incident or an additional incident.

## Usage
`python incidents_db.py`
