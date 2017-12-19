from pymongo import MongoClient

from secret import key, mongo_uri

def connect_db():
    if mongo_uri:
        client = MongoClient(mongo_uri)
        
    else:
        client = MongoClient()
    
    db = client.quotes
    quotes_db = db.truncated_quotes
    return quotes_db

class NotFeasible(Exception):
    pass

class SearchModel():
    def __init__(self):
        self.quotes_db = connect_db()
    
    def search(self, origin_ids, destination_id, outbound_date="Anytime", inbound_date="Anytime"):
        """
        Dates: Either "Anytime", or a date in January (eg. "24")
        """
        n_origins = len(origin_ids)
        
        quotes = []
        
        for origin_id in origin_ids:
            r = self.quotes_db.find(
                {
                    "Origin": origin_id,
                    "Destination": destination_id              
                })
            
            try:
                quotes.append(sorted(list(r),
                                     key=lambda q: q['MinPrice'])[0])
                
            except IndexError:
                raise NotFeasible
        
        return quotes
    
    def get_all(self):
        r = self.quotes_db.find()
        
        return list(r)
