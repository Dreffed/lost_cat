from __future__ import annotations
import logging

from dataclasses import dataclass, field
from datetime import datetime
from typing import List

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import registry, relationship
from sqlalchemy.schema import PrimaryKeyConstraint, UniqueConstraint, ForeignKey

logger = logging.getLogger(__name__)

mapper_registry = registry()

@mapper_registry.mapped
@dataclass
class EntityTypes:
    """Tracks the versions of the found items"""
    __tablename__ = "entitytypes"
    __sa_dataclass_metadata_key__ = "sa"
    __table_args__ = (UniqueConstraint("et_type", "et_ext", name="et_unc"), )

    et_id:            int = field(
            init=False, metadata={"sa": Column(Integer, primary_key=True)}
        )
    et_type:           str = field(default=None, metadata={"sa": Column(String(10))})
    et_ext:            str = field(default=None, metadata={"sa": Column(String(10))})
    et_descr:          str = field(default=None, metadata={"sa": Column(String(1024))})
    et_config:         str = field(default=None, metadata={"sa": Column(String(4048))})

@mapper_registry.mapped
@dataclass
class LCItemMetadata:
    """Tracks the versions of the found items"""
    __tablename__ = "itemmetadata"
    __sa_dataclass_metadata_key__ = "sa"
    __table_args__ = (UniqueConstraint("iv_id", "imd_key", name="imd_unc"), )

    imd_id:            int = field(
            init=False, metadata={"sa": Column(Integer, primary_key=True)}
        )
    iv_id:             int = field(
            init=False, metadata={"sa": Column(ForeignKey("itemversions.iv_id"))}
        )
    imd_key:           str = field(default=None, metadata={"sa": Column(String(255))})
    imd_type:          str = field(default=None, metadata={"sa": Column(String(10))})
    imd_value:         str = field(default=None, metadata={"sa": Column(String(4048))})

@mapper_registry.mapped
@dataclass
class LCItemVersions:
    """Tracks the versions of the found items"""
    __tablename__ = "itemversions"
    __sa_dataclass_metadata_key__ = "sa"
    __table_args__ = (UniqueConstraint("lci_id", "iv_modified", name="lciv_unc"), )

    iv_id:             int = field(
            init=False, metadata={"sa": Column(Integer, primary_key=True)}
        )
    lci_id:            int = field(
            init=False, metadata={"sa": Column(ForeignKey("items.lci_id"))}
        )

    iv_size:       str = field(default=None, metadata={"sa": Column(Integer)})
    iv_created:    datetime = field(default=None, metadata={"sa": Column(DateTime)})
    iv_modified:   datetime = field(default=None, metadata={"sa": Column(DateTime)})

    lci_metadata:   List[LCItemMetadata] = field(default_factory=list,
            metadata={"sa": relationship("LCItemMetadata")})

@mapper_registry.mapped
@dataclass
class LCItems:
    """The objects found in the underlying paths"""
    __tablename__ = "items"
    __sa_dataclass_metadata_key__ = "sa"
    __table_args__ = (UniqueConstraint("lci_uri"), )

    lci_id:             int = field(
            init=False, metadata={"sa": Column(Integer, primary_key=True)}
        )
    sp_id:          int = field(
            init=False, metadata={"sa": Column(ForeignKey("subpaths.sp_id"))}
        )

    lci_uri:        str = field(default=None, metadata={"sa": Column(String(4048))})
        # full path to item
    lci_type:       str  = field(default=None, metadata={"sa": Column(String(10))})
        # File | Stream | BLOB etc.
    lci_name:       str = field(default=None, metadata={"sa": Column(String(255))})
    lci_ext:        str = field(default=None, metadata={"sa": Column(String(10))})

    lci_versions:   List[LCItemVersions] = field(default_factory=list,
            metadata={"sa": relationship("LCItemVersions")})

