"""A module to wrap the database functions and allow the syst4em to wru"""
import logging

from lost_cat.database.schema import mapper_registry
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, session

logger = logging.getLogger(__name__)

class DBEngine():
    """"""
    def __init__(self, connString: str = "sqlite:///lost-cat.db") -> None:
        """"""
        self._engine = create_engine(connString, echo=False)

        # create the mapping objects...
        self._metadata = MetaData()
        mapper_registry.metadata.create_all(bind=self._engine)
        self._metadata.create_all(self._engine)

    def tables(self) -> dict:
        """"""
        conn = self._engine.connect()
        _data = []
        _res = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
        _keys = _res.keys()
        for _row in list(_res):
            _rout = {}
            for _rid, _rc in enumerate(_keys):
                _rout[_rc] = _row[_rid]
            _data.append(_rout)

        return _data

    def session(self) -> session:
        """"""
        _session = sessionmaker(bind=self._engine)
        return _session()

    def sql(self, sql: str) -> list:
        """Returns a dictionary of objects"""
        _data = []
        _db_sess = self.session()
        _res = _db_sess.execute(sql)
        _keys = _res.keys()
        for _row in list(_res):
            _rout = {}
            for _rid, _rc in enumerate(_keys):
                _rout[_rc] = _row[_rid]
            _data.append(_rout)

        return _data
