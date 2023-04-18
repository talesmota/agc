import datetime
from infra.sqlite import insert, select

class Review:
    def __init__(self, uid, created_at = None):
        self.uid = uid
        if created_at is None:
            self.created_at = datetime.datetime.now()
        else:
            self.created_at = created_at 

    def save(self):
        insert(f'INSERT INTO reviews (uid, created_at) VALUES("{self.uid}", "{self.created_at}")');

    @staticmethod
    def find_id( uid):
        reviews = []
        def mapp(x):
            review = Review(x[1], x[2])
            return review
        sql = f'SELECT * from reviews WHERE uid = "{uid}";'
        select( sql, lambda x: reviews.append(mapp(x)))
        return reviews

    @staticmethod
    def find_all():
        reviews = []
        def mapp(x):
            review = Review(x[1], x[2])
            return review
        sql = f'SELECT * from reviews order by created_at asc;'
        select( sql, lambda x: reviews.append(mapp(x)))
        return reviews

