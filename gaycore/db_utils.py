# -*- coding: utf-8 -*-

import time
import traceback
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, TEXT, DATE, SmallInteger
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, mapper
from gaycore.spider import *
from gaycore.utils import *

Base = declarative_base()
engine = create_engine("mysql+pymysql://root@127.0.0.1:3306/gcore?charset=utf8mb4")
Session = sessionmaker(engine)
session = Session()


class Audio(Base):

    __tablename__ = "gcore_audio"

    id = Column(Integer, primary_key=True)
    audio_id = Column("audio_id", Integer, unique=True, nullable=False)
    audio_name = Column("audio_name", String(1000), nullable=False)
    audio_date = Column("audio_date", DATE, nullable=False)
    audio_url = Column("audio_url", String(200), nullable=False)
    audio_mp3_url = Column("audio_mp3_url", String(1000), nullable=False)
    audio_flow_info = Column("audio_flow_info", LONGTEXT, nullable=False, default="[]")
    audio_djs = Column("audio_djs", String(200), nullable=False, default="[]")
    audio_like = Column("audio_like", SmallInteger, nullable=False, default=0)
    audio_comment = Column("audio_comment", SmallInteger, nullable=False, default=0)
    audio_cate = Column("audio_cate", String(200), nullable=False)
    audio_cate_name = Column("audio_cate_name", String(200), nullable=False)


Base.metadata.create_all(engine)


name_list = ["audio_id",
             "audio_name",
             "audio_date",
             "audio_url",
             "audio_mp3_url",
             "audio_flow_info",
             "audio_djs",
             "audio_like",
             "audio_comment",
             "audio_cate",
             "audio_cate_name",
             ]


def paser_value(value):
    audio_id = value[3].split("/")[-1]
    audio_name = value[0]
    audio_date = value[1][0]
    audio_url = value[3]
    audio_mp3_url = value[4]
    audio_flow_info = value[6]
    audio_djs = value[5]
    audio_like = value[2][0]
    audio_comment = value[2][1]
    audio_cate = value[1][1]
    audio_cate_name = value[1][2]
    return [audio_id, audio_name, audio_date, audio_url, audio_mp3_url, audio_flow_info,
            audio_djs, audio_like, audio_comment, audio_cate, audio_cate_name]


def get_page_data(page):
    url = BASE_AUDIO_CATE_URL + "?page={}".format(page)
    cate_result = get_one_cate_info(url)
    insert_data = [dict(zip(name_list, paser_value(i))) for i in cate_result]
    data_list = [Audio(**i) for i in insert_data]
    return data_list


def insert_one_page(page):
    data_list = get_page_data(page)
    session.add_all(data_list)
    try:
        session.commit()
        # session.merge()
    except:
        traceback.print_exc()
        session.rollback()
        time.sleep(1)


def insert_all_page(start, end):
    for i in range(start, end):
        try:
            insert_one_page(i)
            print(i)
        except Exception as e:
            time.sleep(2)
            try:
                insert_one_page(i)
            except:
                traceback.print_exc()
                print("{} is wrong".format(i))


def daily_spider(page=0):
    old_id_list = session.query(Audio.audio_id).order_by(Audio.audio_id.desc()).limit(30)
    old_id_list = [str(i.audio_id) for i in old_id_list]
    data_list = get_page_data(page)
    spider_id_list = [(i.audio_id, i.audio_like, i.audio_comment) for i in data_list]
    spider_old_id_list = [i for i in spider_id_list if i[0] in old_id_list]
    spider_new_id_list = list(set([i[0] for i in spider_id_list]) - set([i[0] for i in spider_old_id_list]))

    # new audios to insert
    insert_values = [i for i in data_list if i.audio_id in spider_new_id_list]
    session.add_all(insert_values)
    session.commit()

    # old audios to update
    for i in spider_old_id_list:
        session.query(Audio).filter(Audio.audio_id==i[0]).update({"audio_like": i[1], "audio_comment": i[2]})
        session.commit()
