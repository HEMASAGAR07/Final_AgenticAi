from datetime import date, datetime

class DateUtils:
    @staticmethod
    def date_serializer(obj):
        """Custom JSON serializer for handling dates"""
        if isinstance(obj, (date, datetime)):
            return obj.strftime("%Y-%m-%d")
        raise TypeError(f"Type {type(obj)} not serializable")

    @staticmethod
    def parse_date(date_str):
        """Parse a date string or date object into YYYY-MM-DD format"""
        if isinstance(date_str, (date, datetime)):
            return date_str.strftime("%Y-%m-%d")
        elif isinstance(date_str, str):
            # Try different date formats
            formats = [
                "%Y-%m-%d",
                "%d/%m/%Y",
                "%m/%d/%Y",
                "%Y/%m/%d",
                "%d-%m-%Y",
                "%m-%d-%Y"
            ]
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
                except ValueError:
                    continue
            
            # Check if it's a Python date object string representation
            if "datetime.date" in date_str:
                try:
                    # Extract year, month, day from string like "datetime.date(2003, 12, 13)"
                    parts = date_str.split("(")[1].split(")")[0].split(",")
                    year = int(parts[0])
                    month = int(parts[1])
                    day = int(parts[2])
                    return date(year, month, day).strftime("%Y-%m-%d")
                except:
                    pass
        return date_str 