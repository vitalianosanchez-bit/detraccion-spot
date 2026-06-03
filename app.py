from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, Empresa, Usuario, Proveedor, Cliente, TipoOperacion, BienServicio
from seed import seed_empresa
import os, io, csv

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'detraccion-secret-2025')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///detapp.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(uid):
    return Usuario.query.get(int(uid))

# ─── INIT DB ────────────────────────────────────────────────────────────────
with app.app_context():
    db.create_all()
    # Crear superadmin si no existe
    if not Usuario.query.filter_by(username='admin').first():
        emp = Empresa(nombre='Empresa Demo', ruc='00000000000', cuenta='000000')
        db.session.add(emp)
        db.session.flush()
        seed_empresa(emp.id)
        u = Usuario(empresa_id=emp.id, nombre='Administrador', username='admin', rol='superadmin')
        u.set_password('admin123')
        db.session.add(u)
        db.session.commit()

# ─── AUTH ────────────────────────────────────────────────────────────────────
@app.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    error = None
    if request.method == 'POST':
        u = Usuario.query.filter_by(username=request.form['username']).first()
        if u and u.activo and u.check_password(request.form['password']):
            login_user(u)
            return redirect(url_for('index'))
        error = 'Usuario o contraseña incorrectos'
    return render_template('login.html', error=error)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ─── MAIN APP ────────────────────────────────────────────────────────────────
@app.route('/')
@login_required
def index():
    empresas = []
    if current_user.rol == 'superadmin':
        empresas = Empresa.query.filter_by(activa=True).all()
    return render_template('app.html', user=current_user, empresas=empresas)

# ─── API EMPRESA (solo superadmin) ───────────────────────────────────────────
@app.route('/api/empresas', methods=['GET'])
@login_required
def get_empresas():
    if current_user.rol != 'superadmin':
        return jsonify([])
    return jsonify([{'id':e.id,'nombre':e.nombre,'ruc':e.ruc,'cuenta':e.cuenta} for e in Empresa.query.filter_by(activa=True).all()])

@app.route('/api/empresas', methods=['POST'])
@login_required
def crear_empresa():
    if current_user.rol != 'superadmin':
        return jsonify({'error':'Sin permiso'}), 403
    d = request.json
    e = Empresa(nombre=d['nombre'], ruc=d['ruc'], cuenta=d.get('cuenta',''))
    db.session.add(e)
    db.session.flush()
    seed_empresa(e.id)
    db.session.commit()
    return jsonify({'id':e.id,'nombre':e.nombre,'ruc':e.ruc})

@app.route('/api/empresas/<int:eid>', methods=['PUT'])
@login_required
def editar_empresa(eid):
    if current_user.rol != 'superadmin':
        return jsonify({'error':'Sin permiso'}), 403
    e = Empresa.query.get_or_404(eid)
    d = request.json
    e.nombre = d.get('nombre', e.nombre)
    e.ruc    = d.get('ruc', e.ruc)
    e.cuenta = d.get('cuenta', e.cuenta)
    db.session.commit()
    return jsonify({'ok':True})

@app.route('/api/empresas/<int:eid>', methods=['DELETE'])
@login_required
def eliminar_empresa(eid):
    if current_user.rol != 'superadmin':
        return jsonify({'error':'Sin permiso'}), 403
    e = Empresa.query.get_or_404(eid)
    e.activa = False
    db.session.commit()
    return jsonify({'ok':True})

# ─── API USUARIOS ─────────────────────────────────────────────────────────────
def eid():
    """Empresa activa del usuario actual."""
    sel = session.get('empresa_sel')
    if current_user.rol == 'superadmin' and sel:
        return int(sel)
    return current_user.empresa_id

@app.route('/api/sel_empresa/<int:empresa_id>', methods=['POST'])
@login_required
def sel_empresa(empresa_id):
    if current_user.rol != 'superadmin':
        return jsonify({'error':'Sin permiso'}), 403
    session['empresa_sel'] = empresa_id
    return jsonify({'ok':True})

