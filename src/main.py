import sys
import os

import pymongo
from pymongo import MongoClient

import re
import spire
import web


def is_name_short_for(a: str, b: str):
    a_words = a.split(" ")
    b_words = b.split(" ")

    if b_words[0].find(a_words[0]) == 0 or a_words[0].find(b_words[0]) == 0:
        b_remaining = set(b_words[1:])
        a_remaining = set(a_words[1:])
 
        return b_remaining.issubset(a_remaining) or a_remaining.issubset(b_remaining)


def find_best_match_for(staff_name: str, cursor):
    for possible_staff in cursor:
        if possible_staff['_score'] >= 1:
            return possible_staff

        for name in possible_staff['names']:
            if is_name_short_for(name, staff_name):
                return possible_staff


def add_course_to_staff(staff_collection, course_staff, course_id):
    for staff_name in course_staff:
        staff = staff_collection.find_one({
            "names": {"$in": [staff_name]}
        })

        if not staff:
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

            staff = find_best_match_for(staff_name, cursor)

        if staff:
            operation = {
                    '$push': {
                        'courses': course_id
                    }
                } if 'courses' in staff else {
                    '$set': {
                        'courses': [course_id]
                    }
                }

            staff_collection.update_one({
                '_id': staff['_id']
            }, operation)


def reg_replace(match: str, pattern: str, replace: str, flags) -> str:
    return re.sub(
        pattern,
        replace,
        match,
        flags=flags
    )


def main(args):
    if len(args) != 2:
        print("Please supply a db-name.")
        return

    client = MongoClient(os.environ['MONGO_CONNECTION_STRING'].replace("DATABASE", args[1]))
    db = client[args[1]]
    semester_collection = db.semesters
    course_collection = db.courses
    staff_collection = db.staff

    # retrieve course information from CICS and Math department websites
    course_map = web.scrape_courses()
    
    # use course description pre reqs
    for (_, course) in course_map.items():
        description = course['description']

        prereq_match = re.search(
            r"(undergraduate)? prerequisite(s)?:.+",
            description,
            flags=re.I
        )

        if prereq_match:
            description = description.replace(prereq_match.group(), "")

            course['enrollmentRequirement'] = reg_replace(
                prereq_match.group(),
                r" \d credits(\.)?",
                "",
                flags=re.M | re.I
            )

        course['description'] = reg_replace(
            description,
            r" \d credits\.",
            "",
            flags=re.M | re.I
        )

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

    client.close()


if __name__ == "__main__":
    main(sys.argv)
