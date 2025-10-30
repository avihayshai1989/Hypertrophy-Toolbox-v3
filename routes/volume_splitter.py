from flask import Blueprint, render_template, jsonify, request, send_file
from utils.database import get_db_connection, DatabaseHandler
from utils.volume_export import export_volume_plan
from utils.volume_ai import generate_volume_suggestions
from openpyxl import Workbook
from io import BytesIO
import datetime

volume_splitter_bp = Blueprint('volume_splitter', __name__)

MUSCLE_GROUPS = [
    'Abdominals', 'Biceps', 'Calves', 'Chest', 'Forearms', 
    'Front-Shoulder', 'Glutes', 'Hamstrings', 'Hip-Adductors',
    'Latissimus-Dorsi', 'Lower Back', 'Middle-Shoulder', 
    'Middle-Traps', 'Neck', 'Obliques', 'Quadriceps',
    'Rear-Shoulder', 'Traps', 'Triceps'
]

RECOMMENDED_RANGES = {
    muscle: {'min': 12, 'max': 20} for muscle in MUSCLE_GROUPS
}

@volume_splitter_bp.route('/volume_splitter')
def volume_splitter():
    return render_template('volume_splitter.html', 
                         muscle_groups=MUSCLE_GROUPS,
                         recommended_ranges=RECOMMENDED_RANGES)

@volume_splitter_bp.route('/api/calculate_volume', methods=['POST'])
def calculate_volume():
    data = request.get_json()
    training_days = data.get('training_days', 3)
    volumes = data.get('volumes', {})
    
    results = {}
    for muscle, weekly_sets in volumes.items():
        sets_per_session = round(weekly_sets / training_days, 1)
        status = 'optimal'
        
        if weekly_sets < RECOMMENDED_RANGES[muscle]['min']:
            status = 'low'
        elif weekly_sets > RECOMMENDED_RANGES[muscle]['max']:
            status = 'high'
            
        if sets_per_session > 10:
            status = 'excessive'
            
        results[muscle] = {
            'weekly_sets': weekly_sets,
            'sets_per_session': sets_per_session,
            'status': status
        }
    
    # Generate AI suggestions
    suggestions = generate_volume_suggestions(training_days, results)
    
    return jsonify({
        'results': results,
        'suggestions': suggestions
    })

@volume_splitter_bp.route('/api/volume_history')
def get_volume_history():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT vp.id, vp.training_days, vp.created_at,
                   mv.muscle_group, mv.weekly_sets, mv.sets_per_session, mv.status
            FROM volume_plans vp
            JOIN muscle_volumes mv ON vp.id = mv.plan_id
            ORDER BY vp.created_at DESC
            LIMIT 100
        ''')
        history = cursor.fetchall()
        
        # Format the data for frontend
        formatted_history = {}
        for row in history:
            plan_id = row[0]
            if plan_id not in formatted_history:
                formatted_history[plan_id] = {
                    'training_days': row[1],
                    'created_at': row[2],
                    'muscles': {}
                }
            formatted_history[plan_id]['muscles'][row[3]] = {
                'weekly_sets': row[4],
                'sets_per_session': row[5],
                'status': row[6]
            }
        
        return jsonify(formatted_history)
        
    finally:
        conn.close()

@volume_splitter_bp.route('/api/save_volume_plan', methods=['POST'])
def save_volume_plan():
    data = request.get_json()
    plan_id = export_volume_plan(data)
    
    if plan_id:
        return jsonify({'success': True, 'plan_id': plan_id})
    return jsonify({'success': False, 'error': 'Failed to save plan'}), 500 

@volume_splitter_bp.route('/api/volume_plan/<int:plan_id>')
def get_volume_plan(plan_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Get plan details
        cursor.execute('''
            SELECT vp.*, mv.muscle_group, mv.weekly_sets, mv.sets_per_session, mv.status
            FROM volume_plans vp
            JOIN muscle_volumes mv ON vp.id = mv.plan_id
            WHERE vp.id = ?
        ''', (plan_id,))
        
        rows = cursor.fetchall()
        if not rows:
            return jsonify({'error': 'Plan not found'}), 404
            
        plan = {
            'training_days': rows[0][1],
            'created_at': rows[0][2],
            'volumes': {}
        }
        
        for row in rows:
            plan['volumes'][row[3]] = {
                'weekly_sets': row[4],
                'sets_per_session': row[5],
                'status': row[6]
            }
            
        return jsonify(plan)
        
    finally:
        conn.close() 

@volume_splitter_bp.route('/api/export_volume_excel', methods=['POST'])
def export_volume_excel():
    data = request.get_json()
    training_days = data.get('training_days', 3)
    volumes = data.get('volumes', {})
    
    # Create a new workbook and select the active sheet
    wb = Workbook()
    ws = wb.active
    ws.title = "Volume Plan"
    
    # Add headers
    headers = ['Muscle Group', 'Sets per Week', 'Sets per Session']
    for col, header in enumerate(headers, 1):
        ws.cell(row=1, column=col, value=header)
    
    # Add data
    row = 2
    for muscle, weekly_sets in volumes.items():
        sets_per_session = round(weekly_sets / training_days, 1)
        ws.cell(row=row, column=1, value=muscle)
        ws.cell(row=row, column=2, value=weekly_sets)
        ws.cell(row=row, column=3, value=sets_per_session)
        row += 1
    
    # Style the worksheet
    for col in range(1, len(headers) + 1):
        ws.column_dimensions[chr(64 + col)].width = 15
    
    # Create the file
    excel_file = BytesIO()
    wb.save(excel_file)
    excel_file.seek(0)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return send_file(
        excel_file,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'volume_plan_{timestamp}.xlsx'
    ) 