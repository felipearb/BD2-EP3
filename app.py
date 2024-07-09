from flask import Flask, render_template, request
import psycopg2
from configparser import ConfigParser

app = Flask(__name__)

def get_db_connection():
    config = ConfigParser()
    config.read('config.ini')

    dbname = config.get('database', 'dbname')
    user = config.get('database', 'user')
    password = config.get('database', 'password')
    host = config.get('database', 'host')

    conn = psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host
    )
    return conn

def init_tables():
    create_tables_sql = """
    CREATE SCHEMA IF NOT EXISTS mydb;

    CREATE TABLE IF NOT EXISTS medico (
        crm VARCHAR(10) NOT NULL,
        nomeM VARCHAR(45) NOT NULL,
        telefoneM VARCHAR(11) NOT NULL,
        percentual DECIMAL(4,2) NOT NULL,
        PRIMARY KEY (crm)
    );

    CREATE TABLE IF NOT EXISTS agenda (
        idAgenda SERIAL PRIMARY KEY,
        diaSemana VARCHAR(7) NOT NULL,
        horaInicio TIME NOT NULL,
        horaFim TIME NOT NULL,
        crm VARCHAR(10) NOT NULL,
        CONSTRAINT fk_medico_agenda_crm
            FOREIGN KEY (crm)
            REFERENCES medico (crm)
            ON DELETE CASCADE
            ON UPDATE CASCADE
    );

    CREATE TABLE IF NOT EXISTS especialidade (
        idEsp SERIAL PRIMARY KEY,
        nomeE VARCHAR(45) NOT NULL,
        indice INT NOT NULL,
        UNIQUE (nomeE)
    );

    CREATE TABLE IF NOT EXISTS exerceEsp (
        crm VARCHAR(10) NOT NULL,
        idEsp INT NOT NULL,
        CONSTRAINT fk_medico_exerceEsp_crm
            FOREIGN KEY (crm)
            REFERENCES medico (crm)
            ON DELETE NO ACTION
            ON UPDATE NO ACTION,
        CONSTRAINT fk_especialidade_exerceEsp_idEsp
            FOREIGN KEY (idEsp)
            REFERENCES especialidade (idEsp)
            ON DELETE NO ACTION
            ON UPDATE NO ACTION
    );

    CREATE TABLE IF NOT EXISTS paciente (
        idPac SERIAL PRIMARY KEY,
        cpf VARCHAR(11) NOT NULL,
        nomeP VARCHAR(45) NOT NULL,
        telefonePac VARCHAR(11),
        endereco VARCHAR(120),
        idade INT NOT NULL,
        sexo CHAR(1) NOT NULL
    );

    CREATE TABLE IF NOT EXISTS consulta (
        idCon SERIAL PRIMARY KEY,
        crm VARCHAR(10) NOT NULL,
        idEsp INT NOT NULL,
        idPac INT NOT NULL,
        data DATE NOT NULL,
        horaInicCon TIME,
        horaFimCon TIME,
        pagou CHAR(1) NOT NULL,
        valorPago DECIMAL(10,2),
        formaPagamento VARCHAR(15),
        CONSTRAINT fk_medico_consulta_crm
            FOREIGN KEY (crm)
            REFERENCES medico (crm)
            ON DELETE CASCADE
            ON UPDATE CASCADE,
        CONSTRAINT fk_especialidade_consulta_idEsp
            FOREIGN KEY (idEsp)
            REFERENCES especialidade (idEsp)
            ON DELETE NO ACTION
            ON UPDATE NO ACTION,
        CONSTRAINT fk_paciente_consulta_idPac
            FOREIGN KEY (idPac)
            REFERENCES paciente (idPac)
            ON DELETE NO ACTION
            ON UPDATE NO ACTION
    );

    CREATE TABLE IF NOT EXISTS diagnostico (
        idDiagnostico SERIAL PRIMARY KEY,
        tratamentoRecomendado VARCHAR(50) NOT NULL,
        remediosReceitados VARCHAR(250),
        observacoes VARCHAR(250),
        idCon INT NOT NULL,
        CONSTRAINT fk_consulta_diagnostico_idCon
            FOREIGN KEY (idCon)
            REFERENCES consulta (idCon)
            ON DELETE NO ACTION
            ON UPDATE NO ACTION
    );

    CREATE TABLE IF NOT EXISTS doenca (
        idDoenca SERIAL PRIMARY KEY,
        nomeD VARCHAR(50) NOT NULL
    );

    CREATE TABLE IF NOT EXISTS diagnostica (
        idDiagnostico INT NOT NULL,
        idDoenca INT NOT NULL,
        CONSTRAINT fk_diagnostico_diagnostica_idDiagnostico
            FOREIGN KEY (idDiagnostico)
            REFERENCES diagnostico (idDiagnostico)
            ON DELETE NO ACTION
            ON UPDATE NO ACTION,
        CONSTRAINT fk_doenca_diagnostica_idDoenca
            FOREIGN KEY (idDoenca)
            REFERENCES doenca (idDoenca)
            ON DELETE NO ACTION
            ON UPDATE NO ACTION
    );



    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(create_tables_sql)
    conn.commit()
    cur.close()
    conn.close()

def init_values():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # SQL para inserir médicos apenas se não existirem
    insert_sql = """
    INSERT INTO medico (crm, nomeM, telefoneM, percentual)
    SELECT * FROM (VALUES
        ('CRM001', 'Dr. João Silva', '12345678901', 10.00),
        ('CRM002', 'Dra. Maria Oliveira', '12345678902', 12.50),
        ('CRM003', 'Dr. Pedro Santos', '12345678903', 15.00),
        ('CRM004', 'Dra. Ana Lima', '12345678904', 8.75),
        ('CRM005', 'Dr. Lucas Costa', '12345678905', 11.00),
        ('CRM006', 'Dra. Fernanda Souza', '12345678906', 14.25),
        ('CRM007', 'Dr. Marcos Ribeiro', '12345678907', 9.50),
        ('CRM008', 'Dra. Carla Almeida', '12345678908', 13.75),
        ('CRM009', 'Dr. Paulo Mendes', '12345678909', 10.50),
        ('CRM010', 'Dra. Laura Azevedo', '12345678910', 16.00)
    ) AS data(crm, nomeM, telefoneM, percentual)
    WHERE NOT EXISTS (
        SELECT 1 FROM medico WHERE medico.crm = data.crm
    );
    """
    
    cur.execute(insert_sql)
    conn.commit()
    
    cur.close()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/search', methods=['POST'])
def search():
    search_query = request.form['search_query']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM medico
        WHERE nomeM ILIKE %s
    """, ('%' + search_query + '%',))
    results = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', results=results)


