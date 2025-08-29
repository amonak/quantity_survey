"""
Real-time Collaboration Module
Provides WebSocket-based real-time collaboration features
"""

import melon
from melon import _
from melon.utils import now_datetime, cstr
from melon.realtime import publish_realtime
import json
from typing import Dict, List, Optional


@melon.whitelist()
def join_collaboration_session(doctype: str, docname: str) -> Dict:
	"""
	Join a real-time collaboration session for a document
	"""
	try:
		# Verify user has access to document
		if not melon.has_permission(doctype, "read", docname):
			return {'success': False, 'message': _('Access denied')}
		
		# Get or create collaboration session
		session = get_collaboration_session(doctype, docname)
		
		# Add user to session
		user_info = {
			'user': melon.session.user,
			'full_name': melon.user.full_name(),
			'image': melon.user.user_image(),
			'joined_at': now_datetime(),
			'cursor_position': None,
			'selected_field': None,
			'status': 'active'
		}
		
		# Update active users
		if not session.get('active_users'):
			session['active_users'] = []
		
		# Remove user if already exists, then add updated info
		session['active_users'] = [u for u in session['active_users'] if u['user'] != melon.session.user]
		session['active_users'].append(user_info)
		
		# Save session
		save_collaboration_session(doctype, docname, session)
		
		# Notify other users
		publish_realtime(
			event='collaboration_user_joined',
			message={
				'doctype': doctype,
				'docname': docname,
				'user_info': user_info,
				'active_users': session['active_users']
			},
			room=get_room_name(doctype, docname),
			after_commit=True
		)
		
		return {
			'success': True,
			'session_id': session.get('session_id'),
			'active_users': session['active_users'],
			'message': _('Joined collaboration session')
		}
		
	except Exception as e:
		melon.log_error(f"Collaboration join error: {str(e)}", "Real-time Collaboration")
		return {'success': False, 'message': str(e)}

@melon.whitelist()
def leave_collaboration_session(doctype: str, docname: str) -> Dict:
    """
    Leave a real-time collaboration session
    """
    try:
        session = get_collaboration_session(doctype, docname)
        
        if session and session.get('active_users'):
            # Remove user from active users
            session['active_users'] = [u for u in session['active_users'] if u['user'] != melon.session.user]
            
            # Save session
            save_collaboration_session(doctype, docname, session)
            
            # Notify other users
            publish_realtime(
                event='collaboration_user_left',
                message={
                    'doctype': doctype,
                    'docname': docname,
                    'user': melon.session.user,
                    'active_users': session['active_users']
                },
                room=get_room_name(doctype, docname),
                after_commit=True
            )
        
        return {'success': True, 'message': 'Left collaboration session'}
        
    except Exception as e:
        melon.log_error(f"Collaboration leave error: {str(e)}", "Real-time Collaboration")
        return {'success': False, 'message': str(e)}

@melon.whitelist()
def broadcast_field_change(doctype: str, docname: str, fieldname: str, value: any, field_type: str = None) -> Dict:
    """
    Broadcast field changes to other collaborators
    """
    try:
        # Verify user has write permission
        if not melon.has_permission(doctype, "write", docname):
            return {'success': False, 'message': 'Write access denied'}
        
        # Get collaboration session
        session = get_collaboration_session(doctype, docname)
        
        if not session or not session.get('active_users'):
            return {'success': True, 'message': 'No active collaboration session'}
        
        # Create change record
        change_info = {
            'user': melon.session.user,
            'full_name': melon.user.full_name(),
            'timestamp': now_datetime(),
            'fieldname': fieldname,
            'value': value,
            'field_type': field_type,
            'change_id': melon.generate_hash(length=12)
        }
        
        # Add to session history
        if not session.get('change_history'):
            session['change_history'] = []
        
        session['change_history'].append(change_info)
        
        # Keep only last 100 changes
        if len(session['change_history']) > 100:
            session['change_history'] = session['change_history'][-100:]
        
        # Save session
        save_collaboration_session(doctype, docname, session)
        
        # Broadcast to other users
        publish_realtime(
            event='collaboration_field_changed',
            message={
                'doctype': doctype,
                'docname': docname,
                'change_info': change_info
            },
            room=get_room_name(doctype, docname),
            after_commit=True
        )
        
        return {'success': True, 'change_id': change_info['change_id']}
        
    except Exception as e:
        melon.log_error(f"Field change broadcast error: {str(e)}", "Real-time Collaboration")
        return {'success': False, 'message': str(e)}

