"""A module to wrap the database functions and allow the syst4em to wru"""
import logging
import sqlite3

from sqlalchemy import create_engine, MetaData, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker, session
from schema import SourceMaps, SourceUris, SubPaths, SourceValues, LCItems ,LCItemVersions, NameProfiles, NameProfileParts, mapper_registry

logger = logging.getLogger(__name__)

class DBEngine():
    """"""
    def __init__(self, connString: str = "sqlite:///lost-cat.db") -> None:
        """"""
        self._engine = create_engine(connString, echo=True)

        # create the mapping objects...
        self._metadata = MetaData()
        mapper_registry.metadata.create_all(bind=self._engine)
        self._metadata.create_all(self._engine)

    def run(self) -> object:
        """"""
        conn = self._engine.connect()
        res = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
        for r in res.fetchall():
            print(r)

    def session(self) -> session:
        """"""
        Session = sessionmaker(bind=self._engine)
        return Session()

if __name__ == "__main__":
    """Run the clss for test"""
    import sys
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    logger = logging.getLogger(name=__name__)

    db_dirty = False
    obj = DBEngine()
    logger.info(obj.run())

    db_sess = obj.session()

    rows = list(db_sess.execute(select(SourceUris).order_by(SourceUris.s_type)))
    for r in rows:
        logger.info(r)

    rows = list(db_sess.execute(select(SourceValues).order_by(SourceValues.sv_label)))
    for r in rows:
        logger.info(r)

    try:
        # sa_type: ENV | STRING | CONFIG | etc.
        db_dirty = True
        sa_r = SourceValues(sv_type="ENV", sv_label="SYSTEM", sv_value="%SYSTEM%")
        res = db_sess.add(sa_r)
        res = db_sess.flush()

        sa_r = SourceValues(sv_type="ENV", sv_label="HOME", sv_value="%HOME%")
        res = db_sess.add(sa_r)
        res = db_sess.flush()

        # s_type: FileSystem | SQL| HTTP | FTP | SAP | LiveLink | DMS etc.
        # s_auth: None | Token | User:Pass | OAuth
        s_r = SourceUris(s_type="FileSystem", s_uri="%HOME%/Documents", s_auth="None")
        res = db_sess.add(s_r)
        res = db_sess.flush()

        s_m = SourceMaps(sv_id=sa_r.sv_id, s_id=s_r.s_id)
        res = db_sess.add(s_m)
        res = db_sess.flush()

    except IntegrityError as ex:
        logger.error("%s", ex)
        db_dirty = False
        db_sess.rollback()

    except sqlite3.IntegrityError as ex:
        logger.error("%s", ex)
        db_dirty = False
        db_sess.rollback()

    except Exception as ex:
        logger.error("%s", ex)
        db_dirty = False
        db_sess.rollback()

    # """
    rows = list(db_sess.execute(select(SourceUris).order_by(SourceUris.s_type)))
    for r in rows:
        logger.info(r)

    rows = list(db_sess.execute(select(SourceValues).order_by(SourceValues.sv_label)))
    for r in rows:
        logger.info(r)

    if db_dirty:
        db_sess.commit()

    obj = None
