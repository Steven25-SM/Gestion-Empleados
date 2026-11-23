
import os
import uuid
from decimal import Decimal

import boto3
from flask import Flask, render_template_string, request, redirect, url_for, flash, send_file
from werkzeug.utils import secure_filename
from botocore.exceptions import ClientError
from io import BytesIO

app = Flask(__name__)
app.secret_key = "glab-s13-local-secret"

ENDPOINT = os.getenv("AWS_ENDPOINT_URL", "http://localhost:4566")
REGION = "us-east-1"
TABLE_NAME = "Empleados"
BUCKET_NAME = "fotos-empleados-glab-s13"

dynamodb = boto3.resource(
    "dynamodb",
    endpoint_url=ENDPOINT,
    region_name=REGION,
    aws_access_key_id="test",
    aws_secret_access_key="test"
)

s3 = boto3.client(
    "s3",
    endpoint_url=ENDPOINT,
    region_name=REGION,
    aws_access_key_id="test",
    aws_secret_access_key="test"
)

table = dynamodb.Table(TABLE_NAME)

HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Gestión de empleados | GLAB-S13</title>

<style>
*{box-sizing:border-box}
body{
 margin:0;background:#edf4f1;color:#203b37;
 font-family:"Segoe UI",Arial,sans-serif;
}
header{
 background:linear-gradient(120deg,#102d35,#174d4b,#167b69);
 color:#e7fff7;padding:30px 7%;
 border-bottom:3px solid #51d6b0;
}
header h1{margin:0;font-size:28px;letter-spacing:.5px}
header p{margin:9px 0 0;color:#a9d9ca}
main{max-width:1180px;margin:35px auto;padding:0 22px}
.card{
 background:#fff;padding:28px;border-radius:13px;
 margin-bottom:25px;border:1px solid #dcebe5;
 box-shadow:0 5px 20px #173d3210;
}
h2{margin-top:0;color:#175b4d;font-size:21px}
form.grid{
 display:grid;grid-template-columns:1fr 1fr;gap:16px
}
input{
 padding:13px;border:1px solid #d3e3dc;
 border-radius:7px;width:100%;font-size:14px;
 background:#fbfdfc;color:#203b37;
 outline:none;transition:.2s;
}
input:focus{
 border-color:#36b995;box-shadow:0 0 0 3px #36b99520
}
input[type=file]{background:#f3f8f5}
button,.btn{
 border:0;border-radius:7px;padding:11px 17px;
 background:#168f75;color:white;cursor:pointer;
 text-decoration:none;display:inline-block;
 font-size:14px;font-weight:600;transition:.2s;
}
button:hover,.btn:hover{
 background:#106d5a;transform:translateY(-1px)
}
.btn-delete{background:#b84d55}
.btn-delete:hover{background:#923942}
.btn-edit{background:#ad8950}
.btn-edit:hover{background:#8a6938}
.actions{display:flex;gap:7px;flex-wrap:wrap}
table{width:100%;border-collapse:collapse}
th,td{
 text-align:left;padding:14px;
 border-bottom:1px solid #e5eee9;font-size:14px
}
th{
 background:#edf6f2;color:#276454;
 font-size:12px;text-transform:uppercase;
 letter-spacing:.5px
}
tbody tr:hover{background:#f5faf7}
.photo{
 width:65px;height:65px;object-fit:cover;
 border-radius:9px;border:2px solid #d8eee5
}
.alert{
 padding:13px;border-radius:8px;
 background:#e1f7ed;color:#146b50;
 border:1px solid #b8e9d3;margin-bottom:15px
}
small{color:#71877e}
footer{
 padding:15px 0;text-align:center;
 border-top:1px solid #dcebe5
}
@media(max-width:650px){
 form.grid{grid-template-columns:1fr}
 .table-wrap{overflow-x:auto}
 header h1{font-size:22px}
 .card{padding:18px}
}
</style>

</head>
<body>
<header>
<h1>Gestión de empleados</h1>
<p>Laboratorio GLAB-S13 | Amazon DynamoDB + Amazon S3</p>
</header>
<main>
{% with messages = get_flashed_messages() %}
{% for message in messages %}
<div class="alert">{{message}}</div>
{% endfor %}
{% endwith %}

<section class="card">
<h2>{% if empleado %}Editar empleado{% else %}Registrar empleado{% endif %}</h2>
<form class="grid" method="POST" action="{% if empleado %}{{url_for('actualizar', id=empleado.empleadoId)}}{% else %}{{url_for('crear')}}{% endif %}" enctype="multipart/form-data">
<input name="nombre" placeholder="Nombre completo" required value="{{empleado.nombre if empleado else ''}}">
<input name="correo" type="email" placeholder="Correo electrónico" required value="{{empleado.correo if empleado else ''}}">
<input name="cargo" placeholder="Cargo" required value="{{empleado.cargo if empleado else ''}}">
<input name="departamento" placeholder="Departamento" required value="{{empleado.departamento if empleado else ''}}">
<label style="grid-column:1/-1">
<small>Fotografía del empleado (JPG, PNG o WEBP)</small>
<input type="file" name="foto" accept="image/jpeg,image/png,image/webp">
</label>
{% if empleado %}
<div><button type="submit">Guardar cambios</button> <a class="btn" href="{{url_for('index')}}">Cancelar</a></div>
{% else %}
<div><button type="submit">Registrar empleado</button></div>
{% endif %}
</form>
</section>

<section class="card">
<h2>Directorio de empleados</h2>
<p><small>Registros almacenados en DynamoDB. Fotografías almacenadas en S3.</small></p>
<div class="table-wrap">
<table>
<thead><tr><th>Fotografía</th><th>Nombre</th><th>Correo</th><th>Cargo</th><th>Departamento</th><th>Acciones</th></tr></thead>
<tbody>
{% for e in empleados %}
<tr>
<td>{% if e.fotoKey %}<img class="photo" src="{{url_for('foto', key=e.fotoKey)}}" alt="Fotografía">{% else %}Sin foto{% endif %}</td>
<td>{{e.nombre}}</td><td>{{e.correo}}</td><td>{{e.cargo}}</td><td>{{e.departamento}}</td>
<td><div class="actions">
<a class="btn btn-edit" href="{{url_for('editar', id=e.empleadoId)}}">Editar</a>
<form method="POST" action="{{url_for('eliminar', id=e.empleadoId)}}" onsubmit="return confirm('¿Eliminar este empleado?')">
<button class="btn-delete" type="submit">Eliminar</button>
</form>
</div></td>
</tr>
{% else %}
<tr><td colspan="6">No hay empleados registrados.</td></tr>
{% endfor %}
</tbody>
</table>
</div>
</section>
<footer><small>Aplicación académica | Tecsup | GLAB-S13</small></footer>
</main>
</body>
</html>
"""


def obtener_empleados():
    response = table.scan()
    empleados = response.get("Items", [])
    while "LastEvaluatedKey" in response:
        response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        empleados.extend(response.get("Items", []))
    return sorted(empleados, key=lambda x: x.get("nombre", "").lower())


def guardar_foto(archivo):
    if not archivo or not archivo.filename:
        return None

    extension = os.path.splitext(secure_filename(archivo.filename))[1].lower()
    permitidas = {".jpg", ".jpeg", ".png", ".webp"}

    if extension not in permitidas:
        raise ValueError("Formato no permitido. Usa JPG, PNG o WEBP.")

    contenido = archivo.read()
    if not contenido:
        raise ValueError("El archivo de imagen está vacío.")
    if len(contenido) > 5 * 1024 * 1024:
        raise ValueError("La fotografía no puede superar los 5 MB.")

    key = f"empleados/{uuid.uuid4().hex}{extension}"
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=key,
        Body=contenido,
        ContentType=archivo.mimetype or "application/octet-stream"
    )
    return key


@app.route("/")
def index():
    return render_template_string(
        HTML,
        empleados=obtener_empleados(),
        empleado=None
    )


@app.route("/crear", methods=["POST"])
def crear():
    try:
        foto_key = guardar_foto(request.files.get("foto"))

        empleado = {
            "empleadoId": str(uuid.uuid4()),
            "nombre": request.form["nombre"].strip(),
            "correo": request.form["correo"].strip(),
            "cargo": request.form["cargo"].strip(),
            "departamento": request.form["departamento"].strip(),
            "fotoKey": foto_key or ""
        }

        table.put_item(Item=empleado)
        flash("Empleado registrado correctamente.")
    except (ValueError, ClientError) as error:
        flash(f"No se pudo registrar: {error}")

    return redirect(url_for("index"))


@app.route("/editar/<id>")
def editar(id):
    response = table.get_item(Key={"empleadoId": id})
    empleado = response.get("Item")
    if not empleado:
        flash("Empleado no encontrado.")
        return redirect(url_for("index"))

    return render_template_string(
        HTML,
        empleados=obtener_empleados(),
        empleado=empleado
    )


@app.route("/actualizar/<id>", methods=["POST"])
def actualizar(id):
    try:
        response = table.get_item(Key={"empleadoId": id})
        empleado = response.get("Item")
        if not empleado:
            flash("Empleado no encontrado.")
            return redirect(url_for("index"))

        nuevos_datos = {
            "nombre": request.form["nombre"].strip(),
            "correo": request.form["correo"].strip(),
            "cargo": request.form["cargo"].strip(),
            "departamento": request.form["departamento"].strip()
        }

        foto_key = guardar_foto(request.files.get("foto"))
        if foto_key:
            nueva_key = foto_key
            table.update_item(
                Key={"empleadoId": id},
                UpdateExpression="SET nombre=:n, correo=:c, cargo=:ca, departamento=:d, fotoKey=:f",
                ExpressionAttributeValues={
                    ":n": nuevos_datos["nombre"],
                    ":c": nuevos_datos["correo"],
                    ":ca": nuevos_datos["cargo"],
                    ":d": nuevos_datos["departamento"],
                    ":f": nueva_key
                }
            )
            if empleado.get("fotoKey"):
                s3.delete_object(Bucket=BUCKET_NAME, Key=empleado["fotoKey"])
        else:
            table.update_item(
                Key={"empleadoId": id},
                UpdateExpression="SET nombre=:n, correo=:c, cargo=:ca, departamento=:d",
                ExpressionAttributeValues={
                    ":n": nuevos_datos["nombre"],
                    ":c": nuevos_datos["correo"],
                    ":ca": nuevos_datos["cargo"],
                    ":d": nuevos_datos["departamento"]
                }
            )

        flash("Empleado actualizado correctamente.")
    except (ValueError, ClientError) as error:
        flash(f"No se pudo actualizar: {error}")

    return redirect(url_for("index"))


@app.route("/eliminar/<id>", methods=["POST"])
def eliminar(id):
    try:
        response = table.get_item(Key={"empleadoId": id})
        empleado = response.get("Item")

        if empleado:
            table.delete_item(Key={"empleadoId": id})
            if empleado.get("fotoKey"):
                s3.delete_object(Bucket=BUCKET_NAME, Key=empleado["fotoKey"])
            flash("Empleado eliminado correctamente.")
        else:
            flash("Empleado no encontrado.")
    except ClientError as error:
        flash(f"No se pudo eliminar: {error}")

    return redirect(url_for("index"))


@app.route("/foto/<path:key>")
def foto(key):
    try:
        response = s3.get_object(Bucket=BUCKET_NAME, Key=key)
        contenido = response["Body"].read()
        return send_file(
            BytesIO(contenido),
            mimetype=response.get("ContentType", "image/jpeg")
        )
    except ClientError:
        return "Fotografía no encontrada en S3.", 404


@app.route("/salud")
def salud():
    return {
        "aplicacion": "GLAB-S13",
        "dynamodb": TABLE_NAME,
        "s3": BUCKET_NAME,
        "estado": "funcionando"
    }


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
