from datetime import datetime
from pymongo import MongoClient
import random
import sys




client = MongoClient()
db = client.lsc.session
db2 = client.lsc.query
SECONDS_PER_CLUE = 60
MAX_POINT = 100
MAX_POINT_TASK_END = 50
PENALTY_PER_WRONG = 10

class Query():
    def __init__(self, idx, text, results):
        self.idx = idx
        existed = db.find_one({"idx": idx})
        if existed:
            self.restore_from_dict(existed)
        else:
            self.id = None
            # ["Default Query 1", "Default Query 2", "Default Query 3"]
            self.text = text
            self.results = results  # ["image1", "image2", "image3"]
            self.current = 0
            self.write_to_db()

    def restore_from_dict(self, dictdata):
        self.text = dictdata["text"]
        self.results = dictdata["results"]
        self.current = dictdata["current"]
        self.idx = dictdata["idx"]
        self.id = dictdata["_id"]

    def to_dict(self):
        return {"text": self.text,
                "results": self.results,
                "current": self.current}

    def get_current_text(self):
        return self.text[self.current]

    def restart(self):
        self.current = 0
        self.write_to_db()

    def next_clue(self):
        self.current += 1
        self.write_to_db()
        if self.current >= len(self.text):
            return False
        return True

    def eval(self, imageid):
        return imageid in self.results

    def write_to_db(self):
        if self.id:
            db2.update_one({'_id': self.id}, {'$set': self.to_dict()})
        else:
            self.id = db2.insert_one(self.to_dict()).inserted_id


def get_all_queries(filename):
    query_id = None
    text = []
    results = []
    queries = []
    with open(filename) as f:
        for line in f.readlines():
            line = line.strip()
            if not line:
                if query_id:
                    queries.append(Query(query_id, text, results))
                query_id = None
                text = []
                results = []
                continue
            if len(line) == 2:
                query_id = int(line)
            else:
                if len(text) < 6:
                    text.append(line.strip())
                else:
                    results.append(line.strip())
    return queries

ALL_QUERIES = get_all_queries('backend/all_queries.txt')

class LSCSession():
    def __init__(self, name):
        self.name = name
        existed = db.find_one({"name": name})
        if existed:
            self.restore_from_dict(existed)
        else:
            self.time = datetime.now()
            self.submissions = [[] for i in range(5)]
            self.id = None
            self.query_ids = random.choices(range(len(ALL_QUERIES)), k=5)
            self.query_id = 0
            self.scores = [0 for i in range(5)]

    def add_submission(self, imageid):
        current_query = self.get_current_query()
        correctness = current_query.eval(imageid)
        self.submissions[self.query_id].append(
            (imageid, correctness, (60 - self.time) + current_query.current * 60))
        self.get_score()
        if correctness:
            self.get_current_query().finish_clue()
        self.write_to_db()
        return correctness

    def set_time(self, time):
        self.time = int(time)
        self.write_to_db()

    def get_score(self):
        submissions = self.submissions[self.query_id]
        duration = SECONDS_PER_CLUE * len(self.get_current_query().text)
        correctness = [sub[1] for sub in submissions]
        if True in correctness:
            first_correct = correctness.index(True)
            time_fraction = 1 - \
                min(1.0, submissions[first_correct][2] / duration)
            self.scores[self.query_id] = max(0, MAX_POINT_TASK_END + (
                (MAX_POINT - MAX_POINT_TASK_END) * time_fraction) - (first_correct * PENALTY_PER_WRONG))
        self.write_to_db()

    def get_current_query(self):
        return ALL_QUERIES[self.query_ids[self.query_id]]

    def get_current_score(self):
        return round(self.scores[self.query_id], 2)

    def get_total_score(self):
        return round(sum(self.scores), 2)

    def restore_from_dict(self, dictdata):
        self.name = dictdata["name"]
        self.time = dictdata["time"]
        self.scores = dictdata["scores"]
        self.submissions = dictdata["submissions"]
        self.query_ids = dictdata["query_ids"]
        self.query_id = dictdata["query_id"]
        self.id = dictdata["_id"]

    def to_dict(self):
        return {"name": self.name,
                "time": self.time,
                "scores": self.scores,
                "submissions": self.submissions,
                "query_ids": self.query_ids,
                "query_id": self.query_id}

    def next_query(self):
        self.time = datetime.now()
        self.query_id += 1
        self.write_to_db()
        if self.query_id >= len(self.query_ids):
            return False
        return True

    def write_to_db(self):
        if self.id:
            db.update_one({'_id': self.id}, {'$set': self.to_dict()})
        else:
            self.id = db.insert_one(self.to_dict()).inserted_id

    def detete(self):
        db.delete_one({'_id': self.id})