@melon.whitelist()
def broadcast_cursor_position(doctype: str, docname: str, fieldname: str, position: int) -> Dict:
    """
    Broadcast cursor position to other collaborators
    """
    try:
        session = get_collaboration_session(doctype, docname)
        
        if session and session.get('active_users'):
            # Update user cursor position
            for user in session['active_users']:
                if user['user'] == melon.session.user:
                    user['selected_field'] = fieldname
                    user['cursor_position'] = position
                    user['last_activity'] = now_datetime()
                    break
            
            # Save session
            save_collaboration_session(doctype, docname, session)
            
            # Broadcast cursor position
            publish_realtime(
                event='collaboration_cursor_moved',
                message={
                    'doctype': doctype,
                    'docname': docname,
                    'user': melon.session.user,
                    'fieldname': fieldname,
                    'position': position
                },
                room=get_room_name(doctype, docname),
                after_commit=True
            )
        
        return {'success': True}
        
    except Exception as e:
        melon.log_error(f"Cursor broadcast error: {str(e)}", "Real-time Collaboration")
        return {'success': False, 'message': str(e)}

@melon.whitelist()
def send_collaboration_message(doctype: str, docname: str, message: str, message_type: str = 'text') -> Dict:
    """
    Send a message in collaboration session
    """
    try:
        session = get_collaboration_session(doctype, docname)
        
        if not session:
            return {'success': False, 'message': 'No active collaboration session'}
        
        # Create message record
        message_info = {
            'user': melon.session.user,
            'full_name': melon.user.full_name(),
            'image': melon.user.user_image(),
            'timestamp': now_datetime(),
            'message': message,
            'message_type': message_type,
            'message_id': melon.generate_hash(length=12)
        }
        
        # Add to session messages
        if not session.get('messages'):
            session['messages'] = []
        
        session['messages'].append(message_info)
        
        # Keep only last 50 messages
        if len(session['messages']) > 50:
            session['messages'] = session['messages'][-50:]
        
        # Save session
        save_collaboration_session(doctype, docname, session)
        
        # Broadcast message
        publish_realtime(
            event='collaboration_message',
            message={
                'doctype': doctype,
                'docname': docname,
                'message_info': message_info
            },
            room=get_room_name(doctype, docname),
            after_commit=True
        )
        
        return {'success': True, 'message_id': message_info['message_id']}
        
    except Exception as e:
        melon.log_error(f"Collaboration message error: {str(e)}", "Real-time Collaboration")
        return {'success': False, 'message': str(e)}

@melon.whitelist()
def get_collaboration_status(doctype: str, docname: str) -> Dict:
    """
    Get current collaboration status for a document
    """
    try:
        session = get_collaboration_session(doctype, docname)
        
        if not session:
            return {
                'active_users': [],
                'recent_changes': [],
                'messages': [],
                'is_collaborative': False
            }
        
        # Clean up inactive users (older than 5 minutes)
        if session.get('active_users'):
            import datetime
            current_time = now_datetime()
            active_users = []
            
            for user in session['active_users']:
                last_activity = user.get('last_activity', user.get('joined_at'))
                if isinstance(last_activity, str):
                    last_activity = melon.utils.get_datetime(last_activity)
                
                # Keep user active if last activity was within 5 minutes
                if (current_time - last_activity).total_seconds() < 300:
                    active_users.append(user)
            
            session['active_users'] = active_users
            save_collaboration_session(doctype, docname, session)
        
        return {
            'active_users': session.get('active_users', []),
            'recent_changes': session.get('change_history', [])[-10:],  # Last 10 changes
            'messages': session.get('messages', [])[-20:],  # Last 20 messages
            'is_collaborative': len(session.get('active_users', [])) > 1,
            'session_id': session.get('session_id')
        }
        
    except Exception as e:
        melon.log_error(f"Collaboration status error: {str(e)}", "Real-time Collaboration")
        return {
            'active_users': [],
            'recent_changes': [],
            'messages': [],
            'is_collaborative': False,
            'error': str(e)
        }