@mapper_registry.mapped
@dataclass
class SubPaths:
    """The subpaths (folders) encouvtered in the scan"""
    __tablename__ = "subpaths"
    __sa_dataclass_metadata_key__ = "sa"
    __table_args__ = (UniqueConstraint("sp_uri", name="sp_unc"), )

    sp_id:          int = field(
            init=False, metadata={"sa": Column(Integer, primary_key=True)}
        )
    s_id:           int = field(
            init=False, metadata={"sa": Column(ForeignKey("sourceuris.s_id"))}
        )

    sp_uri:         str = field(default=None, metadata={"sa": Column(String(4048))})

    sp_items:       List[LCItems] = field(default_factory=list,
            metadata={"sa": relationship("LCItems")})

@mapper_registry.mapped
@dataclass
class SourceValues:
    """A Key Value form of table to assign values to the Source system"""
    __tablename__ = "sourcevalues"
    __sa_dataclass_metadata_key__ = "sa"
    __table_args__ = (UniqueConstraint("sv_type", "sv_label", name="sv_unc"), )

    sv_id:          int = field(
            init=False, metadata={"sa": Column(Integer, primary_key=True)}
        )

    sv_type:        str = field(default=None, metadata={"sa": Column(String(10))})
        # ENV | STRING | CONFIG | etc.
    sv_label:       str = field(default=None, metadata={"sa": Column(String(255))})
    sv_value:       str = field(default=None, metadata={"sa": Column(String(255))})
    sv_uri:         str = field(default=None, metadata={"sa": Column(String(255))})

@mapper_registry.mapped
@dataclass
class SourceUris:
    """Tracks the sources in the system"""
    __tablename__ = "sourceuris"
    __sa_dataclass_metadata_key__ = "sa"
    __table_args__ = (UniqueConstraint("s_uri", name="s_unc"), )

    s_id:          int = field(
            init=False, metadata={"sa": Column(Integer, primary_key=True)}
        )
    s_type:         str = field(default=None, metadata={"sa": Column(String(10))})
        # FileSystem | SQL| HTTP | FTP | SAP | LiveLink | DMS etc.
    s_uri:          str = field(default=None, metadata={"sa": Column(String(4048))})
    s_auth:         str = field(default=None, metadata={"sa": Column(String(10))})
        # None | Token | User:Pass | OAuth
    sa_paths:       list[SubPaths] = field(default_factory=list,
            metadata={"sa": relationship("SubPaths")})

@mapper_registry.mapped
@dataclass
class SourceMaps:
    """"""
    __tablename__ = "sourcemaps"
    __sa_dataclass_metadata_key__ = "sa"
    __table_args__ = (PrimaryKeyConstraint("sv_id", "s_id", name="sm_ids"), )

    sv_id:          int = field(default=None, metadata={"sa": Column(Integer)})
    s_id:           int = field(default=None, metadata={"sa": Column(Integer)})

@mapper_registry.mapped
@dataclass
class NameProfileParts:
    """The parts of the profile found..."""
    __tablename__ = "nameprofileparts"
    __sa_dataclass_metadata_key__ = "sa"

    prp_id:         int = field(
            init=False, metadata={"sa": Column(Integer, primary_key=True)}
        )
    pr_id:           int = field(
            init=False, metadata={"sa": Column(ForeignKey("nameprofiles.pr_id"))}
        )

    prp_value:      str = field(default=None, metadata={"sa": Column(String(255))})
    prp_start:      int = field(default=None, metadata={"sa": Column(Integer)})
    prp_end:        int = field(default=None, metadata={"sa": Column(Integer)})

@mapper_registry.mapped
@dataclass
class NameProfiles:
    """Stored the breakdown of the names discovered"""
    __tablename__ = "nameprofiles"
    __sa_dataclass_metadata_key__ = "sa"
    __table_args__ = (PrimaryKeyConstraint("pr_phrase", name="pr_unc"), )

    pr_id:          int = field(
            init=False, metadata={"sa": Column(Integer, primary_key=True)}
        )
    pr_phrase:      str = field(default=None, metadata={"sa": Column(String(4048))})
    pr_short:       str = field(default=None, metadata={"sa": Column(String(50))})
    pr_normal:      str = field(default=None, metadata={"sa": Column(String(255))})
    pr_parts:       list[NameProfileParts] = field(default_factory=list,
            metadata={"sa": relationship("NameProfileParts")})