@app.route('/api/usuarios', methods=['GET'])
@login_required
def get_usuarios():
    if current_user.rol not in ('superadmin','admin'):
        return jsonify([])
    q = Usuario.query.filter_by(empresa_id=eid(), activo=True)
    return jsonify([{'id':u.id,'nombre':u.nombre,'username':u.username,'rol':u.rol} for u in q.all()])

@app.route('/api/usuarios', methods=['POST'])
@login_required
def crear_usuario():
    if current_user.rol not in ('superadmin','admin'):
        return jsonify({'error':'Sin permiso'}), 403
    d = request.json
    if Usuario.query.filter_by(username=d['username']).first():
        return jsonify({'error':'Username ya existe'}), 400
    u = Usuario(empresa_id=eid(), nombre=d['nombre'], username=d['username'], rol=d.get('rol','usuario'))
    u.set_password(d['password'])
    db.session.add(u)
    db.session.commit()
    return jsonify({'id':u.id,'nombre':u.nombre,'username':u.username})

@app.route('/api/usuarios/<int:uid>', methods=['PUT'])
@login_required
def editar_usuario(uid):
    if current_user.rol not in ('superadmin','admin'):
        return jsonify({'error':'Sin permiso'}), 403
    u = Usuario.query.get_or_404(uid)
    d = request.json
    u.nombre = d.get('nombre', u.nombre)
    if d.get('password'):
        u.set_password(d['password'])
    u.rol = d.get('rol', u.rol)
    db.session.commit()
    return jsonify({'ok':True})

@app.route('/api/usuarios/<int:uid>', methods=['DELETE'])
@login_required
def eliminar_usuario(uid):
    if current_user.rol not in ('superadmin','admin'):
        return jsonify({'error':'Sin permiso'}), 403
    u = Usuario.query.get_or_404(uid)
    u.activo = False
    db.session.commit()
    return jsonify({'ok':True})

# ─── API PROVEEDORES ──────────────────────────────────────────────────────────
@app.route('/api/proveedores', methods=['GET'])
@login_required
def get_proveedores():
    q = Proveedor.query.filter_by(empresa_id=eid()).all()
    return jsonify([{'id':p.id,'ruc':p.ruc,'razon':p.razon,'cuenta':p.cuenta or '',
                     'dir':p.direccion or '','codBS':p.cod_bs or '','pct':p.pct or 0,
                     'afectoAuto':p.afecto_auto} for p in q])

@app.route('/api/proveedores', methods=['POST'])
@login_required
def crear_proveedor():
    d = request.json
    p = Proveedor(empresa_id=eid(), ruc=d['ruc'], razon=d['razon'].upper(),
                  cuenta=d.get('cuenta',''), direccion=d.get('dir',''),
                  cod_bs=d.get('codBS',''), pct=d.get('pct',0),
                  afecto_auto=d.get('afectoAuto',False))
    db.session.add(p)
    db.session.commit()
    return jsonify({'id':p.id})

@app.route('/api/proveedores/<int:pid>', methods=['PUT'])
@login_required
def editar_proveedor(pid):
    p = Proveedor.query.get_or_404(pid)
    d = request.json
    p.ruc=d.get('ruc',p.ruc); p.razon=d.get('razon',p.razon).upper()
    p.cuenta=d.get('cuenta',p.cuenta); p.direccion=d.get('dir',p.direccion)
    p.cod_bs=d.get('codBS',p.cod_bs); p.pct=d.get('pct',p.pct)
    p.afecto_auto=d.get('afectoAuto',p.afecto_auto)
    db.session.commit()
    return jsonify({'ok':True})

@app.route('/api/proveedores/<int:pid>', methods=['DELETE'])
@login_required
def eliminar_proveedor(pid):
    db.session.delete(Proveedor.query.get_or_404(pid))
    db.session.commit()
    return jsonify({'ok':True})

# ─── API CLIENTES ─────────────────────────────────────────────────────────────
@app.route('/api/clientes', methods=['GET'])
@login_required
def get_clientes():
    q = Cliente.query.filter_by(empresa_id=eid()).all()
    return jsonify([{'id':c.id,'ruc':c.ruc,'razon':c.razon,'cuenta':c.cuenta or '','dir':c.direccion or ''} for c in q])

