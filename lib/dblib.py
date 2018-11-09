#!/usr/bin/python
"""
- Purpose:
    A Library to Handle DB Transactions, mapped as Table -> Class ->  Object by SQLAlchemy

- Author:
    Rudolf Wolter (KN OSY Team)

- Contact for questions and/or comments:
    rudolf.wolter@kuehne-nagel.com

- Version Releases and modifications.
    > 1.0 (18.10.2018) - Initial release with core functions.

- TODO:

"""
### START OF MODULE IMPORTS
# --------------------------------------------------------------- #
from collections import OrderedDict
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Time
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import text
# --------------------------------------------------------------- #
### END OF MODULE IMPORTS
## DB Section
DBURI = "mysql://cruser:q1w2e3r4@denotsl90.int.kn/crdb"
# DBURI = "mysql://cruser:q1w2e3r4@localhost/crdb"
DBENGINE = create_engine(DBURI)
DBASE = declarative_base()
DBSession = sessionmaker(bind=DBENGINE)()

### START OF FUNCTIONS DECLARATION
# --------------------------------------------------------------- #
# --------------------------------------------------------------- #
def mk_dbbenv():
    DBASE.metadata.create_all(DBENGINE)
# --------------------------------------------------------------- #

# --------------------------------------------------------------- #
def select_all_from(_class):
    """
    Purpose:
        Retrieves all entries from Database for a given Class/Table and stores it in a Dictionary

    Parameters:
    """
    result_dict = OrderedDict()
    # Feeding the dictionary with the already existing servers records.
    for entry in eval('DBSession.query({}).order_by({}.name)'.format(_class, _class)):
        result_dict[entry.name] = entry

    return result_dict
# --------------------------------------------------------------- #

def destroy_table(_class):
    """
    Purpose:
        ** CAUTION ** This WILL destroy the Representative's Table and all its contents!
    Parameters:
    """
    global DBSession
    DBSession.execute(text('SET FOREIGN_KEY_CHECKS = 0;'))
    DBSession.close()
    _class.__table__.drop(DBENGINE)
    DBSession = sessionmaker(bind=DBENGINE)()
    DBSession.execute(text('SET FOREIGN_KEY_CHECKS = 1;'))
# --------------------------------------------------------------- #

# --------------------------------------------------------------- #
### END OF FUNCTIONS DECLARATION

# --------------------------------------------------------------- #
class Vmstat(DBASE):
    """
    Purpose:
        Represents an AIX Server
    """
    __tablename__ = 'vmstat'
    # Here we define columns for the table servers
    # Notice that each column is also a normal Python instance attribute.
    id = Column(String(64), primary_key=True)
    servername = Column(String(20), nullable=False)
    date = Column(DateTime, nullable=False)
    peak_avg_busy = Column(Float)
    peak_avg_warning = Column(Float)
    peak_avg_critical = Column(Float)
    peak_samples_count = Column(Integer)
    peak_warn_count = Column(Integer)
    peak_crit_count = Column(Integer)
    peakstart = Column(Time, nullable=False)
    peakstop = Column(Time, nullable=False)
    average_busy = Column(Float)
    average_warning = Column(Float)
    average_critical = Column(Float)
    samples_count = Column(Integer)
    warn_count = Column(Integer)
    crit_count = Column(Integer)
    runqueue = Column(Integer)
    avm = Column(Integer)
    freemem = Column(Integer)

    def self_destruct(self):
        """
        Purpose:
            ** CAUTION ** This WILL destroy the Representative's Table and all its contents!
        Parameters:
        """
        raw_input('Are you sure? Press any key to continue or "ctrl-c" to abort')
        self.__table__.drop(DBENGINE)

    def self_create(self):
        """
        Purpose:
            Creates the Representative's Table
        Parameters:
        """
        self.__table__.create(DBENGINE)

    def get_objvalue(self, column):
        """
        Purpose:
            Retrieves the current value of this instance's column's value. But not from the DB
        Parameters:
            column: The Columns's value to be retrieved.
        """
        return getattr(self, column)

    def get_columns_from_db(self):
        """
        Purpose:
            Retrieves the values of a columns direct from the DB
        Parameters:
        """
        return self.__table__.columns.keys()

    def query_by(self, attr_name, attr_value):
        """
        Purpose:
            Queries the Database for all entries that match single Attribute and returns a list of results
        """
        query = eval('DBSession.query({}).filter({}.{} == "{}")'
                     .format(type(self).__name__, type(self).__name__, attr_name, attr_value))
        return query.all()

    def update(self):
        """
        Purpose:
            Updates and commits the database with the current Object Instance's Values
        """
        DBSession.add(self)
        DBSession.commit()

    def query(self, custom_query):
        query = eval('DBSession.query({}).filter({})').format(type(self).__name__, custom_query)
        return query.all()

    def query_all(self):
        """
        Purpose:
            Retrieves all entries related to this Class from Database and stores it in an Ordered Dictionary of Objects

        Parameters:
        """
        hostsdict = OrderedDict()
        # Feeding the dictionary with the already exists servers records.
        for entry in DBSession.query(type(self)).order_by(type(self).id):
            hostsdict[entry.id] = entry
        return hostsdict
