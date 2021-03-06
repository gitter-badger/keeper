# -*- coding:utf-8 -*-
import os
import re
import datetime
import os.path
import timespans
import platform

WINDOWS = platform.system() == 'Windows'
from settings import *

def get_dir():
    return os.path.dirname(__file__)+"/lists/"

def get_length(s):
    if '?' in s:
        return None
    elif s.endswith('h') or s.endswith('ч'):
        return float(re.findall('\d*\.?\d+', s)[0])
    elif s.endswith('m') or s.endswith('м'):
        return float(re.findall('\d*\.?\d+', s)[0]) / 60

def looks_like_date(s):
    return [] != re.findall('^\d\d?\.\d\d?\.\d\d\d\d', s)

def looks_like_datetime(s):
    return [] != re.findall('^\d\d?\.\d\d?\.\d\d\d\d\s+\d\d?:\d\d?', s)

def looks_like_time(s):
    return [] != re.findall('^\d\d?:\d\d?', s)

def looks_like_till_datetime(s):
    return [] != re.findall('^<\d\d?\.\d\d?\.\d\d\d\d\s+\d\d?:\d\d?', s)


def looks_like_till_date(s):
    return [] != re.findall('^<\d\d?\.\d\d?\.\d\d\d\d', s)

def looks_like_length(s):
    return [] != re.findall('\d+[hmчм]|\?[hmчм]', s)

def looks_like_periodic(s):
    return s.startswith("+")

def looks_like_page_count(s):
    return [] != re.findall('\d+p', s)

