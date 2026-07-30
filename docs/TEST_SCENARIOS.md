# End-to-End Test Scenarios

This document contains end-to-end scenario records covering all major user flows in STAIL Realty OS.

## Authentication & Registration

### SCENARIO-01: Successful User Registration
- **Actor**: Buyer
- **Steps**:
  1. Navigate to `/register`.
  2. Enter valid email, password, and name.
  3. Click Register.
- **Expected Result**: User account is created; user is redirected to dashboard.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Chrome

### SCENARIO-02: Registration with Existing Email
- **Actor**: Buyer
- **Steps**:
  1. Navigate to `/register`.
  2. Enter an email that is already registered.
  3. Click Register.
- **Expected Result**: Error message shown "Email already registered."
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Chrome

### SCENARIO-03: Successful Login
- **Actor**: Buyer
- **Steps**:
  1. Navigate to `/login`.
  2. Enter valid credentials.
  3. Click Login.
- **Expected Result**: User is authenticated and redirected to Dashboard.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Firefox

### SCENARIO-04: Login with Incorrect Password
- **Actor**: Buyer
- **Steps**:
  1. Navigate to `/login`.
  2. Enter valid email but incorrect password.
  3. Click Login.
- **Expected Result**: "Invalid credentials" error message is shown.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Chrome

### SCENARIO-05: Logout
- **Actor**: Buyer
- **Steps**:
  1. Click on User Profile in the navbar.
  2. Select Logout.
- **Expected Result**: Session ends, JWT cleared, user redirected to Login.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Chrome

## Dashboard & Navigation

### SCENARIO-06: Dashboard Loading for Buyer
- **Actor**: Buyer
- **Steps**:
  1. Login as Buyer.
  2. Observe Dashboard.
- **Expected Result**: Displays recent AI chats, saved properties, and preferences.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Chrome

### SCENARIO-07: Navbar Navigation
- **Actor**: Buyer
- **Steps**:
  1. Click "Properties" in navbar.
  2. Click "AI Search" in navbar.
- **Expected Result**: Successfully navigates between respective pages without reloading.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Mobile

### SCENARIO-08: Role-based Navigation Restriction
- **Actor**: Buyer
- **Steps**:
  1. Login as Buyer.
  2. Attempt to navigate to `/crm/leads`.
- **Expected Result**: Redirected to Dashboard with an "Unauthorized" toast.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Chrome

## AI Property Search (Chat)

### SCENARIO-09: Initializing AI Chat
- **Actor**: Buyer
- **Steps**:
  1. Navigate to AI Search `/search`.
  2. Verify welcome message.
- **Expected Result**: Welcome message is displayed and session ID is initialized.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Chrome

### SCENARIO-10: Basic Property Query
- **Actor**: Buyer
- **Steps**:
  1. Enter "Show me 3BHK flats in Bandra under 3 Crores."
  2. Send message.
- **Expected Result**: Agent returns a list of matching properties with a conversational response.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Firefox

### SCENARIO-11: Follow-up Query
- **Actor**: Buyer
- **Steps**:
  1. Complete SCENARIO-10.
  2. Send "Do any of these have a sea view?"
- **Expected Result**: Agent understands context and filters the previous list.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Chrome

### SCENARIO-12: Off-topic Query Rejection
- **Actor**: Buyer
- **Steps**:
  1. Send "What's the weather in Mumbai?"
- **Expected Result**: Agent politely steers conversation back to real estate.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Chrome

### SCENARIO-13: Property Qualification Trigger
- **Actor**: Buyer
- **Steps**:
  1. Send "I want to buy the first property."
- **Expected Result**: Lead Qualification Agent triggers, asking for budget and timeline.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Mobile

### SCENARIO-14: Schedule Visit via Chat
- **Actor**: Buyer
- **Steps**:
  1. Ask "Can I schedule a visit for property X tomorrow?"
- **Expected Result**: CRM Agent books the visit and confirms the time.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Chrome

### SCENARIO-15: Multi-agent Handoff
- **Actor**: Buyer
- **Steps**:
  1. Ask for recommendations, then ask to book a visit.
- **Expected Result**: Seamless handoff between Recommendation Agent and CRM Agent.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Chrome

### SCENARIO-16: Empty Search Results
- **Actor**: Buyer
- **Steps**:
  1. Search for an impossible criteria (e.g., "10BHK in Colaba for 10 Lakhs").
- **Expected Result**: Agent gracefully states no properties match and suggests alternatives.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Firefox

## Property Catalog & Detail

### SCENARIO-17: Property Listing Display
- **Actor**: Buyer
- **Steps**:
  1. Navigate to `/properties`.
