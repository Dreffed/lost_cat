"""A module to wrap the database functions and allow the syst4em to wru"""
import logging

from lost_cat.database.schema import Base
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker, session

logger = logging.getLogger(__name__)

class DBEngine():
    """"""
    def __init__(self, connString: str = "sqlite:///lost-cat.db") -> None:
        """"""
        self.engine = create_engine(connString, echo=False)

        # create the mapping objects...
        Base.metadata.create_all(self.engine)
        self.metadata = MetaData()
        self.session = sessionmaker(bind=self.engine)

    def session(self) -> session:
        """"""
        if not self.session:
            self.session = sessionmaker(bind=self.engine)
        return self.session

    def close(self):
        """"""
        pass

    def table(self, tablename: str):
        """"""
        return Table(tablename, self.metadata, autoload=True, autoload_with=self.engine)

    def tables_list(self) -> dict:
        """"""
        conn = self.engine.connect()
        _data = []
        _res = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
        _keys = _res.keys()
        for _row in list(_res):
            _rout = {}
            for _rid, _rc in enumerate(_keys):
                _rout[_rc] = _row[_rid]
            _data.append(_rout)

        return _data

    def sql(self, sql: str) -> list:
        """Returns a dictionary of objects"""
        _data = []
        _db_sess = self.session()
        _res = _db_sess.execute(sql)
        _keys = _res.keys()
        logger.debug("COLUMNS: %s", _keys)
        for _row in list(_res.fetchall()):
            _rout = {}
            for _rid, _rc in enumerate(_keys):
                _rout[_rc] = _row[_rid]
            _data.append(_rout)
            #logger.debug("ROW: %s", _rout)

        return _data
