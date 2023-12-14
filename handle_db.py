import uuid
from datetime import datetime
from sqlalchemy import ForeignKey, String, Integer, UUID, create_engine, DateTime, CheckConstraint
from sqlalchemy.orm import sessionmaker, mapped_column, relationship, DeclarativeBase
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class User(Base):
    """
    This class inherits from the Base class, the class represents a user table in the database, it first declares
    its name, then declares the column names and their datatypes, and finally a relationship with the uploads table,
    a one-to-many relationship, meaning a single user could have multiple uploads, with the help of back_populates
    parameter it helps to establish a bidirectional relationship.
    the attributes the table holds:
    -id: the id of a user, which is set to primary key.
    -email: the user's email.
    """
    __tablename__ = "users_table"

    id = mapped_column(Integer, primary_key=True, unique=True)
    email = mapped_column(String(30), unique=True, default="anonymous", nullable=False)
    uploads = relationship('Upload', cascade="all, delete-orphan")


class Upload(Base):
    """
    This class also inherits from the Base class and also represents another table in the database, this table holds
    7 attributes, and established another bidirectional relationship with the user table, Multiple upload could belong
    to a single user. The attribute that this table holds:
    -id: generated id of the upload, which is set to a primary key.
    -uid: generated universal unique ID of the upload.
    -file_name: the name of the file uploaded.
    -upload_time: the time the file was uploaded.
    -finish_time: the time the file finished uploading.
    -status: the current status the file is holding.
    -user_id: the id of the user, which is set as a foreign key.
    """
    __tablename__ = "uploads_table"

    id = mapped_column(Integer, primary_key=True, unique=True)
    uid = mapped_column(String, nullable=False, unique=True)
    file_name = mapped_column(String, default="Default_file")
    upload_time = mapped_column(DateTime, nullable=False)
    finish_time = mapped_column(DateTime)
    status = mapped_column(String, nullable=False)
    user_id = mapped_column(Integer, ForeignKey('users_table.id'), default="N/A", nullable=False)
    user = relationship('User', back_populates="uploads")

    def __init__(self, file_name, status, uid, user_id=None):
        """
        Custom Constructor for the database that only receives desired objects.
        :param: file_name: the name of the uploaded file (String)
        :param: status: the current status of a file (String)
        :param: uid: the uid of the file (String)
        :param: user_id: optional variable of the user id, if the user does not exist then its none.
        """
        self.file_name = file_name
        self.status = status
        self.upload_time = datetime.now()
        self.uid = uid
        self.user_id = user_id

    def set_upload_finish_time(self):
        """
        This method sets the time when a file finished uploading
        :return:
        """
        self.finish_time = datetime.now()

    def set_file_status(self, status):
        """
        This method receives a status of a file and updates it in the database
        :param status: status of a file to be updated (String)
        :return:
        """
        self.status = status

    def get_upload_path(self):
        """
        This method returns the path of a certain file in the 'uploads' folder, according to its uid.
        :return: file path (String)
        """
        return f"uploads/{self.uid}.pptx"


engine = create_engine("sqlite:///db/my_database.db", echo=True)
Session = sessionmaker(bind=engine)
session = Session()

Base.metadata.create_all(engine)