- **Expected Result**: Grid of properties displays correctly with images and summary details.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Chrome

### SCENARIO-18: Filtering Properties
- **Actor**: Buyer
- **Steps**:
  1. Apply filter: City="Mumbai", Type="Apartment".
- **Expected Result**: Only matching properties are displayed.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Chrome

### SCENARIO-19: Property Detail View
- **Actor**: Buyer
- **Steps**:
  1. Click on a property card.
- **Expected Result**: Full property details (amenities, location, price, images) load successfully.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Mobile

### SCENARIO-20: Save Property
- **Actor**: Buyer
- **Steps**:
  1. On Property Detail, click "Save".
- **Expected Result**: Property is added to user's saved list in Dashboard.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Chrome

### SCENARIO-21: Manual Schedule Visit from Detail Page
- **Actor**: Buyer
- **Steps**:
  1. Click "Schedule Visit" on property page.
  2. Select date/time and submit.
- **Expected Result**: Visit request submitted, confirmation shown.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Firefox

## Session Resumption & Memory

### SCENARIO-22: View Chat History
- **Actor**: Buyer
- **Steps**:
  1. Navigate to `/history`.
- **Expected Result**: Past chat sessions are listed.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Chrome

### SCENARIO-23: Resume Previous Session
- **Actor**: Buyer
- **Steps**:
  1. Click "Resume" on a past session.
- **Expected Result**: Navigates to `/search` with chat history loaded; "Session Resumed" banner visible.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Chrome

### SCENARIO-24: Agent Remembers Preferences
- **Actor**: Buyer
- **Steps**:
  1. Resume a session where user stated "I have 2 kids."
  2. Ask "What amenities do these properties have?"
- **Expected Result**: Agent highlights kid-friendly amenities (play area, schools nearby).
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Chrome

### SCENARIO-25: Memory Injection on New Session
- **Actor**: Buyer
- **Steps**:
  1. Start a new session.
  2. Check if agent brings up past known preferences (e.g., location preference).
- **Expected Result**: Agent acknowledges known preferences subtly.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Firefox

### SCENARIO-26: Clear Session History
- **Actor**: Buyer
- **Steps**:
  1. Click "Clear Chat" in the AI search UI.
- **Expected Result**: Chat UI is cleared, new session ID generated.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Chrome

## User Preference Management

### SCENARIO-27: View Preferences
- **Actor**: Buyer
- **Steps**:
  1. Navigate to Dashboard -> Preferences.
- **Expected Result**: Form shows current preferences (budget, locations, type).
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Chrome

### SCENARIO-28: Update Preferences Form
- **Actor**: Buyer
- **Steps**:
  1. Change budget from 1Cr to 2Cr.
  2. Save.
- **Expected Result**: Preferences update successfully, toast notification appears.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Chrome

### SCENARIO-29: AI Updates Preferences
- **Actor**: Buyer
- **Steps**:
  1. Tell AI "My budget is actually 3 Crores."
  2. Check Dashboard -> Preferences.
- **Expected Result**: Budget is automatically updated to 3Cr by the memory system.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Chrome

### SCENARIO-30: Preference Validation
- **Actor**: Buyer
- **Steps**:
  1. Enter negative number for budget in form.
- **Expected Result**: Form validation prevents submission.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Firefox

## CRM Lead Dashboard

### SCENARIO-31: Dashboard Load for Broker
- **Actor**: Broker
- **Steps**:
  1. Login as Broker.
  2. Navigate to `/crm/leads`.
- **Expected Result**: Pipeline view with leads categorized by status loads.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Chrome

### SCENARIO-32: View Lead Statistics
- **Actor**: Broker
- **Steps**:
  1. View top stat cards on CRM Dashboard.
- **Expected Result**: Displays correct count for New, Hot, and Qualified leads.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Chrome

### SCENARIO-33: Filter Leads by Status
- **Actor**: Broker
- **Steps**:
  1. Click "HOT" filter.
- **Expected Result**: Only leads with HOT tier are shown.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Mobile

### SCENARIO-34: Search Lead by Name
- **Actor**: Broker
- **Steps**:
  1. Type lead name in search bar.
- **Expected Result**: Table filters in real-time to match lead name.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Chrome

### SCENARIO-35: Pagination on Leads Table
- **Actor**: Broker
- **Steps**:
  1. Click "Next" on table pagination.
- **Expected Result**: Page 2 of leads loads successfully.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Firefox

### SCENARIO-36: Unauthorized Access to CRM
- **Actor**: Buyer
- **Steps**:
  1. Attempt to access `/crm/leads`.
- **Expected Result**: Redirected with 403 Forbidden / Unauthorized message.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Chrome

