import csv


def get_security_info(ticker):

    try:

        with open("../02_Data/security_master.csv", "r", encoding="utf-8") as file:

            reader = csv.DictReader(file)

            for row in reader:

                if row["ticker"].upper() == ticker.upper():

                    return {
                        "ticker": row["ticker"],
                        "name": row["name"],
                        "category": row["category"],
                        "expense_ratio": row["expense_ratio"]
                    }

    except:

        pass

    return None