# GLAB-S13 - Gestión de empleados

Aplicación web desarrollada para el laboratorio GLAB-S13 de Tecsup.

## Tecnologías
- Python 3.12
- Flask
- Boto3
- Amazon DynamoDB
- Amazon S3
- Floci (emulador local de AWS)

## Funcionalidades
- Crear empleados.
- Consultar y listar empleados.
- Actualizar empleados.
- Eliminar empleados.
- Subir fotografías a S3.
- Visualizar fotografías almacenadas.

## Arquitectura
DynamoDB almacena los datos de empleados y S3 almacena sus fotografías. Flask proporciona la interfaz web y Boto3 permite comunicarse con los servicios AWS.

## Ejecución
1. Iniciar el emulador local AWS.
2. Configurar las credenciales ficticias y el endpoint local.
3. Instalar dependencias con pip install -r requirements.txt.
4. Ejecutar con python app.py.