@app.route('/api/clientes', methods=['POST'])
@login_required
def crear_cliente():
    d = request.json
    c = Cliente(empresa_id=eid(), ruc=d['ruc'], razon=d['razon'].upper(),
                cuenta=d.get('cuenta',''), direccion=d.get('dir',''))
    db.session.add(c); db.session.commit()
    return jsonify({'id':c.id})

@app.route('/api/clientes/<int:cid>', methods=['PUT'])
@login_required
def editar_cliente(cid):
    c = Cliente.query.get_or_404(cid)
    d = request.json
    c.ruc=d.get('ruc',c.ruc); c.razon=d.get('razon',c.razon).upper()
    c.cuenta=d.get('cuenta',c.cuenta); c.direccion=d.get('dir',c.direccion)
    db.session.commit()
    return jsonify({'ok':True})

@app.route('/api/clientes/<int:cid>', methods=['DELETE'])
@login_required
def eliminar_cliente(cid):
    db.session.delete(Cliente.query.get_or_404(cid))
    db.session.commit()
    return jsonify({'ok':True})

# ─── API TIPO OPERACION ───────────────────────────────────────────────────────
@app.route('/api/tipo_ops', methods=['GET'])
@login_required
def get_tipo_ops():
    q = TipoOperacion.query.filter_by(empresa_id=eid()).all()
    return jsonify([{'id':t.id,'cod':t.cod,'desc':t.descripcion,'validado':t.validado} for t in q])

@app.route('/api/tipo_ops', methods=['POST'])
@login_required
def crear_tipo_op():
    d = request.json
    t = TipoOperacion(empresa_id=eid(), cod=d['cod'].zfill(2), descripcion=d['desc'], validado=False)
    db.session.add(t); db.session.commit()
    return jsonify({'id':t.id})

@app.route('/api/tipo_ops/<int:tid>', methods=['PUT'])
@login_required
def editar_tipo_op(tid):
    t = TipoOperacion.query.get_or_404(tid)
    d = request.json
    t.cod=d.get('cod',t.cod).zfill(2); t.descripcion=d.get('desc',t.descripcion)
    t.validado=d.get('validado',t.validado)
    db.session.commit()
    return jsonify({'ok':True})

@app.route('/api/tipo_ops/<int:tid>', methods=['DELETE'])
@login_required
def eliminar_tipo_op(tid):
    db.session.delete(TipoOperacion.query.get_or_404(tid))
    db.session.commit()
    return jsonify({'ok':True})

# ─── API BIENES/SERVICIOS ─────────────────────────────────────────────────────
@app.route('/api/bs', methods=['GET'])
@login_required
def get_bs():
    q = BienServicio.query.filter_by(empresa_id=eid()).all()
    return jsonify([{'id':b.id,'cod':b.cod,'desc':b.descripcion,'pct':b.pct,'anexo':b.anexo,'validado':b.validado} for b in q])

@app.route('/api/bs', methods=['POST'])
@login_required
def crear_bs():
    d = request.json
    b = BienServicio(empresa_id=eid(), cod=d['cod'].zfill(3), descripcion=d['desc'],
                     pct=float(d['pct']), anexo=int(d['anexo']), validado=False)
    db.session.add(b); db.session.commit()
    return jsonify({'id':b.id})

@app.route('/api/bs/<int:bid>', methods=['PUT'])
@login_required
def editar_bs(bid):
    b = BienServicio.query.get_or_404(bid)
    d = request.json
    b.cod=d.get('cod',b.cod).zfill(3); b.descripcion=d.get('desc',b.descripcion)
    b.pct=float(d.get('pct',b.pct)); b.validado=d.get('validado',b.validado)
    db.session.commit()
    return jsonify({'ok':True})

@app.route('/api/bs/<int:bid>', methods=['DELETE'])
@login_required
def eliminar_bs(bid):
    db.session.delete(BienServicio.query.get_or_404(bid))
    db.session.commit()
    return jsonify({'ok':True})

# ─── RUN ─────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True, port=5000)
