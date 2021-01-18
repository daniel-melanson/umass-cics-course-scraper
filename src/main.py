import sys

import pymongo
from pymongo import MongoClient

import spire
import web

def is_name_short_for(a: str, b: str):
    a_words = a.split(" ")
    b_words = b.split(" ")

    if b_words[0].find(a_words[0]) == 0 or a_words[0].find(b_words[0]) == 0:
        b_remaining = set(b_words[1:])
        a_remaining = set(a_words[1:])
 
        return b_remaining.issubset(a_remaining) or a_remaining.issubset(b_remaining)


def add_course_to_staff(staff_collection, course_staff, course_id):
    for staff_name in course_staff:
        if staff_collection.update_one({
            "names": {"$in": [staff_name]}
        }, {
            "$push": {
                "courses": course_id
            }
        }).modified_count != 0:
            continue

        cursor = staff_collection.aggregate([
            {"$match": {"$text": {"$search": staff_name}}},
            {
                "$project": {
                    "_score": {"$divide": [{"$meta": "textScore"}, {"$size": "$names"}]},
                    "names": 1,
                }
            },
            {"$sort": {"_score": -1}},
        ])

        accepted = None
        for possible_staff in cursor:
            if possible_staff['_score'] >= 1:
                accepted = possible_staff
                break

            found = False
            for name in possible_staff['names']:
                if is_name_short_for(name, staff_name):
                    found = True
                    break

            if found:
                accepted = possible_staff
                break

        if accepted:
            staff_collection.find_one_and_update({
                "_id": accepted['_id']
            }, {
                "$push": {
                    "courses": course_id,
                    "names": staff_name
                }
            })


def main(args):
    if len(args) != 3:
        print("Please supply a connection string and db-name.")
        return

    client = MongoClient(args[1])
    db = client[args[2]]
    semester_collection = db.semesters
    course_collection = db.courses
    staff_collection = db.staff

    # retrieve course information from CICS and Math department websites
    course_map = web.scrape_courses()
    # get sections, staff, and additional course information from spire
    spire.scrape_additional_course_information(course_map)

    # push information into db
    course_collection.insert_many(course_map.values())
    course_map = None

    # retrieve staff information from CICS website and push
    staff_collection.insert_many(web.retrieve_staff_information())
    # retrieve course information and push
    semester_collection.insert_many(web.get_academic_schedule())

    course_collection.create_index([("id", pymongo.TEXT)])
    staff_collection.create_index([("names", pymongo.TEXT)])

    for course in course_collection.find():
        if "staff" not in course:
            continue

        add_course_to_staff(staff_collection, course['staff'], course['id'])


if __name__ == "__main__":
    main(sys.argv)