def is_number(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

def days(datefrom, dateto):
    datenow = datefrom
    while datenow < dateto:
        yield datenow
        datenow += datetime.timedelta(days = 1)


class Period(object):
    def __init__(self, specification = None, task = None):

        self.specification = specification[1:]
        parts = self.specification.strip().split()
        self.start_time = None
        self.specs = []
        for part in parts:
            if looks_like_time(part):
                self.start_time = datetime.datetime.strptime(part, '%H:%M').time()
            else:
                self.specs.append(part)

        #print self.specs
        #print self.start_time
        self.task = task

    def set_task(self, task):
        self.task = task

    def has_day(self, day):
        """
        :type day:datetime.date
        :param day:
        :return:
        """
        result = not self.specs or \
            "понедельник" in self.specs and day.weekday() == 0 or \
            "вторник" in self.specs and day.weekday() == 1 or \
            "среда" in self.specs and day.weekday() == 2 or \
            "четверг" in self.specs and day.weekday() == 3 or \
            "пятница" in self.specs and day.weekday() == 4 or \
            "суббота" in self.specs and day.weekday() == 5 or \
            "воскресенье" in self.specs and day.weekday() == 6
        #print day, result
        return result

    def get_timespan_for_day(self, day):
        _from = datetime.datetime.combine(day, self.start_time)
        return timespans.TimeSpan(_from = _from,
                                  _to = _from + datetime.timedelta(hours = self.task.length))

class Task:
    def __init__(self, name = "", length = 1, topic = None, topics = [], at = None, till = None, periodics = None, cost = None):
        self.name = name
        self.length = length
        self.topic = topic
        self.cost = cost
        self.periodics = periodics
        if self.periodics:
            for period in self.periodics:
                period.set_task(self)

        self.topics = topics
        if topic and not topics:
            self.topics.append(topic)
            
        self.at = at
        self.till = till
        self.upper_limit = None
        if self.at is not None:
            self.upper_limit = self.at
        elif self.till is not None:
            self.upper_limit = self.till
        
    def planned_time_to_str(self):
        if self.length is None:
            return 'unknown'
        else:
            return str(self.length) + 'h'


    def generate_timespanset(self, start, end):
        if not self.periodics:
            return timespans.TimeSpanSet(self.at, self.upper_limit)
        spans = []
        for period in self.periodics:
            for day in days(start.date() - datetime.timedelta(days=1), end.date()+datetime.timedelta(days=1)):
                if period.has_day(day):
                    spans.append(period.get_timespan_for_day(day))
        spanset = (timespans.TimeSpanSet(timespans = spans).converge()
                  - timespans.TimeSpanSet(_from=None, _to=start)) \
                  - timespans.TimeSpanSet(_from=end, _to=None)
        return spanset.converge()

    def __str__(self):        
        return self.__unicode__()

    def __unicode__(self):
        #print self.topic
        #print self.name
        #print self.planned_time_to_str()

        if not WINDOWS:
            return "{} {} [{}]".format(self.topic, self.name, self.planned_time_to_str())
        else:
            topic = self.topic
            if not topic:
                topic = "None"
            return "{} {} [{}]".format(topic.encode("cp866"), self.name.encode('cp866'), self.planned_time_to_str().encode('cp866'))
        
    

        
class TaskList:
    def __init__(self, filename = None):
        self.tasks = []
        self.special_tasks = []
        if filename:
            self.load_from_file(filename)
        
    def load_from_file(self, filename):
        current_section = None
        section_attributes = dict()
        in_comment = False
        for line in open(filename).readlines():        
            line = line.rstrip()            
            if WINDOWS:                
                line = line.decode('windows-1251')
                
            if line:
                if in_comment and "*/" in line:
                  in_comment = False
                  continue
                if in_comment:
                    continue
                if line.strip().startswith('//') or line.strip().startswith('#'):
                    pass
                elif line.strip().startswith("/*"):
                    in_comment = True
                elif line.endswith(':'):
                    current_section = line.strip()[:-1]
                    section_attributes = self.extract_attributes(current_section)
                    current_section = re.sub('\[.*\]', '', current_section)
                    current_section = re.sub('[ ]+', ' ', current_section.strip())
                    #print section_attributes
                else:
                    attributes = dict()
                    if not line.startswith(' ') and not line.startswith('\t'):
                        current_section = None
                        section_attributes = dict()
                    attributes.update(section_attributes)
                    attributes.update(self.extract_attributes(line))
                    attributes['topic'] = current_section
                    attributes['topics'] += [os.path.basename(filename).split('.')[0]]
                    if 'topics' in section_attributes:
                        attributes['topics'] += section_attributes['topics']
                    if current_section:
                        attributes['topics'].append(current_section)
                    task = Task(**attributes)
                    if not set(attributes['topics']).intersection(set(IGNORED_SECTIONS)):
                        self.tasks.append(task)
                    else:
                        self.special_tasks.append(task)

    @staticmethod
    def extract_attributes(line):
        try:
            result = dict()
            result['name'] = line.strip()
            result['topics'] = []
            times = re.findall('\d+[hm]|\?[hm]', line)
            if times:
                time = times[0]
                result['length'] = get_length(time)
            attribute_line = re.findall('\[(.*?)\]', line)

            if attribute_line:
                attributes = [attr.strip() for attr_set in attribute_line for attr in attr_set.split(',')]
                periodics = []

                for attr in attributes:
                    if looks_like_datetime(attr):
                        result['at'] = datetime.datetime.strptime(attr, '%d.%m.%Y %H:%M')
                    elif looks_like_date(attr):
                        result['at'] = datetime.datetime.strptime(attr, '%d.%m.%Y')
                    elif looks_like_length(attr):
                        result['length'] = get_length(attr)              
                    elif looks_like_till_datetime(attr):
                        result['till'] = datetime.datetime.strptime(attr[1:], '%d.%m.%Y %H:%M')
                    elif looks_like_till_date(attr):
                        result['till'] = datetime.datetime.strptime(attr[1:], '%d.%m.%Y')
                    elif looks_like_periodic(attr):
                        periodics.append(Period(attr))
                    elif attr.startswith('$') or attr.startswith("р"):
                        #print attr, attr[1:], is_number(attr[1:])
                        result['cost'] = float(attr[2:])
                        result['topics'].append('money')
                    elif looks_like_page_count(attr):
                        page_count = int(attr[:-1])
                        result['topics'].append("books")
                        if "hard" in attributes:
                            result['length'] = page_count * HARD_PAGE_TIME
                        else:
                            result['length'] = page_count * SIMPLE_PAGE_TIME
                    else:
                        result['topics'].append(attr)        
                result['periodics'] = periodics
            return result                        
        except Exception as e:
            raise Exception("error while parsing {}: ".format(line) + e.message)

    def today(self):
        return [task for task in self.tasks if task.upper_limit is not None and task.upper_limit.date()<=datetime.date.today()]
        
    def strict_at(self, date):
        return [task for task in self.tasks if task.at == date]
    
    def till(self, date):
        return [task for task in self.tasks if task.till != None and task.till<=date] + self.strict_at(date)

    def is_sleeping_time(self, time):
        start_sleep = datetime.datetime.combine(time.date(), datetime.time(hour=23))
        end_sleep = datetime.datetime.combine(time.date(), datetime.time(hour=7))
        return time < end_sleep or time > start_sleep


    def special_time(self, time_from, time_to):
        """
        result = datetime.timedelta()
        while time_from < time_to:
            if self.is_sleeping_time(time_from):
                result += datetime.timedelta(hours=1)
            time_from += datetime.timedelta(hours=1)
        return result
        """
        span = timespans.TimeSpanSet(timespans = [])

        for t in self.tasks:
            if t.periodics:
                span += t.generate_timespanset(time_from, time_to)
        return span.length()

    def check(self, date_from = None):
        if date_from is None:
            date_from =  datetime.datetime.now()

        limited_tasks = [task for task in self.tasks if task.upper_limit is not None and not task.periodics]
        unbound_tasks = [task for task in self.tasks if task.upper_limit is None and task.length is not None and not task.periodics]
        limited_tasks.sort(key = lambda task : task.upper_limit)

        budget = datetime.timedelta()
        now = date_from
        for task in limited_tasks:
            status = "nominal"
            if task.upper_limit<date_from:
                status = "OVERDUE"
            else:
                budget += task.upper_limit - now
                budget -= self.special_time(now, task.upper_limit)
                budget -= datetime.timedelta(hours=task.length)
                if budget < datetime.timedelta():
                    status = "FUCKUP"
                now = task.upper_limit
            if status != 'nominal': print status, task
        assigned_time = sum([datetime.timedelta(hours = task.length) for task in limited_tasks], datetime.timedelta())
        print assigned_time, " time scheduled"
        print budget, " unscheduled worktime left"
        unbound_time = sum([datetime.timedelta(hours = task.length) for task in unbound_tasks], datetime.timedelta())
        print "All other tasks are", unbound_time
        left = (budget - unbound_time).total_seconds()/60.0/60
        print abs(left), "h of unassigned time" if left > 0 else "h shortage"

        if unbound_time > budget:
            print "You're short of time. Either limit some unbound tasks, or postpone some of limited"
        else:
            print "NOMINAL"

    def scheduled(self, date_from = None):
        if date_from is None:
            date_from =  datetime.datetime.now()
        limited_tasks = [task for task in self.tasks if task.upper_limit is not None]
        limited_tasks.sort(key = lambda task : task.upper_limit)
        for task in limited_tasks:
            print task
            
def load_all():
    taskpool = TaskList()
    lists_dir = get_dir()
    for filename in os.listdir(lists_dir):
        taskpool.load_from_file(lists_dir+filename)
    return taskpool

if __name__== "__main__":
     print TaskList().special_time(datetime.datetime.now(), datetime.datetime.now() + datetime.timedelta(days = 1)).seconds/3600
     
     print looks_like_length('100ч')
     print "100ч"[:-1]
     print get_length('100ч')
