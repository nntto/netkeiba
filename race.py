from __future__ import annotations
import time
from typing import Dict, List
from xml.etree.ElementTree import tostring
import requests
import json
import lxml.html
import re
import logging
import sys
import traceback
from datetime import datetime, timezone, timedelta


logger = logging.getLogger("logger")    #logger名loggerを取得
logger.setLevel(logging.INFO)

#handler1を作成
handler1 = logging.StreamHandler()
handler1.setFormatter(logging.Formatter("%(asctime)s %(levelname)8s %(message)s"))

#handler2を作成
handler2 = logging.FileHandler(filename=f"log/{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.log")  #handler2はファイル出力
handler2.setLevel(logging.WARN)     #handler2はLevel.WARN以上
handler2.setFormatter(logging.Formatter("%(asctime)s %(levelname)8s\n%(message)s"))

#loggerに2つのハンドラを設定
logger.addHandler(handler1)
logger.addHandler(handler2)


HEAD_URL = 'https://db.sp.netkeiba.com'

class Race:
    race_id: str # レースID
    location: str # 場所
    round: str # 1R, 2R, ..., 12R
    race_name: str
    grade: str # G1, G2, ...
    date: str
    start_time: str
    course: str
    weather: str
    baba: str
    race_class: str
    race_rule: str
    horses: List[Horse]
    payback: Payback
    order_of_bend: List[Dict[str,str]]
    rap_time: RapTime

    def __init__(self):
        pass

    def import_from_url(self, url) -> Race:
        netkeiba = lxml.html.fromstring(requests.get(url).content)
        self.race_id = url.replace('https://db.sp.netkeiba.com/race/','').replace('/','')
        self.location = netkeiba.xpath('//*[@class="RaceHeader_Select"]/div[1]/select/option[@selected="selected"]')[0].text
        self.round = netkeiba.xpath('//*[@class="RaceHeader_Select"]/div[2]/select/option[@selected="selected"]')[0].text
        self.race_name = netkeiba.xpath('//*[@class="RaceName_main"]')[0].text
        self.grade = netkeiba.xpath('//*[@class="RaceName"]/span')[1].text if len(netkeiba.xpath('//*[@class="RaceName"]/span')) == 2 else ''
        self.date = netkeiba.xpath('//*[@class="Race_Date"]')[0].text_content().replace('\n','')
        self.start_time = netkeiba.xpath('//*[@class="RaceData"]/span[1]')[0].text
        self.course = netkeiba.xpath('//*[@class="RaceData"]/span[2]')[0].text
        self.weather = netkeiba.xpath('//*[@class="RaceData"]/span[3]')[0].text if len(netkeiba.xpath('//*[@class="RaceData"]/span[3]')) == 1 else ''
        self.baba = netkeiba.xpath('//*[@class="RaceData"]/span[4]')[0].text if len(netkeiba.xpath('//*[@class="RaceData"]/span[4]')) == 1 else ''
        self.race_class = netkeiba.xpath('//*[@class="RaceHeader_Value_Others"]/span[1]')[0].text
        self.race_rule = netkeiba.xpath('//*[@class="RaceHeader_Value_Others"]/span[2]')[0].text
        
        self.horses = []
        for horse_dom in netkeiba.xpath('//*[@class="table_slide_body ResultsByRaceDetail"]/tbody/tr'):
            self.horses.append(Horse().import_from_dom(horse_dom))
        
        self.payback = Payback().import_from_dom(netkeiba.xpath('//*[@class="Result_Pay_Back"]')[0])
        
        self.order_of_bend = []
        for bend_dom in netkeiba.xpath('//*[@class="result_corner"]/table/tbody/tr')[2:]:
            bend_info = {}
            bend_info['bend'] = bend_dom.xpath('th')[0].text
            bend_info['order'] = bend_dom.xpath('td')[0].text_content()
            self.order_of_bend.append(bend_info)
        
        rap_time_dom = netkeiba.xpath('//*[@class="Race_Raptime"]')
        self.rap_time = RapTime().import_from_dom(rap_time_dom[0]) if len(rap_time_dom) == 1 else {}

        return self
    
    def __str__(self):
        return_value = ''
        for key, value in self.__dict__.items():
            return_value += f"{json.dumps(key)} : {json.dumps(value, ensure_ascii=False)}\n"
        return return_value

    def __repr__(self):
        return_value = '{'
        for key, value in self.__dict__.items():
            try:
                return_value += f"{json.dumps(key)} : {json.dumps(value, ensure_ascii=False)},"
            except:
                return_value += f"{json.dumps(key)} : {value.__repr__()},"

        return return_value[:-1] + '}'

