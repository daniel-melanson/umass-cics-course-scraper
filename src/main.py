import sys

from pymongo import MongoClient

from unidecode import unidecode 

import spire
import web

'''
interface Course {
    id: string,
    title: string,
    description: string,
    credits: string
    enrollmentRequirements: string | undefined,
    instructors: string | undefined
    frequency: undefined | string,
}

interface Staff {
    name: string,
    courses: Array<string>
    email: string,
    website: string,
    title: undefined | string,
    photo: string | undefined
}
'''

def main(args):
    if len(args) != 3:
        print("Please supply a connection string and db-name.")
        return

    client = MongoClient(args[1])
    db = client[args[2]]

    '''
    # retrieve course information from CICS and Math department websites
    course_map = web.scrape_courses()

    # retrieve additional staff information from CICS website
    staff_list = web.retrieve_staff_information()

    # get sections, staff, and additional course information from spire
    spire.scrape_additional_course_information(course_map)
    
    # push information into db
    course_collection = db.courses
    course_collection.insert_many(course_map.values())

    staff_collection = db.staff
    staff_collection.insert_many(staff_list)

    semester_collection = db.semesters
    semester_collection.insert_many(web.get_academic_schedule())
    '''


if __name__ == "__main__":
    main(sys.argv)
