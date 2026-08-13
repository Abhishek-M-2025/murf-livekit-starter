import os
import sqlite3
import json
import db

def main():
    analytics = db.get_call_analytics()
    print(json.dumps(analytics))

if __name__ == "__main__":
    main()