class Horse:
    rank: str # 着順
    bracket_number: str # 枠番
    horse_number: str # 馬番
    horse: Dict[str,str] # 馬名 #{'id': hoge, 'name': fuga}
    gender: str # 性
    age: str # 齢
    weight_to_carry: str # 斤量
    jockey: Dict[str,str] # 騎手 #{'id': hoge, 'name': fuga}
    time: str # タイム
    margin: str # 着差
    time_index: str # タイム指数
    passing: str # 通過
    agari: str # 上がり
    win_odds: str # 単勝
    ninki: str # 人気
    horse_weight: str # 馬体重
    note: str # 備考
    trainer: Dict[str,str] # 調教師 #{'id': hoge, 'name': fuga}
    owner: Dict[str,str] # 馬主 #{'id': hoge, 'name': fuga}
    prize: str

    def import_from_dom(self, dom) -> Horse:
        self.rank = dom.xpath('td[1]')[0].text
        self.bracket_number = dom.xpath('td[2]')[0].text
        self.horse_number = dom.xpath('td[3]')[0].text
        self.horse = {}
        try:
            self.horse['id'] = dom.xpath('td[4]/a')[0].attrib['href'].replace('https://db.sp.netkeiba.com/horse/','').replace('/','')
            self.horse['name'] = dom.xpath('td[4]/a')[0].text
        except IndexError:
            pass
        self.gender = dom.xpath('td[5]')[0].text[0]
        self.age = dom.xpath('td[5]')[0].text[1:]
        self.weight_to_carry = dom.xpath('td[6]')[0].text
        self.jockey = {}
        try:
            self.jockey['id'] = dom.xpath('td[7]/a')[0].attrib['href'].replace('https://db.sp.netkeiba.com/jockey/','').replace('/','')
            self.jockey['name'] = dom.xpath('td[7]/a')[0].text
        except IndexError:
            pass
        self.time = dom.xpath('td[8]')[0].text
        self.margin = dom.xpath('td[9]')[0].text
        self.time_index = dom.xpath('td[10]')[0].text.replace('\n','')
        self.passing = dom.xpath('td[11]')[0].text
        self.agari = dom.xpath('td[12]')[0].text
        self.win_odds = dom.xpath('td[13]')[0].text
        self.ninki = dom.xpath('td[14]')[0].text
        self.horse_weight = dom.xpath('td[15]')[0].text
        self.note = dom.xpath('td[18]')[0].text.replace('\n','')
        self.trainer = {}
        try:
            self.trainer['id'] = dom.xpath('td[19]/a')[0].attrib['href'].replace('https://db.sp.netkeiba.com/trainer/','').replace('/','')
            self.trainer['name'] = dom.xpath('td[19]/a')[0].text
        except IndexError:
            pass
        self.owner = {}
        try:
            self.owner['id'] = dom.xpath('td[20]/a')[0].attrib['href'].replace('https://db.sp.netkeiba.com/owner/','').replace('/','')
            self.owner['name'] = dom.xpath('td[20]/a')[0].text
        except IndexError:
            pass
        self.prize = dom.xpath('td[21]')[0].text or ''

        return self

    def __str__(self):
        return_value = "{\n"
        for key, value in vars(self).items():
            return_value += f"\t{key} : {value}\n"
        return return_value + "}\n"

    def __repr__(self):
        return_value = "{"
        for key, value in self.__dict__.items():
            return_value += f'"{key}":{json.dumps(value, ensure_ascii=False)},'
        return_value = return_value[:-1]
        return return_value + "}"
    
