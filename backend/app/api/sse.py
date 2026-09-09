import json
import queue
import time
from flask import Blueprint, Response, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db, limiter
from app.models.event_log import EventLog, EventType, EventSeverity

sse_bp = Blueprint('sse', __name__, url_prefix='/api/v1/events')

# In-memory subscriber queues keyed by user_id
_subscribers = {}
MAX_QUEUE_SIZE = 100


def _coerce_severity(severity):
    """Coerce severity string/enum to a valid EventSeverity member."""
    if severity is None:
        return EventSeverity.INFO
    if isinstance(severity, EventSeverity):
        return severity
    try:
        return EventSeverity[str(severity).upper()]
    except (KeyError, ValueError):
        return EventSeverity.INFO


def publish_event(event_type, title, description=None, entity_type=None, entity_id=None,
                  severity=None, user_id=None, data=None, ip_address=None):
    """Publish an event to all SSE subscribers and persist to DB."""
    event = EventLog.log(
        event_type=event_type,
        title=title,
        description=description,
        entity_type=entity_type,
        entity_id=entity_id,
        severity=_coerce_severity(severity),
        user_id=user_id,
        ip_address=ip_address,
        data=data,
    )
    db.session.commit()

    payload = json.dumps(event.to_dict(), default=str)

    dead_queues = []
    for uid, q in _subscribers.items():
        try:
            q.put_nowait(payload)
        except queue.Full:
            dead_queues.append(uid)
    for uid in dead_queues:
        _subscribers.pop(uid, None)

    return event


@sse_bp.route('/stream', methods=['GET'])
@jwt_required(optional=True)
@limiter.limit("30 per minute")
def stream():
    """SSE stream endpoint. Returns text/event-stream."""
    def generate():
        q = queue.Queue(maxsize=MAX_QUEUE_SIZE)
        _subscribers[id(q)] = q

        try:
            # Send initial connection event
            yield f"event: connected\ndata: {json.dumps({'status': 'connected'})}\n\n"

            while True:
                try:
                    payload = q.get(timeout=30)
                    yield f"data: {payload}\n\n"
                except queue.Empty:
                    # Send keepalive every 30s
                    yield f": keepalive {time.time()}\n\n"
        except GeneratorExit:
            pass
        finally:
            _subscribers.pop(id(q), None)

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',
            'Access-Control-Allow-Origin': '*',
        }
    )


@sse_bp.route('/recent', methods=['GET'])
@jwt_required()
def get_recent_events():
    """Get recent events for polling fallback."""
    from app.utils.helpers import success_response
    limit = min(request.args.get('limit', 50, type=int), 200)
    offset = request.args.get('offset', 0, type=int)

    query = EventLog.query.order_by(EventLog.created_at.desc())
    total = EventLog.query.count()
    events = query.offset(offset).limit(limit).all()

    return success_response({
        'items': [e.to_dict() for e in events],
        'total': total,
    })
