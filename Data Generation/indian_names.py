# resources/indian_names.py

MALE_FIRST_NAMES = [
    # South
    "Murugan", "Karthik", "Suresh", "Ramesh", "Babu", "Venkatesh", "Muthu",
    "Shiva", "Ramu", "Prabhu", "Mani", "Selvam", "Raj", "Anbu", "Kumar",
    "Srinu", "Naresh", "Ravi", "Syed", "Mohammed", "Arun", "Dinesh", "Kannan",

    # North
    "Sonu", "Monu", "Rahul", "Amit", "Sandeep", "Vikas", "Deepak", "Sunil",
    "Anil", "Ajay", "Vijay", "Suraj", "Ram", "Shyam", "Mukesh", "Rakesh",
    "Md", "Imran", "Rizwan", "Pankaj", "Dharmendra",

    # West
    "Santosh", "Ganesh", "Vithal", "Sachin", "Vishal", "Prakash", "Kiran",
    "Maruti", "Akshay", "Sagar", "Nilesh",

    # East
    "Bapi", "Raju", "Tapan", "Mithun", "Prasenjit", "Sujit", "Sanjay",
    "Bikas", "Sukumar", "Ratan", "Arup", "Tarikul"
]

FEMALE_FIRST_NAMES = [
    # South
    "Lakshmi", "Bhavani", "Saraswati", "Parvathi", "Valli", "Amulu", "Roopa",

    # North
    "Sunita", "Anita", "Rekha", "Pooja", "Manju", "Seema", "Geeta",

    # West
    "Savita", "Kavita", "Vaishali", "Priyanka",

    # East
    "Pampa", "Ruma", "Tumpa", "Alpana", "Mampi"
]

SURNAMES = [
    "Kumar",
    "Reddy",
    "Rao",
    "Gowda",
    "Raj",
    "Babu",
    "M",
    "K",
    "V",
    "S",
    "P",
    "Gounder",
    "Nadar",
    "Naidu",
    "Basha",
    "Sheik",
    "Singh",
    "Yadav",
    "Pal",
    "Paswan",
    "Sharma",
    "Verma",
    "Maurya",
    "Gupta",
    "Chauhan",
    "Ansari",
    "Khan",
    "Ali",
    "Devi",
    "Kumari",
    "Khatun",
    "Pawar",
    "Shinde",
    "Kamble",
    "Jadhav",
    "Kadam",
    "Kale",
    "More",
    "Shaikh",
    "Patil",
    "Gaikwad",
    "Das",
    "Mondal",
    "Biswas",
    "Barman",
    "Mahato",
    "Ghosh",
    "Sarkar",
    "Roy",
    "Hossain",
    "Sheikh"
]

# Remove duplicates while preserving order
MALE_FIRST_NAMES = list(dict.fromkeys(MALE_FIRST_NAMES))
FEMALE_FIRST_NAMES = list(dict.fromkeys(FEMALE_FIRST_NAMES))
SURNAMES = list(dict.fromkeys(SURNAMES))