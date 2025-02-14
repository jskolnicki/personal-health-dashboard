from flask import render_template, jsonify, request
from datetime import datetime
import json
import os
from app.blueprints.journal import journal_bp
from app.blueprints.journal.config import QUICK_TAGS, DEFAULT_SCORES
from app import db
from database.models import DailyLogs
from pathlib import Path

def save_to_markdown(date_obj, content, tags):
    """Save journal entry to markdown file in Documents/PersonalDashboard/Journal"""
    # Get user's Documents folder path
    documents_path = Path.home() / "Documents"
    
    # Create base directory for all dashboard files
    dashboard_path = documents_path / "PersonalDashboard"
    journal_path = dashboard_path / "Journal"
    
    # Create year-based subdirectory
    year_path = journal_path / str(date_obj.year)
    year_path.mkdir(parents=True, exist_ok=True)
    
    # Create markdown content
    markdown_content = f"# {date_obj.strftime('%Y-%m-%d')}\n\n"
    markdown_content += content + "\n\n"
    
    if any(tags.values()):
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
def daily(date_str=None):
    if date_str:
        try:
            current_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            current_date = datetime.today().date()
    else:
        current_date = datetime.today().date()
    
    return render_template(
        'daily.html',  # Update template path
        current_date=current_date.strftime('%Y-%m-%d'),
        quick_tags=QUICK_TAGS,      # Use from config
        default_scores=DEFAULT_SCORES  # Add this
    )

@journal_bp.route('/journal/entry/<date_str>')
def get_entry(date_str):
    try:
        entry_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        entry = DailyLogs.query.filter_by(date=entry_date).first()
        
        if entry:
            return jsonify({
                'content': entry.content,
                'summary': entry.summary,
                'day_score': entry.day_score,
                'productivity_score': entry.productivity_score,
                'boolean_tags': json.loads(entry.boolean_tags) if entry.boolean_tags else [],
                'location_tags': json.loads(entry.location_tags) if entry.location_tags else [],
                'people_tags': json.loads(entry.people_tags) if entry.people_tags else [],
                'custom_tags': json.loads(entry.custom_tags) if entry.custom_tags else []
            })
        return jsonify({})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@journal_bp.route('/journal/save', methods=['POST'])
def save_entry():
    try:
        data = request.json
        entry_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        
        # Convert tag lists to JSON strings
        boolean_tags = json.dumps(data.get('boolean_tags', []))
        location_tags = json.dumps(data.get('location_tags', []))
        people_tags = json.dumps(data.get('people_tags', []))
        custom_tags = json.dumps(data.get('custom_tags', []))
        
        # Check for existing entry
        entry = DailyLogs.query.filter_by(date=entry_date).first()
        
        if entry:
            entry.content = data['content']
            entry.summary = data.get('summary')
            entry.day_score = data.get('day_score')
            entry.productivity_score = data.get('productivity_score')
            entry.boolean_tags = boolean_tags
            entry.location_tags = location_tags
            entry.people_tags = people_tags
            entry.custom_tags = custom_tags
        else:
            entry = DailyLogs(
                date=entry_date,
                content=data['content'],
                summary=data.get('summary'),
                day_score=data.get('day_score'),
                productivity_score=data.get('productivity_score'),
                boolean_tags=boolean_tags,
                location_tags=location_tags,
                people_tags=people_tags,
                custom_tags=custom_tags
            )
            db.session.add(entry)
        
        db.session.commit()
        
        # Save to markdown file
        save_to_markdown(entry_date, data['content'], {
            'boolean_tags': boolean_tags,
            'location_tags': location_tags,
            'people_tags': people_tags,
            'custom_tags': custom_tags
        })
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500