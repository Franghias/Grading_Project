# Assignment Management System

This document describes the new assignment management features that have been added to the Grading Project application.

## Overview

The assignment management system provides professors with full CRUD (Create, Read, Update, Delete) operations for managing assignments within their classes. Students can view assignments and submit their work, while professors can manage the assignment lifecycle.

## Backend Endpoints

### New Assignment Endpoints

#### 1. GET `/assignments/{assignment_id}`
- **Purpose**: Retrieve a specific assignment by ID
- **Access**: Professors and students enrolled in the class
- **Response**: Assignment details including name, description, and metadata

#### 2. PUT `/assignments/{assignment_id}`
- **Purpose**: Update an existing assignment
- **Access**: Professors only (must be teaching the class)
- **Request Body**: 
  ```json
  {
    "name": "Updated Assignment Name",
    "description": "Updated assignment description"
  }
  ```
- **Response**: Updated assignment details

#### 3. DELETE `/assignments/{assignment_id}`
- **Purpose**: Delete an assignment
- **Access**: Professors only (must be teaching the class)
- **Validation**: Cannot delete if assignments have existing submissions
- **Response**: Success message or error with details

### Existing Endpoints (Enhanced)

#### 1. POST `/classes/{class_id}/assignments/`
- **Purpose**: Create a new assignment for a class
- **Access**: Professors only (must be teaching the class)
- **Request Body**:
  ```json
  {
    "name": "Assignment Name",
    "description": "Assignment description",
    "class_id": 1
  }
  ```

#### 2. GET `/classes/{class_id}/assignments/`
- **Purpose**: Get all assignments for a class
- **Access**: Professors and students enrolled in the class

## Frontend Features

### Assignment Management Page (`6_Assignment_Management.py`)

The assignment management page has been completely redesigned with the following features:

#### 📋 View Assignments Tab
- **Assignment List**: Displays all assignments for the selected class
- **Assignment Details**: Shows name, description, and creation date
- **Edit Button**: Opens an inline edit form for each assignment
- **Delete Button**: Shows confirmation dialog before deletion
- **Responsive Layout**: Clean, organized display with proper spacing

#### ➕ Create New Assignment Tab
- **Form Validation**: Ensures assignment name is provided
- **Rich Text Area**: Larger text area for detailed descriptions
- **Clear Form Button**: Easy form reset functionality
- **Success Feedback**: Visual confirmation with balloons animation

#### Key Features
- **Tabbed Interface**: Organized workflow with separate tabs for viewing and creating
- **Confirmation Dialogs**: Prevents accidental deletions
- **Error Handling**: Comprehensive error messages and validation
- **Real-time Updates**: Page refreshes after successful operations
- **Responsive Design**: Works well on different screen sizes

### Integration with Other Pages

#### Professor View (`2_Professor_View.py`)
- **Manage Assignments Button**: Direct link to assignment management
- **Assignment Selection**: Dropdown to select assignments for grading
- **Default Assignment Creation**: Quick creation of standard assignments

#### Home Page (`1_Home.py`)
- **Assignment Display**: Shows assignments to students
- **Submission Interface**: Allows students to submit code for assignments
- **Grade Display**: Shows AI and professor grades

#### Student View (`3_Student_View.py`)
- **No Assignment Management Access**: Students cannot access assignment management
- **Class Enrollment**: Students can enroll in classes to access assignments

## Database Schema

### Assignment Model
```python
class Assignment(Base):
    __tablename__ = "assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text, nullable=True)
    class_id = Column(Integer, ForeignKey("classes.id"), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Pydantic Schemas
```python
class AssignmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class Assignment(AssignmentBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
```

## Security and Permissions

### Professor Permissions
- ✅ Create assignments for their classes
- ✅ View all assignments in their classes
- ✅ Edit assignment details
- ✅ Delete assignments (if no submissions exist)
- ✅ Access assignment management interface

### Student Permissions
- ✅ View assignments in enrolled classes
- ✅ Submit code for assignments
- ✅ View their own grades and feedback
- ❌ Cannot create, edit, or delete assignments
- ❌ Cannot access assignment management interface

### Validation Rules
1. **Assignment Name**: Required field, cannot be empty
2. **Class Ownership**: Only professors teaching the class can manage assignments
3. **Deletion Protection**: Cannot delete assignments with existing submissions
4. **Authentication**: All operations require valid JWT token

## Usage Examples

### Creating an Assignment
1. Navigate to Assignment Management page
2. Select the target class from dropdown
3. Go to "Create New Assignment" tab
4. Fill in assignment name and description
5. Click "Create Assignment"

### Editing an Assignment
1. Go to "View Assignments" tab
2. Click "Edit" button next to the assignment
3. Modify name and/or description
4. Click "Save Changes"

### Deleting an Assignment
1. Go to "View Assignments" tab
2. Click "Delete" button next to the assignment
3. Confirm deletion in the dialog
4. Assignment will be permanently removed

## Error Handling

### Common Error Scenarios
1. **Assignment Not Found**: 404 error when accessing non-existent assignment
2. **Permission Denied**: 403 error when unauthorized user tries to modify
3. **Validation Errors**: 400 error for invalid data (empty name, etc.)
4. **Deletion Blocked**: 400 error when trying to delete assignment with submissions
5. **Network Errors**: Proper error messages for connection issues

### User Feedback
- ✅ Success messages with green styling
- ❌ Error messages with red styling
- ⚠️ Warning messages for important confirmations
- ℹ️ Info messages for helpful guidance

## Testing

A comprehensive test script (`test_assignment_endpoints.py`) is provided to verify all endpoints work correctly:

```bash
python test_assignment_endpoints.py
```

The test script covers:
- User creation and authentication
- Class creation
- Assignment CRUD operations
- Permission validation
- Error handling

## Future Enhancements

### Potential Improvements
1. **Assignment Templates**: Pre-defined assignment templates
2. **Due Dates**: Add assignment deadlines
3. **File Attachments**: Support for assignment files
4. **Bulk Operations**: Create/edit multiple assignments at once
5. **Assignment Categories**: Organize assignments by type
6. **Submission Limits**: Restrict number of submissions per assignment
7. **Assignment Statistics**: View submission and grading statistics

### Technical Improvements
1. **Caching**: Cache assignment data for better performance
2. **Pagination**: Handle large numbers of assignments
3. **Search/Filter**: Find assignments by name or description
4. **Export/Import**: Bulk assignment management
5. **Audit Trail**: Track assignment changes over time

## Troubleshooting

### Common Issues
1. **Assignment Not Updating**: Check if you're a professor of the class
2. **Cannot Delete Assignment**: Ensure no students have submitted work
3. **Permission Errors**: Verify you're logged in as a professor
4. **Network Issues**: Check API URL configuration in environment variables

### Debug Information
- Check browser developer tools for network errors
- Verify JWT token is valid and not expired
- Ensure backend server is running on correct port
- Check database connection and permissions

## Conclusion

The assignment management system provides a comprehensive solution for professors to manage their course assignments while maintaining proper security and user experience. The system is designed to be intuitive, secure, and scalable for future enhancements. 