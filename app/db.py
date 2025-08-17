from pony.orm import Database, Required, PrimaryKey
from datetime import date, time

db = Database()
db.bind(provider='sqlite', filename='trackfitter.db', create_db=True)

class Trening(db.Entity):
    id_treninga = PrimaryKey(int, auto=True)
    datum = Required(date)
    vrijeme = Required(time)
    intenzitet = Required(int)        # 1–10
    trajanje = Required(int)          # minute
    vrsta_treninga = Required(str)    # npr. "trčanje"

db.generate_mapping(create_tables=True)
