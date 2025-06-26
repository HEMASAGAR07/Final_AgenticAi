class ValidationUtils:
    @staticmethod
    def is_valid_name(name):
        """Validate a name with reasonable rules"""
        if not name:
            return False, "Name cannot be empty"
        
        # Remove extra spaces and standardize
        name = " ".join(name.split())
        
        # Basic validation rules
        if len(name) < 2:
            return False, "Name is too short"
        
        # Allow letters, spaces, hyphens, and apostrophes for names like O'Connor or Jean-Pierre
        if not all(c.isalpha() or c in " -'" for c in name):
            return False, "Name can only contain letters, spaces, hyphens, and apostrophes"
        
        # Check for at least one space (indicating first and last name)
        if " " not in name:
            return False, "Please provide both first and last name"
        
        # Check each part of the name
        parts = name.split()
        if any(len(part) < 2 for part in parts):
            return False, "Each part of the name must be at least 2 characters"
        
        # Check for obviously fake names
        fake_names = {"test test", "asdf asdf", "john doe", "jane doe"}
        if name.lower() in fake_names:
            return False, "Please provide your real name"
        
        return True, name

    @staticmethod
    def is_valid_phone(phone):
        """Validate a phone number with reasonable rules"""
        if not phone:
            return False, "Phone number cannot be empty"
        
        # Remove all non-digit characters for standardization
        digits = ''.join(filter(str.isdigit, phone))
        
        # Basic validation rules
        if len(digits) < 10 or len(digits) > 15:
            return False, "Phone number must be between 10 and 15 digits"
        
        # Allow common prefixes for Indian numbers
        if digits.startswith('91'):
            if len(digits) != 12:  # 91 + 10 digits
                return False, "Indian phone numbers should be 10 digits after country code"
        
        # Basic format check - don't be too strict about repeated digits
        # Only check for obvious test numbers
        obvious_test = {'1234567890', '0987654321', '1111111111', '0000000000'}
        if digits[-10:] in obvious_test:
            return False, "This appears to be a test phone number"
        
        # Format the number nicely for display
        if digits.startswith('91'):
            formatted = f"+{digits[:2]}-{digits[2:7]}-{digits[7:]}"
        else:
            formatted = f"+{digits}"
        
        return True, formatted 