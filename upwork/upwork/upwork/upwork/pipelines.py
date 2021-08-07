# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import pymongo

# from scrapy.utils.project import get_project_settings
# from scrapy.exceptions import DropItem

# settings = get_project_settings()



class MongoDBPipeline(object):
    
    collection_name = 'adorebeauty'
    def open_spider(self,spider):
        self.client = pymongo.MongoClient(
            'localhost', 
            27017
        )
        self.db = self.client['adorebeauty']
        
    def process_item(self, item, spider):
        self.db[self.collection_name].insert(item)
        return item