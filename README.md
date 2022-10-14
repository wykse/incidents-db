# incidents-db
Get incident data from [City of Oakland's public data API](https://data.oaklandca.gov/Public-Safety/CrimeWatch-Maps-Past-90-Days/ym6k-rx7a) and save to a SQLite database.

Duplicate rows are not inserted into the database. However, duplicate incidents may be inserted because incidents may be updated later. Since each case can have multiple incidents, I do not know if a case has an updated incident or an additional incident.

## Usage
`python incidents_db.py`

A Socrata Open Data API app token (`SODA_APP_TOKEN` in .env) is not necessary.
