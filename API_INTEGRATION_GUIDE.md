# 🏫 School AI - API Integration & Data Management Guide

**Complete Guide for School Admission Systems**

---

## 📊 **School Session Data Export**

Your system automatically exports parent inquiry data to `school_data/parent_inquiries.csv`:

```csv
call_sid,call_date,call_time,parent_name,student_name,admission_type,admission_class,inquiry_focus,follow_up_required,priority_level
CA123,2024-01-15,14:30:25,John Smith,Rahul,firsttime,KG1,fees,No,Medium
```

## 🔌 **API Integration for Schools**

### **School API Client**

Create `school_api_integrations.py`:

```python
#!/usr/bin/env python3
"""
SCHOOL API INTEGRATIONS MODULE
Handles external API calls for school admission systems
"""

import requests
import json
import time
from datetime import datetime
from config import Config

class SchoolAPIClient:
    """Handles integration with school management system"""
    
    def __init__(self):
        self.api_url = Config.SCHOOL_API_URL
        self.api_key = Config.SCHOOL_API_KEY
        self.timeout = Config.SCHOOL_API_TIMEOUT
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
    
    def fetch_class_availability(self, class_name="KG1"):
        """Fetch class availability from school system"""
        try:
            # Check cache first
            cache_key = f"class_{class_name}"
            if self._is_cache_valid(cache_key):
                return self.cache[cache_key]["data"]
            
            # Make API call
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "class_name": class_name,
                "academic_year": "2024-25"
            }
            
            response = requests.post(
                f"{self.api_url}/class-availability",
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                self.cache[cache_key] = {
                    "data": data,
                    "timestamp": time.time()
                }
                return data
            else:
                return {"available_seats": 0, "success": False}
                
        except Exception as e:
            print(f"❌ API Error: {e}")
            return {"available_seats": 0, "success": False}
    
    def check_admission_eligibility(self, student_age, class_name):
        """Check if student is eligible for admission"""
        age_rules = {
            "KG1": {"min_age": 3, "max_age": 4},
            "KG2": {"min_age": 4, "max_age": 5},
            "Class 1": {"min_age": 5, "max_age": 6},
            "Class 2": {"min_age": 6, "max_age": 7}
        }
        
        if class_name not in age_rules:
            return {"eligible": False, "reason": "Invalid class"}
        
        rule = age_rules[class_name]
        if rule["min_age"] <= student_age <= rule["max_age"]:
            return {"eligible": True, "reason": "Age appropriate"}
        else:
            return {"eligible": False, "reason": f"Age {student_age} not suitable for {class_name}"}
    
    def get_fee_structure(self, class_name, admission_type="firsttime"):
        """Get fee structure for specific class"""
        fee_structure = {
            "KG1": {"tuition_fee": 4000, "transport_fee": 600, "admission_fee": 2000},
            "KG2": {"tuition_fee": 4500, "transport_fee": 600, "admission_fee": 2000},
            "Class 1": {"tuition_fee": 5000, "transport_fee": 700, "admission_fee": 2500},
            "Class 2": {"tuition_fee": 5500, "transport_fee": 700, "admission_fee": 2500}
        }
        
        if class_name not in fee_structure:
            return {"success": False, "error": "Invalid class"}
        
        fees = fee_structure[class_name].copy()
        
        # Transfer students get 50% discount on admission fee
        if admission_type == "transfer":
            fees["admission_fee"] = fees["admission_fee"] * 0.5
        
        return {"success": True, **fees}
    
    def _is_cache_valid(self, cache_key):
        """Check if cached data is still valid"""
        if cache_key not in self.cache:
            return False
        cache_age = time.time() - self.cache[cache_key]["timestamp"]
        return cache_age < self.cache_duration

# Global school API client instance
school_api = SchoolAPIClient()
```

## 📝 **Manual Data Management**

### **For Schools Without API Support**

Create `school_manual_data.json`:

```json
{
  "class_availability": {
    "last_updated": "2024-01-15T10:30:00Z",
    "updated_by": "Principal (Mrs. Sharma)",
    "classes": {
      "KG1": {"total_capacity": 30, "available_seats": 5},
      "KG2": {"total_capacity": 30, "available_seats": 8},
      "Class 1": {"total_capacity": 35, "available_seats": 12}
    }
  },
  "fee_structure": {
    "last_updated": "2024-01-10T09:00:00Z",
    "academic_year": "2024-25",
    "classes": {
      "KG1": {"tuition_fee": 4000, "transport_fee": 600, "admission_fee": 2000},
      "KG2": {"tuition_fee": 4500, "transport_fee": 600, "admission_fee": 2000},
      "Class 1": {"tuition_fee": 5000, "transport_fee": 700, "admission_fee": 2500}
    }
  }
}
```

### **Manual Data Manager**

Create `school_manual_data_manager.py`:

```python
#!/usr/bin/env python3
"""
SCHOOL MANUAL DATA MANAGEMENT MODULE
For schools without API support
"""

import json
import os
import time
from datetime import datetime

class SchoolManualDataManager:
    """Manages manually updated school data"""
    
    def __init__(self, data_file="school_manual_data.json"):
        self.data_file = data_file
        self.data = self.load_data()
        self.last_check = 0
        self.check_interval = 60  # Check every minute
    
    def load_data(self):
        """Load data from JSON file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                print(f"📋 Loaded school data from {self.data_file}")
                return data
            else:
                return self.create_default_data()
        except Exception as e:
            print(f"❌ Error loading school data: {e}")
            return self.create_default_data()
    
    def create_default_data(self):
        """Create default school data structure"""
        default_data = {
            "class_availability": {
                "last_updated": datetime.now().isoformat(),
                "updated_by": "System",
                "classes": {
                    "KG1": {"total_capacity": 30, "available_seats": 10},
                    "KG2": {"total_capacity": 30, "available_seats": 8},
                    "Class 1": {"total_capacity": 35, "available_seats": 15}
                }
            },
            "fee_structure": {
                "last_updated": datetime.now().isoformat(),
                "academic_year": "2024-25",
                "classes": {
                    "KG1": {"tuition_fee": 4000, "transport_fee": 600, "admission_fee": 2000},
                    "KG2": {"tuition_fee": 4500, "transport_fee": 600, "admission_fee": 2000},
                    "Class 1": {"tuition_fee": 5000, "transport_fee": 700, "admission_fee": 2500}
                }
            }
        }
        self.save_data(default_data)
        return default_data
    
    def get_class_availability(self, class_name):
        """Get current class availability"""
        self.check_for_updates()
        
        classes_data = self.data.get("class_availability", {}).get("classes", {})
        
        if class_name in classes_data:
            class_info = classes_data[class_name]
            return {
                "available_seats": class_info.get("available_seats", 0),
                "total_capacity": class_info.get("total_capacity", 0),
                "success": True,
                "last_updated": self.data.get("class_availability", {}).get("last_updated")
            }
        else:
            return {"available_seats": 0, "success": False, "error": "Class not found"}
    
    def get_fee_structure(self, class_name):
        """Get fee structure for specific class"""
        self.check_for_updates()
        
        fee_data = self.data.get("fee_structure", {}).get("classes", {})
        
        if class_name in fee_data:
            return {"success": True, **fee_data[class_name]}
        else:
            return {"success": False, "error": "Fee structure not found"}
    
    def check_for_updates(self):
        """Check if data file has been updated"""
        if time.time() - self.last_check < self.check_interval:
            return False
        
        try:
            if os.path.exists(self.data_file):
                file_modified = os.path.getmtime(self.data_file)
                data_timestamp = datetime.fromisoformat(
                    self.data.get("class_availability", {}).get("last_updated", "1970-01-01T00:00:00")
                ).timestamp()
                
                if file_modified > data_timestamp:
                    print("🔄 School data file updated, reloading...")
                    self.data = self.load_data()
                    self.last_check = time.time()
                    return True
        except Exception as e:
            print(f"⚠️ Error checking for updates: {e}")
        
        self.last_check = time.time()
        return False
    
    def save_data(self, data=None):
        """Save data to JSON file"""
        try:
            if data is None:
                data = self.data
            
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"💾 Saved school data to {self.data_file}")
            return True
        except Exception as e:
            print(f"❌ Error saving school data: {e}")
            return False

# Global school manual data manager instance
school_manual_data = SchoolManualDataManager()
```

## 🔄 **Integration with Router**

Update `router.py` to include school API integration:

```python
# Add this import at the top
from school_api_integrations import school_api
# OR for manual data:
# from school_manual_data_manager import school_manual_data

# Add this method to ResponseRouter class
def _handle_admission_inquiry(self, user_input, session):
    """Handle admission inquiries with real-time data"""
    user_lower = user_input.lower()
    
    # Detect admission inquiry
    if any(word in user_lower for word in ["admission", "admit", "enroll", "join", "प्रवेश"]):
        
        # Extract class information
        class_mappings = {
            "kg1": "KG1", "kg 1": "KG1", "nursery": "KG1",
            "kg2": "KG2", "kg 2": "KG2", "ukg": "KG2",
            "1st class": "Class 1", "class 1": "Class 1", "first class": "Class 1",
            "2nd class": "Class 2", "class 2": "Class 2", "second class": "Class 2"
        }
        
        requested_class = None
        for class_key, class_value in class_mappings.items():
            if class_key in user_lower:
                requested_class = class_value
                session.update_session_variable("requested_class", class_value)
                break
        
        if requested_class:
            # Fetch availability (API or manual data)
            availability_data = school_api.fetch_class_availability(requested_class)
            # OR for manual data:
            # availability_data = school_manual_data.get_class_availability(requested_class)
            
            if availability_data.get("success", True) and availability_data.get("available_seats", 0) > 0:
                seats = availability_data["available_seats"]
                response = f"Great! We have {seats} seats available in {requested_class}. Would you like to know about the admission process and fees?"
                return "TTS", response
            else:
                return "TTS", f"I'm sorry, {requested_class} is currently full. Would you like to know about other classes?"
        else:
            return "TTS", "I'd be happy to help with admission. Which class are you interested in? We have KG1, KG2, and Classes 1-5 available."
    
    return None, None

# Update get_school_response method
def get_school_response(self, user_input, session):
    """Enhanced response routing with school API integration"""
    
    # PRIORITY 1: Check for admission inquiry
    response_type, content = self._handle_admission_inquiry(user_input, session)
    if response_type:
        return response_type, content
    
    # PRIORITY 2: Existing school response logic
    # ... rest of existing method ...
```

## 📊 **Staff Update Instructions**

### **For JSON Method:**
```
STAFF INSTRUCTIONS - UPDATING SCHOOL DATA:

1. Open school_manual_data.json on computer
2. Find "class_availability" section  
3. Update "available_seats" for each class
4. Update "last_updated" with current date/time
5. Update "updated_by" with your name
6. Save file - system updates automatically!

EXAMPLE:
"classes": {
  "KG1": {"total_capacity": 30, "available_seats": 3},  ← Updated seats
  "KG2": {"total_capacity": 30, "available_seats": 8}
}
```

### **For API Method:**
```
STAFF INSTRUCTIONS - API INTEGRATION:

1. Ensure school management system API is accessible
2. Configure API credentials in .env file
3. Test API endpoints are working
4. System automatically fetches real-time data
5. No manual updates needed!
```

---

**Built with ❤️ for School Management Systems**