def get_score(session_name):
    session = LSCSession(session_name)
    print(session.submissions)
    print("Scores")
    print([round(score, 2) for score in session.scores])
    print("Total:", session.get_total_score())

if __name__ == "__main__":
    session_name = sys.argv[1]
    if session_name != "mysceal":
        print("Getting stats for session", session_name)
        get_score(session_name)
        try:
            to_delete = sys.argv[2]
            if to_delete == "del":
                session = LSCSession(session_name)
                session.detete()
        except IndexError as e:
            pass
    else:
        mysession = LSCSession("mysceal")
        mysession.submissions = [[["", True, 37]], [["", True, 158]], [
            ["", True, 90]], [["", False, 79], ["", True, 82]], []]
        for i in range(5):
            mysession.query_id = i
            mysession.get_score()
        print("Scores")
        print([round(score, 2) for score in mysession.scores])
        print("Total:", mysession.get_total_score())
    


# Coni
# [[['b00002411_21i6bq_20150319_162318e', True, 54]], 
# [['b00000511_21i6bq_20150307_114813e', True, 325]], 
# [['B00012345_21I6X0_20180523_152443E', True, 335]], [], []]
# Scores
# [92.5, 54.86, 53.47, 0, 0]
# Total: 200.83
# 
# Florian
# [[['b00002412_21i6bq_20150319_162319e', True, 37]], 
# [['20160917_130458_000', False, 140], 
# ['b00000507_21i6bq_20150307_114541e', True, 283]], 
# [], 
# [['b00000077_21i6bq_20150228_071546e', True, 162]], []]
# Scores
# [94.86, 50.69, 0, 77.5, 0]
# Total: 223.06

# Nhu_Exp_1
# [[['b00002413_21i6bq_20150319_162320e', True, 108]], 
# [['b00000506_21i6bq_20150307_114508e', True, 226]], 
# [], 
# [['b00000072_21i6bq_20150228_071542e', True, 352]], 
# []]
# Scores
# [85.0, 68.61, 0, 51.11, 0]
# Total: 204.72

# Khiem_exp_1
# [[['b00002366_21i6bq_20150316_152935e', False, 11], 
# ['b00002410_21i6bq_20150319_162318e', True, 23]], 
# [['20161002_133656_000', False, 117], ['20160917_130458_000', False, 128], ['b00000506_21i6bq_20150307_114508e', True, 237]],
# [['20160906_212416_000', False, 30], ['B00012345_21I6X0_20180523_152443E', True, 264]], 
# [], 
# []]
# Scores
# [86.81, 47.08, 53.33, 0, 0]
# Total: 187.22

# Tu_Exp1
# [[['b00002412_21i6bq_20150319_162319e', True, 13]], 
# [['b00000518_21i6bq_20150307_115233e', True, 295]], 
# [], 
# [['b00000072_21i6bq_20150228_071542e', True, 342]], 
# []]
# Scores
# [98.19, 59.03, 0, 52.5, 0]
# Total: 209.72

# Getting stats for session An
# [[['b00002411_21i6bq_20150319_162318e', True, 87]], 
# [['b00000506_21i6bq_20150307_114508e', True, 303]], 
# [], 
# [], 
# []]
# Scores
# [87.92, 57.92, 0, 0, 0]
# Total: 145.83

# Getting stats for session Diem
# [[['b00002410_21i6bq_20150319_162318e', True, 67]], 
# [['b00000492_21i6bq_20150307_114114e', False, 298], ['b00000506_21i6bq_20150307_114508e', True, 336]], 
# [['20160906_215143_000', False, 292]], 
# [['b00000079_21i6bq_20150228_071547e', True, 256]], 
# []]
# Scores
# [90.69, 43.33, 0, 64.44, 0]
# Total: 198.47

# MySceal
# [[[True, 37]], [[True, 158]], [[True, 90]], [[False, 79], [True, 82]], []] 
# [94.86, 78.06, 87.5, 78.61, 0]
# Total: 339.03
