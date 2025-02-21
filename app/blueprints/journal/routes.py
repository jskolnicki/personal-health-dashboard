from flask import render_template, jsonify, request
from datetime import datetime
import json
from flask_login import login_required, current_user
from app.blueprints.journal import journal_bp
from app.blueprints.journal.config import QUICK_TAGS, DEFAULT_SCORES
from app import db
from database.models import DailyLogs, Reflections
from pathlib import Path
from sqlalchemy import desc

def save_to_markdown(date_obj, content, tags=None, is_reflection=False):
    """Save entry to markdown file in Documents/PersonalDashboard/{Journal|Reflections}"""
    # Get user's Documents folder path
    documents_path = Path.home() / "Documents"
    
    # Create base directory for all dashboard files
    dashboard_path = documents_path / "PersonalDashboard"
    base_path = dashboard_path / ("Reflections" if is_reflection else "Journal")
    
    # Create year-based subdirectory
    year_path = base_path / str(date_obj.year)
    year_path.mkdir(parents=True, exist_ok=True)
    
    # Create markdown content
    markdown_content = f"# {date_obj.strftime('%Y-%m-%d')}\n\n"
    markdown_content += content + "\n\n"
    
    if tags and any(tags.values()):
        markdown_content += "\n## Tags\n"
        for tag_type, tag_list in tags.items():
            if tag_list:
                tag_list = json.loads(tag_list) if isinstance(tag_list, str) else tag_list
                if tag_list:
                    markdown_content += f"\n### {tag_type.replace('_', ' ').title()}\n"
                    markdown_content += ", ".join(tag_list) + "\n"
    
    # Create the file using pathlib
    file_path = year_path / f"{date_obj.strftime('%Y-%m-%d')}.md"
    file_path.write_text(markdown_content, encoding='utf-8')

@journal_bp.route('/journal')
@journal_bp.route('/journal/<date_str>')
@login_required
def load_daily_page(date_str=None):
    if date_str:
        try:
            current_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            current_date = datetime.today().date()
    else:
        current_date = datetime.today().date()
    
    return render_template(
        'daily.html',
        current_date=current_date.strftime('%Y-%m-%d'),
        quick_tags=QUICK_TAGS,
        default_scores=DEFAULT_SCORES
    )

@journal_bp.route('/reflections')
@journal_bp.route('/reflections/<date_str>')
@login_required
def load_reflections_page(date_str=None):
    if date_str:
        try:
            current_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            current_date = datetime.today().date()
    else:
        current_date = datetime.today().date()
    
    return render_template(
        'reflections.html',
        current_date=current_date.strftime('%Y-%m-%d')
    )

@journal_bp.route('/journal/entry/<date_str>')
@login_required
def get_entry(date_str):
    try:
        entry_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        entry = DailyLogs.query.filter_by(
            date=entry_date,
            user_id=current_user.user_id
        ).first()
        
        if entry:
            return jsonify({
                'content': entry.content,
                'summary': entry.summary,
                'day_score': entry.day_score,
                'productivity_score': entry.productivity_score,
                'activities': json.loads(entry.activities) if entry.activities else [],
                'social': json.loads(entry.social) if entry.social else [],
                'education': json.loads(entry.education) if entry.education else [],
                'mood': json.loads(entry.mood) if entry.mood else [],
                'custom_tags': json.loads(entry.custom_tags) if entry.custom_tags else []
            })
        return jsonify({})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@journal_bp.route('/reflections/entry/<date_str>')
@login_required
def get_reflection(date_str):
    try:
        reflection_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        reflection = Reflections.query.filter_by(
            date=reflection_date,
            user_id=current_user.user_id
        ).first()
        
        if reflection:
            return jsonify({
                'content': reflection.content,
                'themes': json.loads(reflection.themes) if reflection.themes else []
            })
        return jsonify({})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@journal_bp.route('/reflections/navigate/<date_str>/<direction>')
@login_required
def navigate_reflections(date_str, direction):
    try:
        current_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        query = Reflections.query.filter_by(user_id=current_user.user_id)
        
        if direction == 'prev':
            reflection = query\
                .filter(Reflections.date < current_date)\
                .order_by(desc(Reflections.date))\
                .first()
        else:  # next
            reflection = query\
                .filter(Reflections.date > current_date)\
                .order_by(Reflections.date)\
                .first()
        
        if reflection:
            return jsonify({
                'date': reflection.date.strftime('%Y-%m-%d'),
                'content': reflection.content,
                'themes': json.loads(reflection.themes) if reflection.themes else [],
                'status': 'success'
            })
        return jsonify({
            'status': 'no_entries',
            'message': 'No earlier reflections found' if direction == 'prev' else 'No later reflections found'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@journal_bp.route('/journal/save', methods=['POST'])
@login_required
def save_entry():
    try:
        data = request.json
        entry_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        
        # Convert tag lists to JSON strings
        activities = json.dumps(data.get('activities', []))
        social = json.dumps(data.get('social', []))
        education = json.dumps(data.get('education', []))
        mood = json.dumps(data.get('mood', []))
        custom_tags = json.dumps(data.get('custom_tags', []))
        
        # Check for existing entry
        entry = DailyLogs.query.filter_by(
            date=entry_date,
            user_id=current_user.user_id
        ).first()
        
        if entry:
            entry.content = data['content']
            entry.summary = data.get('summary')
            entry.day_score = data.get('day_score')
            entry.productivity_score = data.get('productivity_score')
            entry.activities = activities
            entry.social = social
            entry.education = education
            entry.mood = mood
            entry.custom_tags = custom_tags
        else:
            entry = DailyLogs(
                user_id=current_user.user_id,
                date=entry_date,
                content=data['content'],
                summary=data.get('summary'),
                day_score=data.get('day_score'),
                productivity_score=data.get('productivity_score'),
                activities=activities,
                social=social,
                education=education,
                mood=mood,
                custom_tags=custom_tags
            )
            db.session.add(entry)
        
        db.session.commit()
        
        # Save to markdown file
        save_to_markdown(entry_date, data['content'], {
            'activities': activities,
            'social': social,
            'education': education,
            'mood': mood,
            'custom_tags': custom_tags
        })
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@journal_bp.route('/reflections/save', methods=['POST'])
@login_required
def save_reflection():
    try:
        data = request.json
        reflection_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        
        # Convert themes to JSON string
        themes = json.dumps(data.get('themes', []))
        
        # Check for existing reflection
        reflection = Reflections.query.filter_by(
            date=reflection_date,
            user_id=current_user.user_id
        ).first()
        
        if reflection:
            reflection.content = data['content']
            reflection.themes = themes
        else:
            reflection = Reflections(
                user_id=current_user.user_id,
                date=reflection_date,
                content=data['content'],
                themes=themes
            )
            db.session.add(reflection)
        
        db.session.commit()
        
        # Save to markdown file
        save_to_markdown(
            reflection_date,
            data['content'],
            {'themes': themes},
            is_reflection=True
        )
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500