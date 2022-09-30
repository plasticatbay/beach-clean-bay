import pandas as pd
from sqlalchemy.orm import sessionmaker
from db import init_db, Beach, TeamMember, WeightData

def import_csv():
    print("Importing CSV data")
    return {
        "team": pd.read_csv("csvdata/Team_members.csv", header=None, names=["Id", "Name", "Team"]),
        "weight": pd.read_csv("csvdata/WeightData.csv", header=None, names=["Id", "Beach", "Lat", "Longit", "Weight", "Dates", "team", "person"]),
        "beach": pd.read_csv("csvdata/Beach2coord.csv", header=None, names=["Id", "Beach", "Lat", "Lon", "Country", "State"]),
    }

def insert_data(engine, data):
    with engine.connect() as conn, conn.begin():
        print("Inserting TeamMember data")
        data["team"].to_sql(TeamMember.__tablename__, conn, if_exists="replace", index_label="Id", index=False)

        print("Inserting WeightData data")
        data["weight"].to_sql(WeightData.__tablename__, conn, if_exists="replace", index_label="Id", index=False)

        print("Inserting Beach data")
        data["beach"].to_sql(Beach.__tablename__, conn, if_exists="replace", index_label="Id", index=False)
    

def run():
    engine = init_db(drop=True)

    data = import_csv()
    insert_data(engine, data)

    Session = sessionmaker(bind=engine)
    session = Session()

    print("\n\nSample data from database:")
    for i in session.query(Beach).order_by(Beach.Id)[0:4]:
        print("  ", i)
    for i in session.query(TeamMember).order_by(TeamMember.Id)[0:4]:
        print("  ", i)
    for i in session.query(WeightData).order_by(WeightData.Id)[0:4]:
        print("  ", i)


if __name__ == '__main__':
    run()
