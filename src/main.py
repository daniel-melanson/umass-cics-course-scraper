import sys

import pymongo
from pymongo import MongoClient

import spire
import web


def main(args):
    if len(args) != 3:
        print("Please supply a connection string and db-name.")
        return

    # retrieve course information from CICS and Math department websites
    course_map = web.scrape_courses()

    # retrieve additional staff information from CICS website
    staff_list = web.retrieve_staff_information()

    # get sections, staff, and additional course information from spire
    spire.scrape_additional_course_information(course_map)

    # push information into db
    client = MongoClient(args[1])
    db = client[args[2]]
    semester_collection = db.semesters
    course_collection = db.courses
    staff_collection = db.staff
    course_collection.insert_many(course_map.values())
    staff_collection.insert_many(staff_list)
    semester_collection.insert_many(web.get_academic_schedule())

    course_collection.create_index([('id', pymongo.TEXT)])
    staff_collection.create_index([('names', pymongo.TEXT)])

    for course in course_collection.find():
        if 'staff' not in course:
            continue

        course_id = course['id']
        course_staff = course['staff']
        for staff_name in course_staff:
            if staff_collection.update_one({
                'names': {'$in': [staff_name]}
            }, {
                '$push': {
                    'courses': course_id
                }
            }).modified_count != 0:
                continue

            cursor = staff_collection.find(
                {'$text': {'$search': staff_name}},
                {'score': {'$meta': 'textScore'}}
            ).sort([('score', {'$meta': 'textScore'})])
            entries = []
            for staff in cursor:
                score = staff['score']

                entries.append({
                    'staff': staff,
                    'score': score / len(staff['names']),
                })

            if len(entries) != 0:
                best = sorted(
                    entries,
                    key=lambda x: x['score'],
                    reverse=True
                )[0]
                if best['score'] > 1:
                    staff_collection.update_one({
                        "_id": best['staff']['_id'],
                    }, {
                        "$push": {
                            "courses": course_id,
                            "names": staff_name
                        },
                    })


if __name__ == '__main__':
    main(sys.argv)

'''
interface Event {
    date: Date;
    description: string;
}

export type Season = 'Spring' | 'Summer' | 'Fall';
export interface Semester {
    season: Season;
    year: number;
    startDate: Date;
    endDate: Date;
    events: Array<Event>;
}

export interface Course {
    subject: string;
    id: string;
    title: string;
    description: string;
    staff?: Array<string>;
    website?: string;
    frequency?: string;
    career?: string;
    units?: string;
    gradingBasis?: string;
    components?: string;
    enrollmentRequirement?: string;
}

export interface Staff {
    names: Array<string>;
    title: string;
    photo: string;
    email: string;
    website: string;
    courses: Array<string>;
}
'''
