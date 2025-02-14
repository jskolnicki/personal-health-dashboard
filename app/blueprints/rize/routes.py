from flask import Blueprint, render_template, request
from datetime import datetime, time, timedelta
from app import db
from database.models import RizeSessions, SleepData
from flask_login import login_required

rize_bp = Blueprint('rize', __name__, template_folder='templates')

@rize_bp.route('/rize_dashboard', methods=['GET'])
def load_rize_dashboard():
    # Determine date range from query params or default to last 7 days
    local_start_str = request.args.get('start_date', None)
    local_end_str = request.args.get('end_date', None)

    # Default to last 7 days if none provided
    if not local_start_str or not local_end_str:
        today = datetime.utcnow().date()
        default_end = today
        default_start = today - timedelta(days=6)  # last 7 days: inclusive
        local_start_str = local_start_str if local_start_str else default_start.isoformat()
        local_end_str = local_end_str if local_end_str else default_end.isoformat()

    local_start_date = datetime.strptime(local_start_str, "%Y-%m-%d").date()
    local_end_date = datetime.strptime(local_end_str, "%Y-%m-%d").date()

    # Build a list of all days in the range
    dates_needed = [(local_start_date + timedelta(days=i)) for i in range((local_end_date - local_start_date).days + 1)]
    date_strings = [d.isoformat() for d in dates_needed]

    # Get timezone offsets from SleepData
    sleep_data = db.session.query(SleepData).filter(SleepData.date.in_(date_strings)).all()
    offsets_by_date = {s.date: s.timezone_offset for s in sleep_data}

    # For any day without an offset, assume a default offset (e.g., -420)
    # Adjust as needed or raise an error if missing data is not acceptable.
    for d in date_strings:
        if d not in offsets_by_date:
            offsets_by_date[d] = -420  # fallback offset

    # Convert local date boundaries to UTC intervals
    utc_intervals = []
    for d_str in date_strings:
        d = datetime.strptime(d_str, "%Y-%m-%d").date()
        offset_minutes = offsets_by_date[d_str]

        local_day_start = datetime.combine(d, time.min)
        local_day_end = datetime.combine(d, time.max)

        day_start_utc = local_day_start - timedelta(minutes=offset_minutes)
        day_end_utc = local_day_end - timedelta(minutes=offset_minutes)

        utc_intervals.append((day_start_utc, day_end_utc))

    overall_utc_start = min(iv[0] for iv in utc_intervals)
    overall_utc_end = max(iv[1] for iv in utc_intervals)

    # Fetch sessions overlapping the entire UTC range
    sessions = db.session.query(RizeSessions).filter(
        RizeSessions.end_time >= overall_utc_start,
        RizeSessions.start_time <= overall_utc_end
    ).all()

    # Prepare results structures
    # Per day/hour: results[date_str][hour] = total_minutes
    results = {d_str: {h: 0 for h in range(24)} for d_str in date_strings}
    
    # We'll also track totals by hour of day across all selected dates
    hour_of_day_totals = {h: 0 for h in range(24)}

    # We'll also track totals by day of week (Sunday through Saturday)
    # Python's weekday(): Monday=0, Sunday=6, we’ll remap to Sunday=0,...Saturday=6 for clarity.
    day_of_week_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    day_of_week_totals = {day: 0 for day in day_of_week_names}

    # Process each session and accumulate time into results
    for sess in sessions:
        start_utc = sess.start_time
        end_utc = sess.end_time

        for d_str in date_strings:
            offset_minutes = offsets_by_date[d_str]
            d = datetime.strptime(d_str, "%Y-%m-%d").date()

            local_day_start = datetime.combine(d, time.min)
            local_day_end = datetime.combine(d, time.max)

            day_start_utc = local_day_start - timedelta(minutes=offset_minutes)
            day_end_utc = local_day_end - timedelta(minutes=offset_minutes)

            # Overlap in UTC
            overlap_start_utc = max(start_utc, day_start_utc)
            overlap_end_utc = min(end_utc, day_end_utc)

            if overlap_start_utc < overlap_end_utc:
                # Convert overlap to local
                overlap_start_local = overlap_start_utc + timedelta(minutes=offset_minutes)
                overlap_end_local = overlap_end_utc + timedelta(minutes=offset_minutes)

                # Break down by hour within this local day
                # We'll iterate hour by hour
                current = overlap_start_local
                while current < overlap_end_local:
                    hour_bucket = current.hour
                    end_of_hour = current.replace(minute=59, second=59, microsecond=999999)
                    hour_end = min(end_of_hour, overlap_end_local)
                    diff_minutes = (hour_end - current).total_seconds() / 60.0
                    results[d_str][hour_bucket] += diff_minutes
                    hour_of_day_totals[hour_bucket] += diff_minutes
                    current = hour_end + timedelta(microseconds=1)

    # Now accumulate day-of-week totals
    # For each day in results, sum all hours and assign to day_of_week_totals
    for d_str, hours_dict in results.items():
        d = datetime.strptime(d_str, "%Y-%m-%d").date()
        total_minutes_day = sum(hours_dict.values())
        # Python's weekday: Monday=0, Sunday=6
        # We want Sunday=0,... so we do:
        # Sunday=0 means we shift Python’s weekday:
        # Python: Monday=0,...,Sunday=6
        # We can do: day_of_week_index = (weekday+1) % 7 to shift Sunday to 0
        day_index = (d.weekday() + 1) % 7
        day_name = day_of_week_names[day_index]
        day_of_week_totals[day_name] += total_minutes_day

    # Prepare data for charts (hour_of_day_totals and day_of_week_totals)
    # Convert minutes to hours for better readability
    hour_of_day_hours = [hour_of_day_totals[h] / 60.0 for h in range(24)]
    day_of_week_hours = [day_of_week_totals[d] / 60.0 for d in day_of_week_names]

    return render_template('rize_dashboard.html',
                           results=results,
                           start_date=local_start_str,
                           end_date=local_end_str,
                           day_of_week_totals=day_of_week_totals,
                           hour_of_day_totals=hour_of_day_totals,
                           day_of_week_names=day_of_week_names,
                           hour_of_day_hours=hour_of_day_hours,
                           day_of_week_hours=day_of_week_hours)