## Lead Detail & FSM Transitions

### SCENARIO-37: View Lead Detail
- **Actor**: Broker
- **Steps**:
  1. Click a lead row in CRM Dashboard.
- **Expected Result**: Navigates to Lead Detail page showing timeline, notes, and profile.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Chrome

### SCENARIO-38: Advance Lead Status (NEW -> QUALIFIED)
- **Actor**: Broker
- **Steps**:
  1. Click "Mark as Qualified".
- **Expected Result**: Status updates; transition recorded in timeline.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Chrome

### SCENARIO-39: Attempt Invalid Transition
- **Actor**: Broker
- **Steps**:
  1. Attempt to mark a "NEW" lead directly as "CLOSED_WON" (if UI allows).
- **Expected Result**: Backend returns 400 Bad Request due to invalid FSM transition.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Chrome

### SCENARIO-40: Add Manual Note to Lead
- **Actor**: Broker
- **Steps**:
  1. Enter note text in "Add Note" section and submit.
- **Expected Result**: Note appears in lead's timeline.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Chrome

### SCENARIO-41: Close Lead (Lost)
- **Actor**: Broker
- **Steps**:
  1. Transition lead to CLOSED_LOST.
  2. Enter required reason.
- **Expected Result**: Lead marked as lost, reason saved in DB.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Firefox

## Follow-Up Task Management

### SCENARIO-42: View Pending Follow-ups
- **Actor**: Broker
- **Steps**:
  1. Open Lead Detail page.
- **Expected Result**: "Follow-ups" panel shows pending tasks.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Chrome

### SCENARIO-43: Add New Follow-up
- **Actor**: Broker
- **Steps**:
  1. Click "Add Follow-up", set date/time and description, submit.
- **Expected Result**: Task added to list.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Chrome

### SCENARIO-44: Mark Follow-up Complete
- **Actor**: Broker
- **Steps**:
  1. Check the box next to a pending follow-up.
- **Expected Result**: Task moves to completed state.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Chrome

### SCENARIO-45: Overdue Follow-up Indicator
- **Actor**: Broker
- **Steps**:
  1. View a lead with an overdue task.
- **Expected Result**: Task is visually highlighted in red.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Mobile

## Site Visit Scheduling

### SCENARIO-46: Broker Schedules Visit
- **Actor**: Broker
- **Steps**:
  1. On Lead Detail, click "Schedule Visit".
  2. Select property, date, time.
- **Expected Result**: Visit scheduled and added to timeline.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Chrome

### SCENARIO-47: Complete Site Visit
- **Actor**: Broker
- **Steps**:
  1. Mark a scheduled site visit as "Completed".
- **Expected Result**: Visit status updates, lead advances to VISITED if applicable.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Chrome

### SCENARIO-48: Cancel Site Visit
- **Actor**: Broker
- **Steps**:
  1. Mark site visit as "Cancelled".
- **Expected Result**: Status updates; no FSM advancement.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Firefox

### SCENARIO-49: Concurrent Visit Booking Prevention
- **Actor**: Broker
- **Steps**:
  1. Try to book a visit for a property at a time that's already booked by the same agent.
- **Expected Result**: Backend validation rejects the request (if implemented).
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Chrome

## Edge Cases & Error Handling

### SCENARIO-50: Agent Service Timeout
- **Actor**: Buyer
- **Steps**:
  1. Send chat message while an agent Docker container is stopped.
- **Expected Result**: Orchestrator retries, then returns graceful fallback message.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Chrome

### SCENARIO-51: Invalid Token Expiry
- **Actor**: Buyer
- **Steps**:
  1. Manipulate JWT in local storage to be expired.
  2. Attempt API request.
- **Expected Result**: Request fails with 401; frontend redirects to login.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Chrome

### SCENARIO-52: Token Refresh Flow
- **Actor**: Buyer
- **Steps**:
  1. Wait for access token to expire while keeping refresh token valid.
  2. Navigate dashboard.
- **Expected Result**: Axios interceptor silently refreshes token, navigation succeeds.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Firefox

### SCENARIO-53: Rate Limiting
- **Actor**: Buyer
- **Steps**:
  1. Send 50 chat messages within 10 seconds (via script).
- **Expected Result**: 429 Too Many Requests response returned.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Automated

### SCENARIO-54: Database Connection Failure
- **Actor**: Admin
- **Steps**:
  1. Stop PostgreSQL container.
  2. Attempt to load properties.
- **Expected Result**: API returns 500 Internal Server Error; frontend shows a generic error toast.
- **Actual Result**: 
- **Status**: TBD
- **Tested On**: Chrome
