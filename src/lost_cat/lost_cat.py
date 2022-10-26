"""
Lost cat will scan and process a range of files
"""
import logging
import multiprocessing as mp
import shelve
import time

from datetime import datetime
from queue import Empty
from sqlite3 import IntegrityError
from sqlalchemy import func

from lost_cat.database.db_utils import DBEngine
from lost_cat.database.schema import URIMD, Domains, DomainMD, ProcessorMD, \
                ProcessorURIs, Processors, URIs, VersionMD, Versions
from lost_cat.utils.module_utils import load_module, load_modulefile
from lost_cat.utils.path_utils import SourceNotValid
from lost_cat.utils.tag_anon import TagAnon

logger = logging.getLogger(__name__)

# <TODO: move this out exception library>
class FeatureNotImplemented(Exception):
    """used for the feature not implemented"""
    def __init__(self, label: str, feature: str, message: str) -> None:
        super().__init__()
        self.label = label
        self.feature = feature
        self.message = message

class ProcessorCannotbeLoaded(Exception):
    """A simple exception to raise already exist error"""

class SourceAlreadyExists(Exception):
    """A simple exception to raise already exist error"""

class ParserAlreadyExists(Exception):
    """A simple exception to raise already exist error"""

class ProcessorAlreadyExists(Exception):
    """A simple exception to raise already exist error"""

class NoHandlersFoundForType(Exception):
    """A simple exception to raise already exist error"""
    def __init__(self, label: str, message: str) -> None:
        super().__init__()
        self.label = label
        self.message = message

class ClassFailedToLoad(Exception):
    """A simple exception to raise already exist error"""
    def __init__(self, label: str, message: str) -> None:
        super().__init__()
        self.label = label
        self.message = message

class ParserFailedToLoad(Exception):
    """A simple exception to raise already exist error"""
    def __init__(self, label: str, base_class: str, message: str) -> None:
        super().__init__()
        self.label = label
        self.base_class = base_class
        self.message = message

