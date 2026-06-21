from datetime import date, timedelta
from flask import Blueprint, render_template, request, send_file
from flask_login import login_required

from app.models import Bin, Collection
from app.utils.pdf_generator import generate_report_pdf
from app.ml.predictor import predict_all_bins

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')


def _get_period_range(period):
    """Return (start_date, end_date, label) for the given period string."""
    today = date.today()
    if period == 'weekly':
        start = today - timedelta(days=7)
        label = f'Weekly Report - {start.isoformat()} to {today.isoformat()}'
    elif period == 'monthly':
        start = today - timedelta(days=30)
        label = f'Monthly Report - {start.isoformat()} to {today.isoformat()}'
    else:
        period = 'daily'
        start = today
        label = f'Daily Report - {today.isoformat()}'
    return start, today, label, period


def _build_report_data(period):
    start, end, label, period = _get_period_range(period)

    collections = (
        Collection.query
        .filter(Collection.scheduled_date >= start, Collection.scheduled_date <= end)
        .order_by(Collection.scheduled_date.desc())
        .all()
    )

    completed = [c for c in collections if c.status == 'completed']
    total_waste = sum(float(c.waste_collected_kg) for c in completed if c.waste_collected_kg)
    completion_rate = (len(completed) / len(collections) * 100) if collections else 0

    bins = Bin.query.order_by(Bin.fill_level.desc()).all()
    avg_fill = (sum(float(b.fill_level) for b in bins) / len(bins)) if bins else 0

    summary_stats = {
        'Total Collections Scheduled': len(collections),
        'Collections Completed': len(completed),
        'Completion Rate (%)': round(completion_rate, 1),
        'Total Waste Collected (kg)': round(total_waste, 1),
        'Average Bin Fill Level (%)': round(avg_fill, 1),
        'Bins Currently Full': sum(1 for b in bins if b.status == 'full'),
        'Total Active Bins': len(bins),
    }

    bin_rows = [['Bin Code', 'Location', 'Capacity (L)', 'Fill Level (%)', 'Status']]
    for b in bins:
        bin_rows.append([b.bin_code, b.location, str(b.capacity_l), f'{b.fill_level}%', b.status.title()])

    collection_rows = [['Date', 'Bin', 'Collector', 'Status', 'Waste (kg)']]
    for c in collections:
        collection_rows.append([
            c.scheduled_date.isoformat(),
            c.bin.bin_code,
            c.collector.full_name if c.collector else '-',
            c.status.replace('_', ' ').title(),
            f'{c.waste_collected_kg}' if c.waste_collected_kg else '-'
        ])

    return {
        'period': period,
        'label': label,
        'start': start,
        'end': end,
        'summary_stats': summary_stats,
        'bin_rows': bin_rows,
        'collection_rows': collection_rows,
        'bins': bins,
        'collections': collections,
    }


@reports_bp.route('/')
@login_required
def index():
    """Display analytics dashboard with daily/weekly/monthly views."""
    period = request.args.get('period', 'daily')
    data = _build_report_data(period)

    # Bin utilization for chart (top 10 by fill level)
    top_bins = data['bins'][:10]

    # AI trend insight
    predictions = predict_all_bins()

    return render_template(
        'reports.html',
        period=data['period'],
        label=data['label'],
        summary_stats=data['summary_stats'],
        bin_rows=data['bin_rows'],
        collection_rows=data['collection_rows'],
        top_bins=top_bins,
        predictions=predictions,
    )


@reports_bp.route('/download')
@login_required
def download():
    """Generate and download the report as a PDF."""
    period = request.args.get('period', 'daily')
    data = _build_report_data(period)

    buffer = generate_report_pdf(
        report_title='Waste Collection Report',
        period_label=data['label'],
        summary_stats=data['summary_stats'],
        bin_rows=data['bin_rows'],
        collection_rows=data['collection_rows'],
    )

    filename = f'waste_report_{data["period"]}_{date.today().isoformat()}.pdf'
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')