@app.route('/searchall', methods=['POST'])
def searchall():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM medico")
    results = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', results=results)


@app.route('/list_consultas_paciente_medico', methods=['POST'])
def list_consultas_paciente_medico():
    crm = request.form['crm']
    idPac = request.form['idPac']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT crm, idPac, idEsp, data, horaInicCon
        FROM consulta
        WHERE crm = %s AND idPac = %s
    """, (crm, idPac))
    results = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', results=results)


@app.route('/list_medicos_uma_especialidade', methods=['POST'])
def list_medicos_uma_especialidade():
    especialidade = request.form['especialidade']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT m.crm, m.nomeM
        FROM medico m
        JOIN exerceEsp e ON m.crm = e.crm
        JOIN especialidade esp ON e.idEsp = esp.idEsp
        WHERE esp.nomeE = %s
    """, (especialidade,))
    results = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', results=results)


@app.route('/list_pacientes_medico_especialidade', methods=['POST'])
def list_pacientes_medico_especialidade():
    medico = request.form['medico']
    especialidade = request.form['especialidade']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.cpf, p.nomeP
        FROM consulta c
        JOIN paciente p ON c.idPac = p.idPac
        JOIN medico m ON c.crm = m.crm
        JOIN especialidade e ON c.idEsp = e.idEsp
        WHERE m.nomeM = %s AND e.nomeE = %s
    """, (medico, especialidade))
    results = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', results=results)


@app.route('/list_consultas_janeiro', methods=['POST'])
def list_consultas_janeiro():
    mes = request.form['mes']
    ano = request.form['ano']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT crm, idPac, idEsp, data, horaInicCon
        FROM consulta
        WHERE EXTRACT(MONTH FROM data) = %s AND EXTRACT(YEAR FROM data) = %s
    """, (mes, ano))
    results = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', results=results)


@app.route('/total_consultas_medico', methods=['POST'])
def total_consultas_medico():
    nomeM = request.form['nomeM']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT c.idEsp, COUNT(c.idCon) AS TotalConsultas
        FROM consulta c
        JOIN medico m ON c.crm = m.crm
        WHERE m.nomeM = %s
        GROUP BY c.idEsp
    """, (nomeM,))
    results = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', results=results)


@app.route('/medico_menos_consultas', methods=['GET'])
def medico_menos_consultas():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT m.crm AS CRM, m.nomeM AS NomeM, COUNT(c.idCon) AS TotalConsultas
        FROM medico m
        LEFT JOIN consulta c ON m.crm = c.crm
        GROUP BY m.crm, m.nomeM
        ORDER BY TotalConsultas
        LIMIT 1
    """)
    results = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', results=results)


@app.route('/remover_consultas_nao_pagas', methods=['POST'])
def remover_consultas_nao_pagas():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        DELETE FROM consulta
        WHERE pagou = 'N'
    """)
    conn.commit()
    cur.close()
    conn.close()
    
    # Recuperando consultas removidas
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) AS consultas_removidas
        FROM consulta
        WHERE pagou = 'N'
    """)
    results_remove = cur.fetchone()
    cur.close()
    conn.close()
    
    return render_template('index.html', results_remove=results_remove)


@app.route('/transferir_consulta', methods=['POST'])
def transferir_consulta():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE consulta
        SET crm = (SELECT crm FROM medico WHERE nomeM = 'Dr. Kildare'),
            data = '2024-05-24'
        WHERE idPac = (SELECT idPac FROM paciente WHERE nomeP = 'Diego Pituca')
            AND data = '2024-05-10'
            AND horaInicCon = '10:00:00'
            AND idEsp = (SELECT idEsp FROM especialidade WHERE nomeE = 'Dermatologia')
    """)
    conn.commit()
    cur.close()
    conn.close()
    
    # Verificando se a consulta foi transferida
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) AS consultas_transferidas
        FROM consulta
        WHERE crm = (SELECT crm FROM medico WHERE nomeM = 'Dr. Kildare')
            AND data = '2024-05-24'
            AND idPac = (SELECT idPac FROM paciente WHERE nomeP = 'Diego Pituca')
    """)
    results_transfer = cur.fetchone()
    cur.close()
    conn.close()
    
    return render_template('index.html', results_transfer=results_transfer)



if __name__ == '__main__':
    init_tables()
    init_values()
    app.run(debug=True)
