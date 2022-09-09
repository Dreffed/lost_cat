import json
import logging
import sqlite3

from collections import deque
import time
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from lost_cat.database.schema import SourceUris, SourceValues, SourceMaps, \
        SubPaths, LCItems ,LCItemVersions, \
        NameProfiles, NameProfileParts, EntityTypes, \
        mapper_registry
from lost_cat.database.db_utils import DBEngine
from lost_cat.utils.path_utils import get_filename, scan_files

logger = logging.getLogger(__name__)


def main():
    """will load the data into the database"""

if __name__ == "__main__":
    """Run the clss for test"""
    import sys
    from lost_cat.utils.path_utils import build_path
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    logging.getLogger('sqlalchemy').setLevel(logging.ERROR)

    logger = logging.getLogger(name=__name__)

    db_dirty = False
    obj = DBEngine()
    db_sess = obj.session()

    sql = """SELECT
            s.s_id,
            s.s_type,
            s.s_uri,
            s.s_auth,
            COUNT(sm.s_id) AS s_values
        FROM sourceuris s
            LEFT JOIN sourcemaps sm
                ON s.s_id = sm.s_id
        GROUP BY
            s.s_id,
            s.s_type,
            s.s_uri,
            s.s_auth"""

    sources = obj.sql(sql=sql)
    if not sources:
        try:
            # sa_type: ENV | STRING | CONFIG | etc.
            db_dirty = True
            sa_r = SourceValues(sv_type="ENV", sv_label="SYSTEM", sv_value="%SYSTEM%")
            res = db_sess.add(sa_r)
            res = db_sess.flush()

            sa_r = SourceValues(sv_type="ENV", sv_label="HOME", sv_value="%HOME%")
            res = db_sess.add(sa_r)
            res = db_sess.flush()

            rows = []

            # s_type: FileSystem | SQL| HTTP | FTP | SAP | LiveLink | DMS etc.
            # s_auth: None | Token | User:Pass | OAuth
            rows.append(SourceUris(s_type="Folder", s_uri="C:/users/ms/Documents", s_auth="None"))

            #for fld in ['Pictures', 'Gallery', 'Dropbox', 'Music', 'Videos', 'OneDrive', 'MSO - thoughtswinsystems.com']:
            #    rows.append(SourceUris(s_type="Folder", s_uri=f"D:/users/ms/{fld}", s_auth="None"))

            #for fld in ['Purge', 'archives']:
            #    rows.append(SourceUris(s_type="Folder", s_uri=f"D:/{fld}", s_auth="None"))

            #for fld in ['Documents', 'Pictures', 'ebooks', 'google']:
            #    rows.append(SourceUris(s_type="Folder", s_uri=f"E:/users/ms/{fld}", s_auth="None"))

            res = db_sess.add_all(rows)
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
    if db_dirty:
        db_sess.commit()

    # scan the paths...
    # this should be preloaded with database objects
    folder_dict = {}
    file_queue = deque()

    cat_options = {
                "splitfolders": True,
                "splitextension": True,
                "stats": True
            }

    timeit = {
        "scan": {
            "items":0,
            "folders":0,
            "files":0,
            "start": time.time()
        }
    }

    start = time.time()
    sources = db_sess.execute(select(SourceUris)).fetchall() # -obj.sql(sql=sql)
    for row in sources:
        logger.info(type(row[0]))
        logger.info(row[0])
        db_source = row[0]

        count = 0
        folder_count = 0
        file_count = 0
        uri_obj = build_path(uri=db_source.s_uri, path_type=db_source.s_type)
        logger.info(uri_obj)
        uri = get_filename(file_dict=uri_obj)
        start_it = time.time()
        try:
            for idx, fnd_file in enumerate(scan_files(uri, options=cat_options)):
                file_uri = get_filename(file_dict=fnd_file)
                folder_uri = get_filename(file_dict={
                    "type": "folder",
                    "root": fnd_file.get("root"),
                    "folders": fnd_file.get("folders")
                })

                fnd_file["source"] = db_source
                fnd_file["source_id"] = db_source.s_id
                fnd_file["source_uri"] = db_source.s_uri
                fnd_file["folder_uri"] = folder_uri
                fnd_file["file_uri"] = file_uri

                logger.info(fnd_file)

                if folder_uri not in folder_dict:
                    folder_count += 1
                    folder_dict[folder_uri] = {}

                if file_uri not in folder_dict.get(folder_uri, {}):
                    folder_dict[folder_uri][file_uri] = fnd_file
                    file_count  += 1

                count += 1
                file_queue.append(fnd_file)

        except FileNotFoundError as ex:
            logger.error("%s => %s", uri, ex)

        if db_source.s_id not in timeit:
            timeit[db_source.s_id] = {
                "items": count,
                "folders": folder_count,
                "files": file_count,
                "start": start_it,
            }

        timeit["scan"]["items"] = timeit.get("scan", {}).get("items", 0) + count
        timeit["scan"]["folders"] = timeit.get("scan", {}).get("folders", 0) + folder_count,
        timeit["scan"]["files"] = timeit.get("scan", {}).get("files", 0) + file_count
        timeit["scan"]["end"] = time.time()

        logger.info("%s | %s | %s => %s", count, folder_count, file_count, time.time() - start_it)

    logger.info("%s | %s => %s", len(file_queue), len(folder_dict), time.time() - start)

    #<TODO Resolve update / Add Code>
    #<TODO Resolve Foreign Key inserts / updates>
    # process the file_queue and perform bulk insert...
    start = time.time()
    db_objects = []
    for folder_uri, fnd_files in folder_dict.items():
        # break out the folders...
        start_it = time.time()
        db_folder = SubPaths(sp_uri=folder_uri)
        db_folder.s_id = fnd_files.get("source_id")
        db_sess.flush()

        db_bulk_vers = []
        db_bulk_files = []
        for file_uri, fnd_file in fnd_files.items():
            db_file = LCItems(lci_uri=file_uri,
                    lci_type=fnd_file.get("type"),
                    lci_name=fnd_file.get("file", fnd_file.get("name", "missing")),
                    lci_ext=fnd_file.get("ext"))

            db_vers = LCItemVersions(iv_size=fnd_file.get("size",0),
                    iv_created=fnd_file.get("created"),
                    iv_modified=fnd_file.get("modified"))

            db_vers.lci_id = db_file.lci_id

            db_file.lci_versions.append(db_vers)
            db_bulk_vers.append(db_vers)
            db_bulk_files.append(db_file)

        db_sess.bulk_save_objects(db_bulk_files)
        db_sess.bulk_save_objects(db_bulk_vers)
        db_sess.flush()

        db_folder.sp_items.extend(db_bulk_files)
        logger.info("%s => %s", count, time.time() - start_it)

        # perform the insert...
        db_objects.append(db_folder)

    logger.info("%s | %s => %s", len(db_objects), len(folder_dict), time.time() - start)

    # now we
    db_sess.bulk_save_objects(db_objects)
    db_sess.commit()

    logger.info(json.dumps(timeit))

    obj = None