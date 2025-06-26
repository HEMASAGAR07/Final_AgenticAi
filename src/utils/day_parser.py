class DayParser:
    def __init__(self):
        self.day_map = {
            "mon": "Monday",
            "tue": "Tuesday",
            "wed": "Wednesday",
            "thu": "Thursday",
            "fri": "Friday",
            "sat": "Saturday",
            "sun": "Sunday"
        }

    def parse_available_days(self, days_str):
        days_str = days_str.strip().lower()
        
        if "-" in days_str:
            return self._parse_day_range(days_str)
        else:
            return self._parse_day_list(days_str)

    def _parse_day_range(self, days_str):
        start, end = [d.strip() for d in days_str.split("-")]
        keys = list(self.day_map.keys())
        start_idx = keys.index(start)
        end_idx = keys.index(end)
        
        if end_idx < start_idx:
            end_idx += 7
            
        result = []
        for i in range(start_idx, end_idx + 1):
            key = keys[i % 7]
            result.append(self.day_map[key])
        return result

    def _parse_day_list(self, days_str):
        parts = [d.strip() for d in days_str.split(",")]
        return [self.day_map.get(p, "") for p in parts if p in self.day_map] 