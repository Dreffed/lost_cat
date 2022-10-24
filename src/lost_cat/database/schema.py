from sqlalchemy import Column, ForeignKey, func
from sqlalchemy import Integer, String, DateTime, Boolean, UniqueConstraint
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship, backref

Base = declarative_base()

class Processors(Base):
    __table_args__ = {'extend_existing': True}
    __tablename__ = "processors"
    id = Column(Integer, primary_key=True)
    name = Column(String(30))
    uri = Column(String(), unique = True)
    rel_path = Column(String(), unique = True)
    added = Column(DateTime, default = func.now())

    # joins
    #uris = relationship("URIs", secondary= "processoruris") #back_populates = "processor")
    pmd = relationship("ProcessorMD")

    def __repr__(self):
        return f"Processor(id={self.id!r}, name={self.name!r})"

class ProcessorMD(Base):
    __table_args__ = {'extend_existing': True}
    __tablename__ = "processormd"
    processorid = Column(Integer, ForeignKey("processors.id"), primary_key = True)
    key = Column(String(255), primary_key = True)
    added = Column(DateTime, default = func.now())
    value = Column(String())

    def __repr__(self):
        return f"Processor MD(id={self.id!r}, key={self.key!r}, value={self.value!r})"

class Domains(Base):
    __table_args__ = {'extend_existing': True}
    __tablename__ = "domains"
    id = Column(Integer, primary_key=True)
    domain = Column(String(), unique = True)
    domain_type = Column(String(15))

    # joins
    dmd = relationship("DomainMD")
    domains = relationship("URIs")

    def __repr__(self):
        return f"Domain(id={self.id!r}, name={self.domain!r})"

class DomainMD(Base):
    __table_args__ = {'extend_existing': True}
    __tablename__ = "domainmd"
    domainid = Column(Integer, ForeignKey("domains.id"), primary_key = True)
    key = Column(String(255), primary_key = True)
    added = Column(DateTime, default = func.now())
    modified = Column(DateTime)
    value = Column(String())

    def __repr__(self):
        return f"Domain MD(id={self.id!r}, key={self.key!r}, value={self.value!r})"

class URIs(Base):
    __table_args__ = {'extend_existing': True}
    __tablename__ = "uris"
    id = Column(Integer, primary_key=True)
    uriid_parent = Column(Integer, foreign_key="uris.id", default=0)

    uri = Column(String())

    uri_type = Column(String(15))
    domainid = Column(Integer, ForeignKey("domains.id"))
    root = Column(Boolean, default = False)
    added = Column(DateTime, default = func.now())
    deleted = Column(DateTime)

    # joins
    #processors = relationship("Processors", secondary= "processoruris") # back_populates = "uri")
    umd = relationship("URIMD")
    versions = relationship("Versions")

    # contstaints
    UniqueConstraint("uriid_parent", "uri", name='uri_unique')

    def __repr__(self):
        return f"URI(id={self.id!r}, name={self.uri!r})"

class URIMD(Base):
    __table_args__ = {'extend_existing': True}
    __tablename__ = "urimd"
    uriid = Column(Integer, ForeignKey("uris.id"), primary_key = True)
    key = Column(String(255), primary_key = True)
    added = Column(DateTime, default = func.now())
    modified = Column(DateTime)
    deleted = Column(DateTime)
    value = Column(String())

    def __repr__(self):
        return f"URI MD(uriid={self.uriid!r}, key={self.key!r}, value={self.value!r})"

class ProcessorURIs(Base):
    __table_args__ = {'extend_existing': True}
    __tablename__ = "processoruris"
    #id = Column(Integer, primary_key=True)
    processorid = Column(Integer, ForeignKey("processors.id"), primary_key = True)
    uriid = Column(Integer, ForeignKey("uris.id"), primary_key = True)
    added = Column(DateTime, default = func.now())
    deleted = Column(DateTime)

    # joins
    uri = relationship("URIs", backref = backref("processors_assoc"))
    processor = relationship("Processors", backref = backref("uris_assoc"))

class Versions(Base):
    __table_args__ = {'extend_existing': True}
    __tablename__ = "versions"
    id = Column(Integer, primary_key=True)
    uriid = Column(Integer, ForeignKey("uris.id"))
    added = Column(DateTime, default = func.now())
    modified = Column(DateTime)
    size = Column(Integer)
    checksum = Column(String(255))

    # join
    vmd = relationship("VersionMD")

    def __repr__(self):
        return f"URI(versionid={self.id!r}, uriid={self.uriid!r}, size={self.size}, modified={self.modified})"

class VersionMD(Base):
    __table_args__ = {'extend_existing': True}
    __tablename__ = "versionmd"
    id = Column(Integer, primary_key=True)
    versionid = Column(Integer, ForeignKey("versions.id"))
    added = Column(DateTime, default = func.now())
    modified = Column(DateTime)
    deleted = Column(DateTime)
    key = Column(String(255))
    value = Column(String())

    def __repr__(self):
        return f"Version MD(uriid={self.versionid!r}, key={self.key!r}, value={self.value!r})"
