import csv, io
from flask import Blueprint, jsonify, request, Response
from db import get_conn, release_conn
from auth_middleware import auth_required

dashboard_routes = Blueprint("dashboard", __name__)

COLS = "id,nome,endereco,telefone,municipio,data_nascimento,lideranca,bairro,zona_eleitoral,secao_eleitoral,partido,status,votos_declarados"

def _row_to_dict(row):
    return {
        "id":row[0],"nome":row[1],"endereco":row[2],"telefone":row[3],
        "municipio":row[4],"data_nascimento":str(row[5]) if row[5] else "",
        "lideranca":row[6],"bairro":row[7],"zona_eleitoral":row[8],
        "secao_eleitoral":row[9],"partido":row[10],
        "status":row[11] or "Indefinido","votos_declarados":row[12] or 0,
    }

def _municipio_filter(user):
    return user.get("municipio") or "" if user.get("role")=="coordenador" else None

@dashboard_routes.route("/", methods=["GET"])
@auth_required
def dashboard():
    mf = _municipio_filter(request.user)
    c = get_conn()
    try:
        with c.cursor() as cur:
            if mf:
                cur.execute("SELECT COUNT(*) FROM pessoas WHERE municipio=%s",(mf,))
                total=cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM pessoas WHERE lideranca!='Nenhuma' AND municipio=%s",(mf,))
            else:
                cur.execute("SELECT COUNT(*) FROM pessoas"); total=cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM pessoas WHERE lideranca!='Nenhuma'")
            liderancas=cur.fetchone()[0]
    finally: release_conn(c)
    return jsonify({"total":total,"liderancas":liderancas,"municipio":mf or ""})

@dashboard_routes.route("/pessoas", methods=["GET","POST"])
@auth_required
def pessoas():
    mf = _municipio_filter(request.user)
    if request.method=="GET":
        municipio = mf or request.args.get("municipio","").strip()
        lideranca = request.args.get("lideranca","").strip()
        status    = request.args.get("status","").strip()
        query = f"SELECT {COLS} FROM pessoas"
        filters, params = [], []
        if municipio: filters.append("municipio=%s"); params.append(municipio)
        if lideranca: filters.append("lideranca=%s"); params.append(lideranca)
        if status:    filters.append("status=%s");    params.append(status)
        if filters: query += " WHERE "+" AND ".join(filters)
        query += " ORDER BY id DESC"
        c=get_conn()
        try:
            with c.cursor() as cur: cur.execute(query,params); rows=cur.fetchall()
        finally: release_conn(c)
        return jsonify({"pessoas":[_row_to_dict(r) for r in rows],"municipio_fixo":mf or ""})

    data            = request.get_json(silent=True) or {}
    nome            = (data.get("nome") or "").strip()
    municipio       = mf or (data.get("municipio") or "").strip()
    endereco        = (data.get("endereco") or "").strip()
    telefone        = (data.get("telefone") or "").strip()
    bairro          = (data.get("bairro") or "").strip()
    zona_eleitoral  = (data.get("zona_eleitoral") or "").strip()
    secao_eleitoral = (data.get("secao_eleitoral") or "").strip()
    partido         = (data.get("partido") or "").strip()
    status          = (data.get("status") or "Indefinido").strip()
    lideranca       = (data.get("lideranca") or "Nenhuma").strip()
    votos_declarados= int(data.get("votos_declarados") or 0)
    data_nascimento = data.get("data_nascimento") or None
    if not nome or not municipio:
        return jsonify({"error":"Nome e município são obrigatórios."}),400
    c=get_conn()
    try:
        with c.cursor() as cur:
            cur.execute(f"""INSERT INTO pessoas
                (nome,endereco,telefone,municipio,data_nascimento,lideranca,
                 bairro,zona_eleitoral,secao_eleitoral,partido,status,votos_declarados)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING {COLS}""",
                (nome,endereco,telefone,municipio,data_nascimento,lideranca,
                 bairro,zona_eleitoral,secao_eleitoral,partido,status,votos_declarados))
            row=cur.fetchone()
        c.commit()
    except Exception as e:
        c.rollback(); return jsonify({"error":str(e)}),500
    finally: release_conn(c)
    return jsonify({"ok":True,"pessoa":_row_to_dict(row)}),201

@dashboard_routes.route("/pessoas/<int:pid>", methods=["DELETE"])
@auth_required
def deletar_pessoa(pid):
    mf=_municipio_filter(request.user)
    c=get_conn()
    try:
        with c.cursor() as cur:
            if mf: cur.execute("DELETE FROM pessoas WHERE id=%s AND municipio=%s RETURNING id",(pid,mf))
            else:  cur.execute("DELETE FROM pessoas WHERE id=%s RETURNING id",(pid,))
            row=cur.fetchone()
        if not row: return jsonify({"error":"Não encontrado ou sem permissão."}),404
        c.commit()
    except Exception as e:
        c.rollback(); return jsonify({"error":str(e)}),500
    finally: release_conn(c)
    return jsonify({"ok":True})

@dashboard_routes.route("/exportar-csv", methods=["GET"])
@auth_required
def exportar_csv():
    mf=_municipio_filter(request.user)
    municipio = mf or request.args.get("municipio","").strip()
    status    = request.args.get("status","").strip()
    query = f"SELECT {COLS} FROM pessoas"
    filters,params=[],[]
    if municipio: filters.append("municipio=%s"); params.append(municipio)
    if status:    filters.append("status=%s");    params.append(status)
    if filters: query+=" WHERE "+" AND ".join(filters)
    query+=" ORDER BY id DESC"
    c=get_conn()
    try:
        with c.cursor() as cur: cur.execute(query,params); rows=cur.fetchall()
    finally: release_conn(c)
    out=io.StringIO()
    w=csv.writer(out)
    w.writerow(["ID","Nome","Município","Bairro","Zona","Seção","Telefone","Partido","Status","Tipo","Votos Declarados","Endereço","Nasc."])
    for r in rows:
        d=_row_to_dict(r)
        w.writerow([d["id"],d["nome"],d["municipio"],d["bairro"],d["zona_eleitoral"],
                    d["secao_eleitoral"],d["telefone"],d["partido"],d["status"],
                    d["lideranca"],d["votos_declarados"],d["endereco"],d["data_nascimento"]])
    out.seek(0)
    return Response("\ufeff"+out.getvalue(),mimetype="text/csv;charset=utf-8",
        headers={"Content-Disposition":"attachment;filename=eleitores.csv"})
