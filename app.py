from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response
from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime
from functools import wraps
import csv, io, os

app = Flask(__name__)
app.secret_key = 'lifebasket-secret-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['ANTHROPIC_API_KEY'] = os.environ.get('ANTHROPIC_API_KEY', '')

db = SQLAlchemy(app)

# ── MODELS ──────────────────────────────────────────
class Product(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(200), nullable=False)
    qty        = db.Column(db.Integer, default=0)
    price      = db.Column(db.Float, default=0.0)
    date_added = db.Column(db.Date, default=date.today)

    @property
    def total_value(self):
        return self.qty * self.price

class Return(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    product_id   = db.Column(db.Integer, db.ForeignKey('product.id'))
    product_name = db.Column(db.String(200))
    qty          = db.Column(db.Integer, default=1)
    return_date  = db.Column(db.Date, default=date.today)
    reason       = db.Column(db.String(300))
    status       = db.Column(db.String(20), default='pending')

class DeductLog(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    product_name = db.Column(db.String(200))
    qty        = db.Column(db.Integer)
    log_date   = db.Column(db.Date, default=date.today)
    note       = db.Column(db.String(300))
    source     = db.Column(db.String(50), default='manual')

with app.app_context():
    db.create_all()

# ── AUTH ─────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('username', '')
        p = request.form.get('password', '')
        if u == 'admin' and p == 'admin123':
            session['logged_in'] = True
            return redirect(url_for('index'))
        flash('Wrong username or password', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ── MAIN PAGE ────────────────────────────────────────
@app.route('/')
@login_required
def index():
    products = Product.query.order_by(Product.date_added.desc()).all()
    returns  = Return.query.order_by(Return.return_date.desc()).all()
    logs     = DeductLog.query.order_by(DeductLog.log_date.desc()).limit(20).all()
    return render_template('index.html', products=products, returns=returns, logs=logs,
                           api_key=app.config['ANTHROPIC_API_KEY'])

# ── ADD PRODUCT ──────────────────────────────────────
@app.route('/add', methods=['POST'])
@login_required
def add():
    name     = request.form.get('name', '').strip()
    qty      = int(request.form.get('qty') or 0)
    price    = float(request.form.get('price') or 0)
    date_str = request.form.get('date_added', '')
    if not name:
        flash('Product name required!', 'error')
        return redirect(url_for('index'))
    d = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else date.today()
    db.session.add(Product(name=name, qty=qty, price=price, date_added=d))
    db.session.commit()
    flash(f'✅ "{name}" added!', 'success')
    return redirect(url_for('index'))

# ── DELETE ───────────────────────────────────────────
@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    p = Product.query.get_or_404(id)
    Return.query.filter_by(product_id=id).delete()
    DeductLog.query.filter_by(product_id=id).delete()
    db.session.delete(p)
    db.session.commit()
    flash(f'🗑 "{p.name}" deleted', 'info')
    return redirect(url_for('index'))

# ── CSV UPLOAD ───────────────────────────────────────
@app.route('/upload', methods=['POST'])
@login_required
def upload():
    f = request.files.get('file')
    if not f:
        flash('No file selected!', 'error')
        return redirect(url_for('index'))
    stream = io.StringIO(f.stream.read().decode('utf-8'))
    added = 0
    for row in csv.reader(stream):
        if not row or not row[0].strip(): continue
        try:
            name  = row[0].strip()
            qty   = int(row[1].strip()) if len(row) > 1 else 0
            price = float(row[2].strip()) if len(row) > 2 else 0.0
            d_str = row[3].strip() if len(row) > 3 else ''
            d = datetime.strptime(d_str, '%Y-%m-%d').date() if d_str else date.today()
            db.session.add(Product(name=name, qty=qty, price=price, date_added=d))
            added += 1
        except: continue
    db.session.commit()
    flash(f'✅ {added} products imported!', 'success')
    return redirect(url_for('index'))

# ── EXPORT CSV ───────────────────────────────────────
@app.route('/export')
@login_required
def export():
    products = Product.query.all()
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(['Name','Qty','Price','Total Value','Date Added'])
    for p in products:
        w.writerow([p.name, p.qty, p.price, round(p.total_value,2),
                    p.date_added.strftime('%Y-%m-%d') if p.date_added else ''])
    resp = make_response(out.getvalue())
    resp.headers['Content-Type'] = 'text/csv'
    resp.headers['Content-Disposition'] = 'attachment; filename=inventory.csv'
    return resp

# ── RETURNS ──────────────────────────────────────────
@app.route('/return/add', methods=['POST'])
@login_required
def return_add():
    pid      = int(request.form.get('product_id') or 0)
    qty      = int(request.form.get('qty') or 0)
    reason   = request.form.get('reason', '').strip()
    date_str = request.form.get('return_date', '')
    p = Product.query.get(pid)
    if not p:
        flash('Product not found!', 'error')
        return redirect(url_for('index'))
    d = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else date.today()
    db.session.add(Return(product_id=pid, product_name=p.name, qty=qty, return_date=d,
                          reason=reason, status='pending'))
    db.session.commit()
    flash(f'↩ Return registered for "{p.name}" — pending approval', 'info')
    return redirect(url_for('index'))

@app.route('/return/approve/<int:id>', methods=['POST'])
@login_required
def return_approve(id):
    r = Return.query.get_or_404(id)
    if r.status == 'pending':
        r.status = 'approved'
        p = Product.query.get(r.product_id)
        if p: p.qty += r.qty
        db.session.commit()
        flash(f'✅ Return approved — {r.qty} units added back to "{r.product_name}"', 'success')
    return redirect(url_for('index'))

@app.route('/return/reject/<int:id>', methods=['POST'])
@login_required
def return_reject(id):
    r = Return.query.get_or_404(id)
    if r.status == 'pending':
        r.status = 'rejected'
        db.session.commit()
        flash(f'❌ Return rejected for "{r.product_name}"', 'error')
    return redirect(url_for('index'))

# ── MANUAL DEDUCT ────────────────────────────────────
@app.route('/deduct', methods=['POST'])
@login_required
def deduct():
    pid      = int(request.form.get('product_id') or 0)
    qty      = int(request.form.get('qty') or 0)
    note     = request.form.get('note', '').strip()
    date_str = request.form.get('date', '')
    p = Product.query.get(pid)
    if not p:
        flash('Product not found!', 'error')
        return redirect(url_for('index'))
    if qty > p.qty:
        flash(f'❌ Cannot deduct {qty} — only {p.qty} in stock!', 'error')
        return redirect(url_for('index'))
    d = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else date.today()
    p.qty -= qty
    db.session.add(DeductLog(product_id=pid, product_name=p.name, qty=qty,
                             log_date=d, note=note, source='manual'))
    db.session.commit()
    flash(f'⬇ Deducted {qty} from "{p.name}"', 'success')
    return redirect(url_for('index'))

# ── AI BULK DEDUCT ───────────────────────────────────
@app.route('/deduct/bulk', methods=['POST'])
@login_required
def deduct_bulk():
    names = request.form.getlist('names[]')
    qtys  = request.form.getlist('qtys[]')
    done  = 0
    for name, q in zip(names, qtys):
        qty = int(q or 1)
        p = Product.query.filter(Product.name.ilike(f'%{name}%')).first()
        if p and p.qty >= qty:
            p.qty -= qty
            db.session.add(DeductLog(product_id=p.id, product_name=p.name, qty=qty,
                                     log_date=date.today(), note='AI scan', source='ai_scan'))
            done += 1
    db.session.commit()
    flash(f'🤖 AI deducted {done} product(s) from stock', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