class Payback:
    # {'result': str, 'payout': str, 'ninki': str}
    PaybackElement = List[Dict[str, str]]
    tansho: PaybackElement # 単勝
    fukusho: PaybackElement # 複勝
    wakuren: PaybackElement # 枠連
    umaren: PaybackElement # 馬連
    wide: PaybackElement # ワイド
    umatan: PaybackElement # 馬単
    fuku3: PaybackElement # 3連複
    tan3: PaybackElement # 3連単

    def import_from_dom(self, dom) -> Payback:
        self.tansho = self.__dict_from_dom(dom.xpath('table/tbody[@class="Tansho"]/tr'))
        self.fukusho = self.__dict_from_dom(dom.xpath('table/tbody[@class="Fukusho"]/tr'))
        self.wakuren = self.__dict_from_dom(dom.xpath('table/tbody[@class="Wakuren"]/tr'))
        self.umaren = self.__dict_from_dom(dom.xpath('table/tbody[@class="Umaren"]/tr'))
        self.wide = self.__dict_from_dom(dom.xpath('table/tbody[@class="Wide"]/tr'))
        self.umatan = self.__dict_from_dom(dom.xpath('table/tbody[@class="Umatan"]/tr'))
        self.fuku3 = self.__dict_from_dom(dom.xpath('table/tbody[@class="Fuku3"]/tr'))
        self.tan3 = self.__dict_from_dom(dom.xpath('table/tbody[@class="Tan3"]/tr'))

        return self
    
    def __dict_from_dom(self, dom) -> List[Dict[str,str]]:
        list = []
        for tr in dom:
            ele = {}
            ele['result'] = tr.xpath('td[@class="Result"]')[0].text
            ele['payout'] = tr.xpath('td[@class="Payout"]')[0].text
            ele['ninki'] = tr.xpath('td[@class="Ninki"]')[0].text
            list.append(ele)
        return list

    def __str__(self):
        return_value = "{\n"
        for key, value in vars(self).items():
            return_value += f"\t{key} : {value}\n"
        return return_value + "}\n"

    def __repr__(self):
        return_value = "{"
        for key, value in self.__dict__.items():
            return_value += f'"{key}":{json.dumps(value, ensure_ascii=False)},'
        return return_value[:-1] + "}"


class RapTime:
    race_pace: str
    rap_pace: str
    result: List[Dict[str,str]]
    # [{'distance': , 'pass_time':, 'rap_time':},...]

    def import_from_dom(self, dom) -> RapTime:
        self.race_pace = dom.xpath('//span[@class="RapPace"]/span')[0].text
        self.rap_pace = dom.xpath('//div[@class="rap_pace"]')[0].text
        self.result = []
        for th, td in zip(dom.xpath('//tr[@class="Header"]/th'), dom.xpath('//tr[@class="HaronTime"]/td')):
            if th.text == None:
                continue
            info = {}
            info['distance'] = th.text
            info['pass_time'] = re.findall(r'\d?:?\d+\.\d+', tostring(td).decode())[0]
            info['rap_time'] = re.findall(r'\d?:?\d+\.\d+', tostring(td).decode())[1]
            self.result.append(info)
        return self

    def __str__(self):
        return_value = "{\n"
        for key, value in vars(self).items():
            return_value += f"\t{key} : {value}\n"
        return return_value + "}\n"

    def __repr__(self):
        return_value = "{"
        for key, value in self.__dict__.items():
            return_value += f'"{key}":{json.dumps(value, ensure_ascii=False)},'
        return return_value[:-1] + "}"

def parse_race_list(year: int):
    search_url = f"https://db.sp.netkeiba.com/?pid=race_list&word=&start_year={year}&start_mon=none&end_year={year}&end_mon=none&kyori_min=&kyori_max=&sort=date&submit=&page=1"

    while 1:
        search_result = lxml.html.fromstring(requests.get(search_url).content)
        for i in search_result.xpath('//*[@class="CommonList_01"]/li/div'):
            race_url = i.xpath('a')[-1].attrib['href']
            if len(re.findall('\d{4}/\d{1,2}/\d{1,2}', race_url)) == 1:
                logger.info(f"wrong url: {race_url}")
                continue
            yield race_url
        
        next_li = search_result.xpath('//*[@class="Icon_SNS_S"]')[0].xpath('li')[-1]
        if len(next_li.xpath('a')) == 1:
            search_url = HEAD_URL + next_li.xpath('a')[0].attrib['href']
        else:
            break
        time.sleep(1)


if __name__=="__main__":
    # race = Race().import_from_url('https://db.sp.netkeiba.com/race/202245020211/')
    # json = json.loads(race.__repr__())
    # print(json)
    for year in range(2018, 2023):
        with open(f'./race/{year}.json', 'w') as f:
            f.write('[\n')
            for i, race_url in enumerate(parse_race_list(year)):
                try:
                    race = Race().import_from_url(race_url)
                    f.write((',' if i != 0 else '') + race.__repr__() + '\n')
                    logger.info(f"{i} success: {race.race_name}")
                except:
                    logger.warning(f"{i} failure: {race_url}")
                    logger.warning(traceback.format_exc())
                time.sleep(1)
            f.write(']\n')