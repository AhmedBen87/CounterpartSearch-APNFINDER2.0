from flask import render_template, request, jsonify
from sqlalchemy import func, or_
from app import app, db
from models import CP, APN
from helpers import get_apn_details

@app.route('/search_suggestions')
def search_suggestions():
    customer = request.args.get('customer')
    carline = request.args.get('carline')
    term = request.args.get('term', '').lower()
    
    query = CP.query.filter(
        func.lower(CP.Client_ID_1) == func.lower(customer),
        func.lower(CP.PRJ_ID1) == func.lower(carline),
        func.lower(CP.CP).contains(func.lower(term))
    ).limit(10)
    
    suggestions = [{'cp': cp.CP} for cp in query.all()]
    return jsonify(suggestions)

@app.route('/')
def index():
    """Render the landing page with customer selection"""
    # Get unique customers (Client_ID_1 values)
    customers = db.session.query(CP.Client_ID_1).distinct().order_by(CP.Client_ID_1).all()
    customers = [c[0] for c in customers if c[0]]  # Extract values and filter out None/empty values
    
    return render_template('index.html', customers=customers)

@app.route('/get_carlines/<customer>')
def get_carlines(customer):
    """Get car lines for a specific customer"""
    carlines = db.session.query(CP.PRJ_ID1)\
        .filter(CP.Client_ID_1 == customer)\
        .distinct()\
        .order_by(CP.PRJ_ID1)\
        .all()
    
    carlines = [c[0] for c in carlines if c[0]]  # Extract values and filter out None/empty values
    
    return jsonify(carlines)

@app.route('/search')
def search():
    """Search for a CP and return the results"""
    customer = request.args.get('customer')
    carline = request.args.get('carline')
    cp_name = request.args.get('cp_name')
    
    if not all([customer, carline, cp_name]):
        return render_template('results.html', error="All search parameters are required.")
    
    # Search for the CP with matching criteria
    cp_results = CP.query.filter(
        func.lower(CP.Client_ID_1) == func.lower(customer),
        func.lower(CP.PRJ_ID1) == func.lower(carline),
        func.lower(CP.CP).contains(func.lower(cp_name))
    ).all()
    
    if not cp_results:
    
    if not cp_result:
        return render_template('results.html', error="No matching CP found.")
    
    # Gather the APN details for this CP
    apn_details = get_apn_details(cp_result)
    
    return render_template(
        'results.html',
        cp=cp_result,
        apn_details=apn_details,
        error=None
    )

@app.errorhandler(404)
def page_not_found(e):
    return render_template('index.html', error="Page not found."), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('index.html', error="An internal server error occurred."), 500