# --------------------------------------------------------------- #

# --------------------------------------------------------------- #
class Lparstat(DBASE):
    """
    Purpose:
        Represents an AIX Server
    """
    __tablename__ = 'lparstat'
    # Here we define columns for the table servers
    # Notice that each column is also a normal Python instance attribute.
    id = Column(String(64), primary_key=True)
    servername = Column(String(20), nullable=False)
    date = Column(DateTime, nullable=False)
    ent_cap = Column(Float, nullable=False)
    vprocs = Column(Integer, nullable=False)
    cpu_type = Column(String(20), nullable=False)
    cpu_mode = Column(String(20), nullable=False)
    peak_avg_physc = Column(Float)
    peak_average_entc = Column(Float)
    peak_average_idle = Column(Float)
    peak_avg_idle_warning = Column(Float)
    peak_avg_idle_critical = Column(Float)
    peak_samples_count = Column(Integer)
    peakstart = Column(Time, nullable=False)
    peakstop = Column(Time, nullable=False)
    average_physc = Column(Float)
    samples_count = Column(Integer)
    average_entc = Column(Float)
    average_idle = Column(Float)
    avg_idle_warning = Column(Float)
    avg_idle_critical = Column(Float)

    def self_destruct(self):
        """
        Purpose:
            ** CAUTION ** This WILL destroy the Representative's Table and all its contents!
        Parameters:
        """
        self.__table__.drop(DBENGINE)

    def self_create(self):
        """
        Purpose:
            Creates the Representative's Table
        Parameters:
        """
        self.__table__.create(DBENGINE)

    def get_objvalue(self, column):
        """
        Purpose:
            Retrieves the current value of this instance's column's value. But not from the DB
        Parameters:
            column: The Columns's value to be retrieved.
        """
        return getattr(self, column)

    def get_columns_from_db(self):
        """
        Purpose:
            Retrieves the values of a columns direct from the DB
        Parameters:
        """
        return self.__table__.columns.keys()

    def query_by(self, attr_name, attr_value):
        """
        Purpose:
            Queries the Database for all entries that match single Attribute and returns a list of results
        """
        query = eval('DBSession.query({}).filter({}.{} == "{}")'
                     .format(type(self).__name__, type(self).__name__, attr_name, attr_value))
        return query.all()

    def update(self):
        """
        Purpose:
            Updates and commits the database with the current Object Instance's Values
        """
        DBSession.add(self)
        DBSession.commit()

    def query(self, custom_query):
        query = eval('DBSession.query({}).filter({})').format(type(self).__name__, custom_query)
        return query.all()

    def query_all(self):
        """
        Purpose:
            Retrieves all entries related to this Class from Database and stores it in an Ordered Dictionary of Objects

        Parameters:
        """
        hostsdict = OrderedDict()
        # Feeding the dictionary with the already exists servers records.
        for entry in DBSession.query(type(self)).order_by(type(self).id):
            hostsdict[entry.id] = entry
        return hostsdict
# --------------------------------------------------------------- #
