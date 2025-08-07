#!/usr/bin/env python3
"""
SCHOOL SESSION DATA EXPORTER MODULE
Exports collected parent/student session data to CSV/Excel files for school reporting
"""

import os
import csv
import json
from datetime import datetime
from config import Config

class SchoolSessionDataExporter:
    """Handles exporting school session data to CSV files for school reporting"""
    
    def __init__(self):
        self.export_folder = "school_data"
        self.csv_file = "parent_inquiries.csv"
        self.ensure_export_directory()
        self.ensure_csv_headers()
    
    def ensure_export_directory(self):
        """Create export directory if it doesn't exist"""
        if not os.path.exists(self.export_folder):
            os.makedirs(self.export_folder, exist_ok=True)
            print(f"📁 Created school data folder: {self.export_folder}")
    
    def ensure_csv_headers(self):
        """Ensure CSV file exists with proper headers for school inquiries"""
        csv_path = os.path.join(self.export_folder, self.csv_file)
        
        # Define CSV headers based on school session variables
        headers = [
            "call_sid",
            "call_date",
            "call_time", 
            "call_direction",
            "parent_name",
            "parent_phone",
            "student_name",
            "student_age",
            "admission_type",
            "admission_class",
            "student_location",
            "inquiry_focus",
            "transport_required",
            "scholarship_interest",
            "meeting_requested",
            "call_duration_seconds",
            "conversation_summary",
            "follow_up_required",
            "priority_level"
        ]
        
        # Create CSV with headers if it doesn't exist
        if not os.path.exists(csv_path):
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(headers)
            print(f"📊 Created school data CSV: {csv_path}")
    
    def export_session_data(self, session, call_duration=None):
        """Export session data to CSV file"""
        try:
            csv_path = os.path.join(self.export_folder, self.csv_file)
            
            # Extract session variables
            variables = session.session_variables
            
            # Calculate call duration if not provided
            if call_duration is None:
                call_duration = self._calculate_call_duration(session)
            
            # Generate conversation summary
            conversation_summary = self._generate_conversation_summary(session)
            
            # Determine follow-up requirement
            follow_up_required = self._needs_follow_up(session)
            
            # Determine priority level
            priority_level = self._determine_priority_level(session)
            
            # Prepare row data
            row_data = [
                session.call_sid,
                datetime.now().strftime("%Y-%m-%d"),  # call_date
                datetime.now().strftime("%H:%M:%S"),  # call_time
                session.call_direction,  # inbound/outbound
                variables.get("parent_name", ""),
                variables.get("parent_phone", ""),
                variables.get("student_name", ""),
                variables.get("student_age", ""),
                variables.get("admission_type", ""),
                variables.get("admission_class", ""),
                variables.get("student_location", ""),
                variables.get("inquiry_focus", ""),
                "Yes" if variables.get("student_location") else "No",  # transport_required
                "Yes" if "scholarship" in str(variables.get("inquiry_focus", "")).lower() else "No",  # scholarship_interest
                "Yes" if any(word in str(session.conversation_history).lower() for word in ["meeting", "visit", "demo"]) else "No",  # meeting_requested
                call_duration,
                conversation_summary,
                follow_up_required,
                priority_level
            ]
            
            # Append to CSV file
            with open(csv_path, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(row_data)
            
            # Log successful export
            parent_info = variables.get("parent_name", "Unknown")
            inquiry_info = variables.get("inquiry_focus", "general inquiry")
            print(f"📊 Exported school session data: {parent_info} - {inquiry_info}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error exporting session data: {e}")
            return False
    
    def _calculate_call_duration(self, session):
        """Calculate call duration from conversation history"""
        try:
            # Simple estimation based on conversation length
            # In a real implementation, you'd track start time
            conversation_length = len(session.conversation_history)
            estimated_duration = conversation_length * 10  # ~10 seconds per exchange
            return max(estimated_duration, 30)  # Minimum 30 seconds
        except:
            return 60  # Default 1 minute
    
    def _generate_conversation_summary(self, session):
        """Generate a brief summary of the conversation"""
        try:
            if not hasattr(session, 'conversation_history') or not session.conversation_history:
                return "No conversation recorded"
            
            # Get key conversation elements
            history = session.conversation_history
            summary_parts = []
            
            # Check what was discussed
            variables = session.session_variables
            if variables.get("admission_type"):
                summary_parts.append(f"Admission: {variables['admission_type']}")
            if variables.get("admission_class"):
                summary_parts.append(f"Class: {variables['admission_class']}")
            if variables.get("inquiry_focus"):
                summary_parts.append(f"Focus: {variables['inquiry_focus']}")
            if variables.get("student_location"):
                summary_parts.append(f"Location: {variables['student_location']}")
            
            # Add conversation length info
            summary_parts.append(f"Exchanges: {len(history)}")
            
            return " | ".join(summary_parts) if summary_parts else "Brief conversation"
            
        except Exception as e:
            return f"Summary error: {str(e)[:50]}"
    
    def _needs_follow_up(self, session):
        """Determine if follow-up is required"""
        try:
            variables = session.session_variables
            
            # Follow-up needed if:
            # 1. Parent showed interest but no meeting scheduled
            # 2. Scholarship inquiry without details
            # 3. Transport inquiry without location
            # 4. Admission inquiry without class specified
            
            if variables.get("inquiry_focus") == "admission" and not variables.get("admission_class"):
                return "Yes - Need Class Details"
            elif variables.get("inquiry_focus") == "transport" and not variables.get("student_location"):
                return "Yes - Need Location"
            elif variables.get("inquiry_focus") == "fees" and "scholarship" in str(session.conversation_history).lower():
                return "Yes - Scholarship Interest"
            elif any(word in str(session.conversation_history).lower() for word in ["meeting", "visit", "demo"]):
                return "Yes - Meeting Requested"
            elif variables.get("admission_type") and not variables.get("parent_name"):
                return "Yes - Need Parent Details"
            else:
                return "No"
                
        except:
            return "Unknown"
    
    def _determine_priority_level(self, session):
        """Determine priority level for follow-up"""
        try:
            variables = session.session_variables
            
            # High priority: Meeting requested, scholarship interest, urgent admission
            if any(word in str(session.conversation_history).lower() for word in ["meeting", "visit", "demo"]):
                return "High"
            elif "scholarship" in str(session.conversation_history).lower():
                return "High"
            elif variables.get("admission_type") == "transfer":
                return "Medium"
            elif variables.get("inquiry_focus") in ["fees", "transport"]:
                return "Medium"
            else:
                return "Low"
                
        except:
            return "Low"
    
    def get_export_stats(self):
        """Get statistics about exported data"""
        try:
            csv_path = os.path.join(self.export_folder, self.csv_file)
            
            if not os.path.exists(csv_path):
                return {"total_inquiries": 0, "file_size": 0}
            
            # Count rows (minus header)
            with open(csv_path, 'r', encoding='utf-8') as csvfile:
                row_count = sum(1 for row in csv.reader(csvfile)) - 1  # Subtract header
            
            # Get file size
            file_size = os.path.getsize(csv_path)
            
            return {
                "total_inquiries": max(0, row_count),
                "file_size_kb": round(file_size / 1024, 2),
                "csv_file": csv_path
            }
            
        except Exception as e:
            print(f"❌ Error getting export stats: {e}")
            return {"total_inquiries": 0, "file_size": 0, "error": str(e)}
    
    def generate_school_report(self):
        """Generate a summary report for school management"""
        try:
            csv_path = os.path.join(self.export_folder, self.csv_file)
            
            if not os.path.exists(csv_path):
                return "No data available for report"
            
            # Read CSV data
            inquiries = []
            with open(csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    inquiries.append(row)
            
            if not inquiries:
                return "No inquiries found"
            
            # Generate statistics
            total_inquiries = len(inquiries)
            admission_inquiries = len([i for i in inquiries if i.get('admission_type')])
            fee_inquiries = len([i for i in inquiries if i.get('inquiry_focus') == 'fees'])
            transport_inquiries = len([i for i in inquiries if i.get('transport_required') == 'Yes'])
            high_priority = len([i for i in inquiries if i.get('priority_level') == 'High'])
            
            report = f"""
📊 SCHOOL INQUIRY REPORT
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}

📈 SUMMARY:
• Total Inquiries: {total_inquiries}
• Admission Inquiries: {admission_inquiries}
• Fee Inquiries: {fee_inquiries}
• Transport Inquiries: {transport_inquiries}
• High Priority Follow-ups: {high_priority}

📋 RECENT INQUIRIES (Last 5):
"""
            
            # Add recent inquiries
            for inquiry in inquiries[-5:]:
                report += f"• {inquiry.get('call_date', 'Unknown')} - {inquiry.get('parent_name', 'Unknown')} - {inquiry.get('inquiry_focus', 'General')}\n"
            
            return report
            
        except Exception as e:
            return f"Error generating report: {e}"

# Global school session data exporter instance
school_session_exporter = SchoolSessionDataExporter()