class LostCat():
    """
    The Lost Cat Main class

    - Lost cat will accept a range of sources (OS Paths)
    - Scan the folders and files
    - Create an artifact list
    - Create a catalog:
        - Grouped by key tags
        - metadata extracted from files as needed
        - file / folder path metadata included
        - it will also scan and index archive files (zip only atm)
    - provide a set of tools to move, relabel, and so on to help organize
    """
    name = "LostCat"
    version = "0.1.0"

    def __init__(self,
            options: dict = None,
            paths: dict = None) -> None:
        """Initialize the core elements

        Parameters
        ----------
        opttion : dict      A dict that sets the search options for the syste,
            {
                "threads": {

                },
                "<scanner - class name>": {
                    scanner options - see scanner classes for supported options
                },
                "<parsers - class name>": {
                    parser options - see parser classes for support options
                },
                "<converters - class name>" :{
                    converter options - see converter classes for support options
                }
            }

        paths: dict  A dict of paths to use for the components
            {
                "artifacts":    path to artifacts shelve file
                "databasae":    path to the sqlite db
            }

        """
        # a labelled dic of sources,
        # sources are parsed to an object
        self._sources = dict()          # a dict via labels, of uris to scan
        self._processors = dict()         # a dict of the available processors to use
                                        # the processor will only
        self._urihandlers = dict()      # a dictionary of the uri types and the list of
                                        # processor labels to use
        self._fltrhandlers = dict()  # a dictionary of the uri subtypes and the list of
                                        # processor labels to use

        self._parsers = dict()          # a dict of parser, grouped by ext / type
        self._parse_ext = dict()        # a dict of extension used to select the
                                        # correct parser to use
        self._features = ["scanner", "parser", "converter"]     # a set of features to make avaiable
        self._anonobj = None            # the anonymizer class, will look at tags and
                                        # them, using a local cache for consistency

        # caches for updates...
        self._domains = {}              # K: domain          | V: id
        self._uris = {}                 # K: uri             | V: id
        self._urimd = {}                # K: uriid, key      | V: id, value
        self._versions = {}             # K: uriid, modified | V: row
        self._vlatest = {}              # KL uriid           | v: row
        self._versionmd = {}            # K: versionid, key  | V: id, value

        # tags might be better to be set at the scanner, parser level
        self._tags = dict()             # the provided tags

        # set the objects
        if options:
            self._options = options
        else:
            # default to create a phrase profile for the filename
            self._options = {
                "threads": {
                    "count": 3,
                    "stop": True, # tells the system to stop when the in queue is empty
                    "timeout": 2
                }
            }

        # shelve root is the base oath for the shelve file
        # this program will create a shelve for each function run...
        # artifacts - augmented with meatadata and file information
        self._paths = paths
        self._artifacts = None
        self._db = None

        if "artifacts" in paths:
            # a local store for the disovered artifacts
            logger.info("Shelve file: %s", self._paths.get("artifacts", "<missing>"))
            self._artifacts = shelve.open(self._paths.get("artifacts", "<missing>"))

        else:
            logger.info("Database: %s", self._paths.get("database", "<missing>"))
            self._db = DBEngine(connString=self._paths.get("database", "lost-cat.db"))
            self.load_processors()

        # a place to store the processed artifacts, organized
        # by the grouping, and with metadata...
        self._catalog = dict()

    def close(self) -> None:
        """Will save the shelve to the OS"""
        if self._artifacts:
            logger.debug("Closing shelve %s", len(self._artifacts))
            self._artifacts.close()

    def set_tags(self, tags: dict) -> None:
        """Accepts a dictionary of tags expecets:
            alias: dict of k,v pairs, k is field to convert v is the field name
            groups: list of tags to use for grouping
            metadata: list of tags to metadata
            anonimizer: list of tags to run through the anonimizer
            <class name>: { alias, group, metadata}
        """
        logger.debug("Added tags: %s", tags)
        self._tags = tags

    def set_anonimizer(self, anonimizer: TagAnon) -> None:
        """This will set the anonimizer for the class"""
        self._anonobj = anonimizer

    def load_processors(self):
        """Will load the core information from the underlying datastores"""
        if not self._db:
            return
        self._processors = {}

        # load processort metadata if any
        _sql = """SELECT pmd.processorid AS processorid
                , p.uri AS processoruri
                , p. name AS processorname
                , pmd.key AS key
                , pmd.value AS value
            FROM processormd pmd
                INNER JOIN processors p
                    ON p.id = pmd.processorid"""
        pmd_results = self._db.sql(sql=_sql)
        _pmd = {}
        for r in pmd_results:
            if not r.get("processorname"):
                continue
            _pname = r.get("processorname")
            if _pname not in _pmd:
                _pmd[_pname] = {}
            _pmd[_pname][r.get("key")] = r.get("value")

        # load in the tables from the source system...
        _sql = """SELECT p.id AS processorid
                , p.name AS processorname
                , p.uri AS processoruri
            FROM processors p"""

        proc_results = self._db.sql(sql=_sql)
        for r in proc_results:
            try:
                if not r.get("processorname"):
                    continue
                _pname = r.get("processorname")
                if _pname not in self._processors:
                    _pname, _uri, base_class, obj = self.resolve_class(
                                module_path=r.get("processoruri"))
                    if obj:
                        obj.processorid = r.get("processorid")

                    self._processors[_pname] = {
                        "id": r.get("processorid"),
                        "uri": _uri,
                        "class": base_class,
                        "obj": obj,
                        "metadata": _pmd.get(_pname),
                    }

                    _tags = None
                    if not (_tags := self._tags.get("pname")):
                        # load the default _tags
                        if self._tags:
                            _tags ={
                                "alias": self._tags.get("alias", {}),
                                "groups": self._tags.get("groups", {}),
                                "metadata": self._tags.get("metadata", {}),
                                "anonimizer": self._tags.get("anonimizer", {}),
                            }

                    if _tags:
                        self._processors[_pname]["tags"] = _tags

                    self.add_typehandler(obj, _pname)

            except Exception as ex:
                logger.error("Failed to load processor %s",  ex)

        logger.info(self._processors)

    def add_processor(self, label: str = None,
            base_class: object = None,
            module_path: str = None,
            settings: dict = None,
            overwrite: bool = False):
        """will add a processor to the the system, and perform simple
        setting and config loads."""

        _pname, _uri, base_class, obj = self.resolve_class(
                        base_class=base_class,
                        module_path=module_path,
                        settings=settings,
                        overwrite=overwrite)
        _pmd = {
            _pname: {}
        }

        if _pname in self._processors:
            logger.info("Updating class: %s %s", _pname, _uri)
            self._processors[_pname]["base_class"] = base_class
            self._processors[_pname]["obj"] = obj

        else:
            # add the processor to the database
            _db_sess = self._db.session()
            _proc = _db_sess.query(Processors).where(Processors.name == _pname).one_or_none()

            _procmds = []
            if _proc:
                # get the metadata
                for _procmd in list(_db_sess.query(ProcessorMD).where(ProcessorMD.processorid == _proc.id).all()):
                    logger.debug("Proc MD: %s", _procmd)

            else:
                logger.info("Adding class: %s %s", _pname, _uri)

                try:
                    _proc = Processors(name=_pname, uri=_uri)
                    _db_sess.add(_proc)
                    _db_sess.flush()

                    logger.info(_proc)

                    # Add the metadata elements if there are any
                    for _mdk, _mdv in obj.avail_config().get("metadata",{}).items():
                        _proc_md = ProcessorMD(processorid =_proc.id, key = _mdk, value = _mdv)
                        _pmd[_pname][_mdk] = _mdv
                        _procmds.append(_proc_md)

                    _db_sess.add_all(_procmds)
                    _db_sess.flush()
                    _db_sess.commit()

                    if obj:
                        obj.processorid = _proc.id

                except Exception as ex:
                    logger.error("Error adding processor %s %s %s", base_class, module_path, ex)
                    _db_sess.rollback()

                    for row in _db_sess.query(Processors).where(Processors.uri == _uri):
                        logger.info(row)
                        _proc = row

                    logger.info(_proc)

            self._processors[_pname] = {
                        "id": _proc.id,
                        "uri": _proc.uri,
                        "class": base_class,
                        "obj": obj,
                        "metadata": _pmd.get(_pname),
                    }

            _tags = None
            if not (_tags := self._tags.get("pname")):
                # load the default _tags
                if self._tags:
                    _tags ={
                        "alias": self._tags.get("alias", {}),
                        "groups": self._tags.get("groups", {}),
                        "metadata": self._tags.get("metadata", {}),
                        "anonimizer": self._tags.get("anonimizer", {}),
                    }

            if _tags:
                self._processors[_pname]["tags"] = _tags

        self.add_typehandler(obj, _pname)
        #self.add_filterhandler(obj, _pname)

    def resolve_class(self, base_class: object = None,
                        module_path: str = None,
                        rel_path: str = None,
                        settings: dict = None,
                        overwrite: bool = False):
        """ """

        _cls_name = module_path.split('.')[-1] if module_path else None
        logger.info("Name: %s", _cls_name)

        try:
            if module_path:
                logger.info("Loading path: %s", module_path)
                obj = None
                if rel_path:
                    _objs = load_modulefile(folder=module_path, file=rel_path)

                else:
                    _objs = load_module(module = module_path)

                logger.info("OBJS: %s", _objs)
                for _o, _v in _objs.items():
                    logger.info("\t%s => %s", _o, _v)

                _base_class = _objs.get(_cls_name)
                logger.info("Class: %s", _base_class)

                if _base_class:
                    base_class = _base_class
            elif base_class:
                logger.info("Loading obj: %s", base_class)

        except Exception as ex:
            raise ClassFailedToLoad(label=module_path,
                    message="class could not be loaded MODULE") from ex

        if not base_class:
            raise ClassFailedToLoad(label=module_path,
                    message="class could not be loaded MODULE")

        # load the class and extract the
        try:
            obj = base_class(settings=settings)
            _pname = obj.name
            _uri = f"{obj.__module__}.{obj.__class__.__name__}"

        except ImportError as ex:
            raise ClassFailedToLoad(label=base_class,
                    message="class could not be loaded BASE_CLASS") from ex

        # save the processor to the database
        if _pname in self._processors and overwrite is False:
            logger.debug("Class is already loaded %s %s", _pname, _uri)
            return _pname, _uri, base_class, obj

        return _pname, _uri, base_class, obj

    def add_typehandler(self, obj, _pname):
        """ now to set the uritypes it can work with... """
        for _uritype in obj.avail_config().get("uritypes",[]):
            if _uritype not in self._urihandlers:
                self._urihandlers[_uritype] = []
            if _pname not in self._urihandlers[_uritype]:
                self._urihandlers[_uritype].append(_pname)

    def get_sourcequery(self, filters: dict, urimd: list = None, versionmd: list = None, domains: list = None) -> list:
        """Will return a sql string used to query the underlying db
        For example
            SELECT
                u.*,
                pumd.*
            FROM uris u

            -- for the metadata
            INNER JOIN (SELECT
                ium.uriid AS uriid,
                MAX(CASE WHEN ium.key = 'ext' THEN ium.value END) AS ext,
                MAX(CASE WHEN ium.key = 'name' THEN ium.value END) AS name,
                MAX(CASE WHEN ium.key = 'zipfile' THEN ium.value END) AS zipfile
            FROM
                urimd ium
            GROUP BY ium.uriid) AS pumd
                ON u.id = pumd.uriid

            -- for the filter
            INNER JOIN urimd um
                ON u.id = um.uriid AND um.key = 'ext' AND um.value IN ('.dcm')
            WHERE u.domainin in ()
        """

        sel_q = """SELECT u.id AS uriid,
            u.uri_type AS uritype,
            u.uri AS uri"""

        _sel_umd = ""
        _j_umd = ""
        _sel_vmd = ""
        _j_vmd = ""

        if urimd:
            _md_qry = []
            for _md in urimd:
                _md_qry.append(f"MAX(CASE WHEN ium.key = '{_md}' THEN ium.value END) AS {_md}")

            _sel_umd = ", pumd.* "
            _pvt_umd = ", " + ", ".join(_md_qry)
            _umd_qry = f""" INNER JOIN (SELECT ium.uriid AS uriid{_pvt_umd} FROM urimd AS ium GROUP BY ium.uriid) AS pumd ON u.id = pumd.uriid"""

        if versionmd:
            _vmd_qry = []
            for _vmd in versionmd:
                _vmd_qry.append(f"MAX(CASE WHEN vm.key = '{_vmd}' then vm.value END) AS {_vmd}")

            _sel_vmd = _sel_vmd = ", " + ", ".join(_vmd_qry)
            _vmd_qry = " INNER JOIN Versions v ON u.id = v.uriid INNER JOIN VersionsMD vm on v.id = vm.versionid "

        from_q = {
            "URIs": """{q}{sumd}{svmd} FROM URIS u {umd}
                    WHERE u.{field} == {select}""",
            "URIMD":"""{q}{sumd}{svmd} FROM URIS u {umd}
                    INNER JOIN URIMD um ON u.id = um.uriid
                    WHERE um.{field} == \"{select}\"
                    AND um.value IN ({filter})""",
            "VersionsMD": """{q}{sumd}{svmd} FROM URIS u {umd}{vmd}
                    INNER JOIN Versions v ON u.id = v.uriid
                    INNER JOIN VersionsMD vm on v.id = vm.versionid
                    WHERE vm.{field} == \"{select}\"
                    AND vm.value IN ({filter})"""
        }

        _queries = []

        for _fltrtype in filters:
            # table, field, select, filter
            _tbl = _fltrtype.get("table")
            _fld = _fltrtype.get("field")
            _sel = _fltrtype.get("select")
            logger.debug("Filter: %s", _fltrtype)

            _vals = {
                "q": sel_q,
                "field": _fld,
                "select": _sel,
                "sumd": _sel_umd if urimd else "",
                "umd": _umd_qry if urimd else "",
                "svmd": _sel_vmd if urimd else "",
                "vmd": _vmd_qry if versionmd else ""
            }

            #
            if "filter" not in _fltrtype:
                _sql = from_q.get(_tbl,"") \
                        .format(**_vals)
                _queries.append(_sql)
            else:
                _vals["filter"] = "\"{}\"".format(",\"".join(_fltrtype.get("filter",[])))
                _sql = from_q.get(_tbl,"") \
                        .format(**_vals)
                _queries.append(_sql)

            logger.debug("SQ SQL: %s", _sql)

        return _queries

    def load_db_sources(self):
        """will read the sources from the db"""
        if not self._db:
            return

        # load in the tables from the source system...
        """type
                processors []
                uris
                    uri
        """
        self._sources = {}
        sql = """SELECT
                    uris.id AS uriid,
                    uris.uri AS uri,
                    uris.uri_type AS uritype,
                    uris.root AS uriroot,
                    uris.added AS uriadded,
                    uris.deleted AS urideleted,
                    processors.id AS processorid,
                    processors.name AS processorname,
                    processors.uri AS processoruri
                FROM processoruris
                JOIN uris
                    ON uris.id = processoruris.uriid
                JOIN processors
                    ON processors.id = processoruris.processorid
                WHERE uris.root = 1
                    AND uris.deleted IS NULL
                ORDER BY uris.uri_type"""

        for row in self._db.sql(sql=sql):
            # add to the sources dict'
            logger.debug(row)
            _uri_type = row.get("uritype")
            _processor = row.get("processorname")
            _uri = row.get("uri")

            if _uri_type not in self._sources:
                self._sources[_uri_type] = {
                    "processors": [],
                    "uris": {}
                }

            # add the handler to the type
            if _processor not in self._sources[_uri_type]["processors"]:
                self._sources[_uri_type]["processors"].append(_processor)

            # add the uri
            if _uri not in self._sources[_uri_type]["uris"]:
                self._sources[_uri_type]["uris"][_uri] = row.copy()

        #logger.debug(self._sources)

    def add_source(self, processor: str, uri: str,
                isroot: bool = False, overwrite: bool = False) -> dict:
        """It parses the provided source path and
        add to the source list.Build path returns a dict of the uri:
            "type": str
            "uri: str
        """
        logger.debug("Processor: %s URI: %s ", processor, uri)
        if _processor := self._processors.get(processor):
            try:
                _processor["obj"] = _processor.get("class")()
                _uri_obj = _processor.get("obj").build_path(uri=uri)

            except Exception as ex:
                raise ClassFailedToLoad(label=uri,
                        message="Class provided could not be loaded",
                    ) from ex
        else:
            raise ClassFailedToLoad(label=uri,
                    message="Class provided could not be loaded",
                )

        if not _uri_obj:
            raise SourceNotValid(uri=uri, message="missing processor record!")

        logger.debug("Processor: %s", _uri_obj)
        _uritype = _uri_obj.get("type","<>")

        if uri in self._sources.get(_uritype,{}).get("uris",{}) and overwrite is False:
            return self._sources.get(_uritype,{}).get("uris",{}).get(uri,{})

        # add the uri to the sources...
        _procid = _processor.get("id")
        _db_sess = self._db.session()

        # add the domain if needed...
        try:
            _domain = _db_sess.query(Domains).filter(Domains.domain == _uri_obj.get("domain")).one_or_none()
            if not _domain:
                _domain = Domains(domain=_uri_obj.get("domain"), domain_type=_uri_obj.get("domain_type"))
                _db_sess.add(_domain)
                _db_sess.commit()

            _domid = _domain.id

        except Exception as ex:
            logger.error("ERROR adding domain %s %s", _uri_obj, ex)
            # fetch the URI record...
            _db_sess.rollback()

        # add the uri
        try:
            _uri = _db_sess.query(URIs).filter(URIs.uri == uri).one_or_none()
            if not _uri:
                _uri = URIs(uri=uri,
                    uri_type =_uri_obj.get("type"),
                    root = isroot,
                    domainid = _domid)

                _db_sess.add(_uri)
                _uriid = _uri.id
                _db_sess.commit()

        except Exception as ex:
            logger.error("ERROR adding uri %s %s", uri, ex)
            # fetch the URI record...
            _db_sess.rollback()
            for row in list(_db_sess.query(URIs).where(URIs.uri == uri).all()):
                logger.debug(row)
                _uri = row

            logger.debug(_uri)
            _uriid = _uri.id

        try:
            _procuri = _db_sess.query(ProcessorURIs).where(ProcessorURIs.uriid == _uri.id, ProcessorURIs.processorid == _procid).one_or_none()
            if not _procuri:
                _procuri = ProcessorURIs(processorid = _procid, uriid = _uri.id)
                _db_sess.add(_procuri)
                _db_sess.commit()

        except Exception as ex:
            logger.error("ERROR adding processor uri %s %s %s", _procid, uri, ex)
            _db_sess.rollback()

        _uri_obj["uriid"] = _uri.id
        _uri_obj["processorid"] = _procid
        _uri_obj["processorname"] = processor

        # add to teh source dictionary for root items
        if isroot is True:
            if _uritype not in self._sources:
                self._sources[_uritype] = {
                    "processors": [_processor.get("name")],
                    "uris": {}
                }

            self._sources[_uritype]["uris"][uri] = _uri_obj

        return _uri_obj

    def save_queue(self, _out_queue):
        """ Save the data from the queue,
        structured by the following:
            processorid
            domain / md
            uri / md
            version / md"""

        _stats = {
            "loaded": 0,
            "added": 0,
            "updates": 0,
            "deleted": 0
        }

        _db_sess = self._db.session()
        while _out_queue:
            try:
            # set a timeout, and handle the semiphore case too
                o_item = _out_queue.get(timeout=10) if _out_queue else None
                # URIs
                #   -> Metadata
                #   -> Versions
                #       -> metadata
                if o_item == "DONE":
                    break

                logger.debug("Out: %s", o_item)
                # update the database...
                # Domains
                # K: domain          | V: id
                _domain = _db_sess.query(Domains).filter(Domains.domain == o_item.get("domain")).one_or_none()
                if not _domain:
                    _domain = Domains(
                        domain = o_item.get("domain")
                    )
                    _db_sess.add(_domain)
                    _db_sess.flush()

                _domainid = _domain.id

                # domain metadata...
                _domainmds = _db_sess.query(DomainMD).filter(DomainMD.domainid == _domainid).all()
                _domainmd_keys = {}
                for _domainmd in _domainmds:
                    _domainmd_keys[_domainmd.key] = _domainmd.value

                # update the metadata or add if mssing
                _mdadd = []
                for _mdk, _mdv in o_item.get("domainmd",{}).items():
                    _mdval = _domainmd_keys.get(_mdk)
                    if _mdval:
                        if not _mdv:
                            continue

                        if not _mdval or _mdv != _mdval:
                            # perform an update...
                            _db_sess.query(DomainMD) \
                                    .filter_by(domainid=_domainid, key=_mdk) \
                                    .update({
                                        "value": _mdv if _mdv else "<missing>",
                                        "modified": datetime.now()
                                    })

                            _stats["updates"] += 1
                    else:
                        # insert new value
                        if not _mdv:
                            continue

                        _mdrec = DomainMD(
                            domainid = _domainid,
                            key = _mdk if _mdk else "<missing>",
                            value = _mdv,
                            modified = datetime.now()
                        )
                        _mdadd.append(_mdrec)
                        _stats["added"] += 1

                _db_sess.add_all(_mdadd)
                _db_sess.flush()

                # get the uri
                # check for the parent id...
                # if a file in a zip file get the id of the zipfile...
                # else used the base_id

                # have the source uriid that generated the file
                _uriid_source = o_item.get("uriid_source", 0)

                if _uri_zipfile := o_item.get("metadata",{}).get("zipfile"):
                    # the url for the zip file..
                    if _uri_zf := _db_sess.query(URIs).filter(URIs.uri == _uri_zipfile).one_or_none():
                        _uriid_source = _uri_zf.id
                    else:
                        logger.warning("Unable to fidn zipfile id %s", _uri_zipfile)

                # handle zip files as well
                _uri = _db_sess.query(URIs).filter(
                        URIs.uri == o_item.get("uri"),
                        URIs.uriid_parent == _uriid_source).one_or_none()

                if not _uri:
                    logger.debug("ADD: %s", o_item.get("uri"))
                    _uri = URIs(
                            domainid = _domain.id,
                            uri = o_item.get("uri"),
                            uri_type = o_item.get("uri_type"),
                            uriid_parent = _uriid_source,
                            root=False)
                    _db_sess.add(_uri)
                    _db_sess.flush()

                    _stats["added"] += 1

                _uriid = _uri.id

                # add the relationship to the processor id if included...
                if _processorid := o_item.get("processorid"):
                    if not (_procuri := _db_sess.query(ProcessorURIs).filter(
                                    ProcessorURIs.uriid == _uriid,
                                    ProcessorURIs.processorid == _processorid
                            ).one_or_none()):
                        _procuri = ProcessorURIs(
                                processorid = _processorid,
                                uriid = _uriid,
                                added = datetime.now()
                        )
                        _db_sess.add(_procuri)
                        _db_sess.flush()

                        _stats["added"] += 1

                # get the uri metadata
                _urimds = _db_sess.query(URIMD).filter(URIMD.uriid == _uriid).all()
                _urimd_keys = {}
                for _urimd in _urimds:
                    _urimd_keys[_urimd.key] = _urimd.value

                # update the metadata
                # URIMD
                # K: uriid, key      | V: value
                _mdadd = []
                for _mdk, _mdv in o_item.get("metadata",{}).items():
                    _mdval = _urimd_keys.get(_mdk)
                    if _mdval:
                        if not _mdv:
                            continue

                        if not _mdval or _mdv != _mdval:
                            # perform an update...
                            _db_sess.query(URIMD) \
                                    .filter_by(uriid=_uriid, key=_mdk) \
                                    .update({
                                        "value": _mdv if _mdv else "<missing>",
                                        "modified": datetime.now()
                                    })

                            _stats["updates"] += 1
                    else:
                        # insert new value
                        if not _mdv:
                            continue

                        _mdrec = URIMD(
                            uriid = _uriid,
                            key = _mdk if _mdk else "<missing>",
                            value = _mdv,
                            modified = datetime.now()
                        )
                        _mdadd.append(_mdrec)
                        _stats["added"] += 1

                _db_sess.add_all(_mdadd)
                _db_sess.flush()

                # versions
                if o_item.get("versions", {}).get('__latest__'):
                    _subquery = _db_sess.query(
                        Versions,
                        func.rank().over(
                            order_by=Versions.modified.desc(),
                            partition_by=Versions.uriid
                        ).label('rank')
                    ).filter(Versions.uriid == _uri.id
                    ).order_by(Versions.uriid).subquery()

                    _version = _db_sess.query(_subquery).filter(
                            _subquery.c.rank == 1).one_or_none()

                else:
                    _version = _db_sess.query(Versions).filter(
                            Versions.modified == o_item.get("versions", {}).get('modified'),
                            Versions.uriid == _uri.id).one_or_none()

                    # check for changes
                    if _version and (_version.size != o_item.get("versions", {}).get('size') \
                        or _version.modified != o_item.get("versions", {}).get('modified')):

                        logger.info("updated File...%s", o_item.get("uri"))
                        logger.info("\tOItem: %s", o_item.get("versions", {}))
                        logger.debug("\tOrig: Size: %s\n\t      Mod:  %s", _version.size, _version.modified)
                        logger.debug("\tNew:  Size: %s\n\t      Mod:  %s", o_item.get("versions", {}).get('size'), o_item.get("versions", {}).get('modified'))
                        _version = None

                if not _version:
                    _vmod = o_item.get("versions", {}).get('modified')
                    _version = Versions(
                            uriid = _uriid,
                            modified = o_item.get("versions", {}).get('modified'),
                            size = o_item.get("versions", {}).get('size'))

                    _db_sess.add(_version)
                    _db_sess.flush()

                _vid = _version.id

                # version metadata
                _versionmds = _db_sess.query(VersionMD).filter(VersionMD.versionid == _version.id).all()
                _vmd_keys = {}
                for _versionmd in _versionmds:
                    _vmd_keys[_versionmd.key] = _versionmd.value

                # # Version Metadata
                # K: versionid, key  | V: id, value
                _vmdadd = []
                for _vk, _vv in o_item.get("versions", {}).get("versionmd",{}).items():
                    _vmdref = _vmd_keys.get(_vk)
                    _vv = str(_vv)

                    if _vmdref and _vmdref != _vv:
                        # check for changes...
                        _db_sess.query(VersionMD) \
                                .filter_by(versionid=_version.id, key=_vk) \
                                .update({
                                    "value": _vv,
                                    "modified": datetime.now()
                                })

                        _stats["updates"] += 1
                    else:
                        # added new metadata
                        if not _vv:
                            continue

                        _vmdobj = VersionMD(
                            versionid = _vid,
                            key = _vk,
                            value = _vv,
                            modified = datetime.now()
                        )

                        _vmdadd.append(_vmdobj)

                _db_sess.add_all(_vmdadd)
                _db_sess.flush()

            except IntegrityError as ex:
                _db_sess.rollback()
                logger.error(ex)

            except Empty:
                break

        _db_sess.commit()
        logger.info(_stats)

    def fetch_tree(self, uri:str, zipuri:str = None, modified: datetime = None) -> dict:
        """Will return the
            uri,
            urimd,
            version,
            versionmd
        dataset."""
        _db_sess = self._db.session()

        # get the uri
        # handle zip files as well
        if zipuri:
            _uri = _db_sess.query(URIs).join(URIMD).filter(
                    URIs.uri == uri,
                    URIMD.key == 'zipfile',
                    URIMD.value == zipuri).one_or_none()
        else:
            _uri = _db_sess.query(URIs).filter(URIs.uri == uri).one_or_none()

        if not _uri:
            logger.info("ADD: %s", _uri)
        logger.info(_uri)

        _uriid = _uri.id

        # get the uri metadata
        _urimds = _db_sess.query(URIMD).filter(URIMD.uriid == _uriid).all()
        _urimd_keys = {}
        for _urimd in _urimds:
            _urimd_keys[_urimd.key] = _urimd.value

        logger.info(_urimd_keys)

        # versions
        if modified:
            logger.info("Date: %s", modified)
            _version = _db_sess.query(Versions).filter(
                    Versions.modified == modified, #o_item.get("versions", {}).get('modified'),
                    Versions.uriid == _uri.id).one_or_none()
        else:
            logger.info("User latest...")
            _subquery = _db_sess.query(
                Versions,
                func.rank().over(
                    order_by=Versions.modified.desc(),
                    partition_by=Versions.uriid
                ).label('rank')
            ).filter(Versions.uriid == _uri.id
            ).order_by(Versions.uriid).subquery()

            _version = _db_sess.query(_subquery).filter(
                    _subquery.c.rank == 1).one_or_none()

            logger.info(_version)

        logger.info(_version)
        if not _version:
            logger.info("ADD: %s", _version)

        # version metadata
        _versionmds = _db_sess.query(VersionMD).filter(VersionMD.versionid == _version.id).all()
        _vmd_keys = {}
        for _versionmd in _versionmds:
            _vmd_keys[_versionmd.key] = _versionmd.value

        logger.info(_vmd_keys)

    def catalog_artifacts(self) -> dict:
        """Will scan the sources and load a dictionary with the found files,
        it'll use the template list for extensions to use.
        <<for web addresses, it'll need a scraper built>>"""
        _data = {
            "start": time.time(),
            "processors": [],
        }


        # run through the processor list and build a queue for each one...
        _in_queues = {}
        _out_queue = mp.Queue()
        _processors = []

        for uritype, sourceobj in self._sources.items():
            logger.debug("Uri Type: %s\tObj: %s", uritype, sourceobj)

            # <TODO: add a check to match type to a processor>
            for _pname in sourceobj.get("processors"):
                if _pname not in _processors:
                    logger.debug("Name: %s\tInitiate queue", _pname)
                    _processors.append(_pname)
                    # add as a queue
                    _in_queues[_pname] = mp.Queue()

                for _src, _uri_obj in sourceobj.get("uris").items():
                    logger.debug("Name: %s\tAdd: %s", _pname, _uri_obj)
                    _in_queues[_pname].put(_uri_obj)

        # create a thread for each processor...
        for _pname, _que in _in_queues.items():
            #
            _processor = self._processors.get(_pname, {})
            logger.debug("Name: %s\n\tProcessor: %s", _pname, _processor)

            obj = _processor.get("obj")
            if not obj:
                #
                raise ClassFailedToLoad(label=_pname, message="Class didn't load!")

            obj.processorid = _processor.get("id")
            obj.in_queue(in_queue=_que)
            obj.out_queue(out_queue=_out_queue)

            # scan returns on completion
            obj.scan()

        _data["load"] = time.time(),

        # process the output
        _out_queue.put("DONE")

        self.save_queue(_out_queue)

        _data["end"] = time.time(),
        _data["processors"] = _processor

        return _data

    def parse_artifacts(self):
        """Will load the """

        logger.debug("Processors")
        for _pk, _pv in self._processors.items():
            logger.debug("Proc: %s\n\t\tVal: %s", _pk, _pv)

        logger.debug("Handlers")
        for _pk, _pv in self._urihandlers.items():
            logger.debug("Proc: %s\n\t\tVal: %s", _pk, _pv)

        _pnames = self._urihandlers.get("file")
        logger.debug(_pnames)
        if not _pnames:
            raise NoHandlersFoundForType(label="file", message="No handler found for type")

        _out_queue = mp.Queue()
        _in_queue = {}

        for _pname in _pnames:
            _proc = self._processors.get(_pname,{})
            logger.debug("Proc: %s", _proc)
            obj = _proc.get("obj")
            if not obj:
                logger.debug("missing object: %s", _pname)
                continue

            _settings = obj.avail_config()

            #<TODO: change the query set up to a dict of wueries include field lists
            #Filters
            #   <function>
            #       <tables>
            #                table alias join criteria
            #        fields  table
            #                    field: alias
            #        Pivot   table
            #                    field alias
            #        filter  table
            #                    field value | [values]
            _queries = self.get_sourcequery(filters=_settings.get("source",[]),
                        urimd=_settings.get("uri_metadata",[]),
                        versionmd=_settings.get("version_metadata",[]))

            for _qry in _queries:
                logger.debug("SQL: %s", _qry)
                _in_queue[_pname] = mp.Queue()
                _rows = self._db.sql(sql=_qry)
                for _row in _rows:
                    _in_queue[_pname].put(_row)

            obj.processorid = _proc.get("id")
            obj.in_queue(in_queue=_in_queue.get(_pname))
            obj.out_queue(out_queue=_out_queue)

            # set the helper functions...
            if _anonfunc := obj.avail_functions().get("anonimizer"):
                try:
                    _anonfunc(anonimizer=self._anonobj)
                except Exception as ex:
                    logger.warning("No Anonimizer set\n\t%s", ex)


            logger.debug("Setting tags...")
            if _tags := _proc.get("tags",{}):
                logger.debug("\tChecking proc settings...")
                for _fld in ["alias", "groups", "metadata"]:
                    if _func := obj.avail_functions().get(f"tags_{_fld}"):
                        logger.debug("\t\t%s", _fld)
                        _func(tags=_tags.get(_fld))
            elif self._tags:
                logger.debug("\tChecking generic settings...")
                for _tn in ["alias", "groups", "meatadata"]:
                    if _fn := obj.avail_functions().get(f"tags_{_tn}"):
                        logger.debug("\t\t%s => %s", _tn, _fn)
                        _fn(tags=self._tags.get(f"{_fn}",[]))

            else:
                logger.debug("\tChecking default...")
                if (_fn_def := obj.avail_functions().get(f"default_alias")) and \
                        (_fn := obj.avail_functions().get(f"tags_alias")):
                    logger.debug("\t\t%s => %s", _fn_def, _fn)
                    _fn(tags=_fn_def)
                if (_fn_def := obj.avail_functions().get(f"default_groups")) and \
                        (_fn := obj.avail_functions().get(f"tags_groups")):
                    logger.debug("\t\t%s => %s", _fn_def, _fn)
                    _fn(tags=_fn_def)
                if (_fn_def := obj.avail_functions().get(f"default_metadata")) and \
                        (_fn := obj.avail_functions().get(f"tags_metadata")):
                    logger.debug("\t\t%s => %s", _fn_def, _fn)
                    _fn(tags=_fn_def)

            # initi the parser...
            logger.debug("run the parser function...")
            obj.avail_functions().get("parser")()

        # process the output
        _out_queue.put("DONE")
        self.save_queue(_out_queue)