def get_collaboration_session(doctype: str, docname: str) -> Dict:
    """
    Get collaboration session from cache or database
    """
    session_key = get_session_key(doctype, docname)
    
    # Try to get from cache first
    session = melon.cache().get_value(session_key)
    
    if not session:
        # Try to get from database
        try:
            session_doc = melon.get_doc('Collaboration Session', {
                'reference_doctype': doctype,
                'reference_name': docname
            })
            session = json.loads(session_doc.session_data or '{}')
        except melon.DoesNotExistError:
            # Create new session
            session = {
                'session_id': melon.generate_hash(length=20),
                'created_at': now_datetime(),
                'active_users': [],
                'change_history': [],
                'messages': []
            }
    
    return session

def save_collaboration_session(doctype: str, docname: str, session: Dict):
    """
    Save collaboration session to cache and database
    """
    session_key = get_session_key(doctype, docname)
    
    # Save to cache (expires in 1 hour)
    melon.cache().set_value(session_key, session, expires_in_sec=3600)
    
    # Save to database
    try:
        session_doc = melon.get_doc('Collaboration Session', {
            'reference_doctype': doctype,
            'reference_name': docname
        })
    except melon.DoesNotExistError:
        session_doc = melon.new_doc('Collaboration Session')
        session_doc.reference_doctype = doctype
        session_doc.reference_name = docname
        session_doc.session_id = session.get('session_id')
    
    session_doc.session_data = json.dumps(session, default=str)
    session_doc.last_activity = now_datetime()
    session_doc.active_users_count = len(session.get('active_users', []))
    
    session_doc.save(ignore_permissions=True)

def get_session_key(doctype: str, docname: str) -> str:
    """
    Generate session key for collaboration
    """
    return f"collaboration_session:{doctype}:{docname}"

def get_room_name(doctype: str, docname: str) -> str:
    """
    Generate room name for WebSocket communication
    """
    return f"collaboration:{doctype}:{docname}"

@melon.whitelist()
def resolve_conflict(doctype: str, docname: str, fieldname: str, resolution: str, winning_value: any) -> Dict:
    """
    Resolve field conflict in collaborative editing
    """
    try:
        # Verify user has write permission
        if not melon.has_permission(doctype, "write", docname):
            return {'success': False, 'message': 'Write access denied'}
        
        # Update document with winning value
        doc = melon.get_doc(doctype, docname)
        setattr(doc, fieldname, winning_value)
        doc.save(ignore_permissions=True)
        
        # Broadcast conflict resolution
        publish_realtime(
            event='collaboration_conflict_resolved',
            message={
                'doctype': doctype,
                'docname': docname,
                'fieldname': fieldname,
                'resolution': resolution,
                'winning_value': winning_value,
                'resolved_by': melon.session.user,
                'resolved_at': now_datetime()
            },
            room=get_room_name(doctype, docname),
            after_commit=True
        )
        
        return {'success': True, 'message': 'Conflict resolved successfully'}
        
    except Exception as e:
        melon.log_error(f"Conflict resolution error: {str(e)}", "Real-time Collaboration")
        return {'success': False, 'message': str(e)}

@melon.whitelist()
def get_document_locks(doctype: str, docname: str) -> Dict:
    """
    Get field-level locks for collaborative editing
    """
    try:
        session = get_collaboration_session(doctype, docname)
        locks = {}
        
        if session and session.get('active_users'):
            for user in session['active_users']:
                if user.get('selected_field') and user['user'] != melon.session.user:
                    locks[user['selected_field']] = {
                        'user': user['user'],
                        'full_name': user['full_name'],
                        'locked_at': user.get('last_activity'),
                        'cursor_position': user.get('cursor_position')
                    }
        
        return {'success': True, 'locks': locks}
        
    except Exception as e:
        melon.log_error(f"Document locks error: {str(e)}", "Real-time Collaboration")
        return {'success': False, 'message': str(e)}

@melon.whitelist()
def cleanup_inactive_sessions():
    """
    Cleanup inactive collaboration sessions (called by scheduler)
    """
    try:
        # Get sessions older than 1 hour with no activity
        old_sessions = melon.get_all('Collaboration Session',
            filters={
                'last_activity': ['<', melon.utils.add_to_date(now_datetime(), hours=-1)]
            },
            fields=['name']
        )
        
        for session in old_sessions:
            melon.delete_doc('Collaboration Session', session.name, ignore_permissions=True)
        
        melon.db.commit()
        
        if old_sessions:
            melon.logger().info(f"Cleaned up {len(old_sessions)} inactive collaboration sessions")
        
    except Exception as e:
        melon.log_error(f"Session cleanup error: {str(e)}", "Real-time Collaboration")
